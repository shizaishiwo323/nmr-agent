"""Ideal-structure (rule geometry) NMR workflow with a parameter-confirmation step.

The flow mirrors the segmented-CT route: the agent collects what the prompt
states, the user confirms or edits every simulation choice in a dialog
(shape, pore sizes, coupling, water saturation, physics, inversion), and only
then is the pyGIMLi mesh, decay, inversion, Gaussian and interpretation chain run
in a run-specific folder.

Only the bundled geometry is supported: one large equilateral triangular pore
and one inverted small equilateral triangular pore, optionally joined by a
rectangular throat. This module imports no pyGIMLi code at import time.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from .models import AgentToolResult

if TYPE_CHECKING:  # pragma: no cover
    from .agent import AgentRuntimeContext

StageCallback = Callable[[AgentToolResult], None]

SUPPORTED_SHAPES = ("equilateral_triangle_pair",)

# Below this water saturation the triangle holds water only in its three corners
# (zero-contact-angle menisci); above it the gas sits as a central bubble.
CORNER_WATER_SATURATION = 1.0 - math.pi / (3.0 * math.sqrt(3.0))

GEOMETRY_FIELDS = ("large_side_um", "small_side_um", "large_depth_um", "small_depth_um")
COUPLING_FIELDS = ("coupled", "throat_length_um", "throat_width_um")
SATURATION_FIELDS = ("large_water_saturation", "small_water_saturation")
SIMULATION_CORE_FIELDS = ("diffusion_um2_per_ms", "bulk_t2_ms", "rho_solid_um_per_ms")
INVERSION_FIELDS = ("run_lcurve", "regularization", "lcurve_criterion", "num_bins")
GAUSSIAN_FIELDS = ("run_gaussian", "peak_count")
TIME_FIELDS = ("t_max_ms", "dt_ms")
MESH_FIELDS = ("ideal_mesh_area_um2",)
IDEAL_PARAM_FIELDS = (
    *GEOMETRY_FIELDS,
    *COUPLING_FIELDS,
    *SATURATION_FIELDS,
    *SIMULATION_CORE_FIELDS,
    *INVERSION_FIELDS,
    *GAUSSIAN_FIELDS,
    *TIME_FIELDS,
    *MESH_FIELDS,
)


def _english(language: str) -> bool:
    return language.lower().startswith("english")


def triangle_area_um2(side_um: float) -> float:
    return math.sqrt(3.0) / 4.0 * float(side_um) ** 2


@dataclass
class IdealRunConfig:
    shape: str = "equilateral_triangle_pair"
    large_side_um: float = 20.0
    small_side_um: float = 8.0
    large_depth_um: float = 20.0
    small_depth_um: float = 8.0
    coupled: bool = True
    throat_length_um: float = 5.0
    throat_width_um: float = 1.0
    large_water_saturation: float = 1.0
    small_water_saturation: float = 1.0
    diffusion_um2_per_ms: float = 2.0
    bulk_t2_ms: float = 3000.0
    rho_solid_um_per_ms: float = 0.005
    t_max_ms: float | None = None
    dt_ms: float | None = None
    ideal_mesh_area_um2: float = 0.05
    run_lcurve: bool = True
    lcurve_criterion: str = "ratio"
    regularization: float = 1.0
    num_bins: int = 200
    run_gaussian: bool = True
    peak_count: int = 2

    @classmethod
    def from_mapping(cls, values: dict[str, Any] | None) -> "IdealRunConfig":
        values = dict(values or {})
        known = {key: values[key] for key in cls.__dataclass_fields__ if key in values and values[key] is not None}
        config = cls(**known)
        for key in ("large_water_saturation", "small_water_saturation"):
            setattr(config, key, float(min(1.0, max(0.0, getattr(config, key)))))
        return config

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def air_area_um2(self, pore: str) -> float:
        side = self.large_side_um if pore == "large" else self.small_side_um
        saturation = self.large_water_saturation if pore == "large" else self.small_water_saturation
        return max(0.0, (1.0 - saturation) * triangle_area_um2(side))

    def time_axis(self) -> dict[str, float]:
        if self.t_max_ms is not None and self.dt_ms is not None:
            return {"t_max_ms": float(self.t_max_ms), "dt_ms": float(self.dt_ms)}
        return recommend_time_axis(max(estimate_pore_t2_ms(self, "large"), estimate_pore_t2_ms(self, "small")))

    def to_tool_args(self) -> dict[str, Any]:
        axis = self.time_axis()
        return {
            "geometry_mode": "rule",
            "coupled": bool(self.coupled),
            "large_side_um": float(self.large_side_um),
            "small_side_um": float(self.small_side_um),
            "large_depth_um": float(self.large_depth_um),
            "small_depth_um": float(self.small_depth_um),
            "throat_length_um": float(self.throat_length_um),
            "throat_width_um": float(self.throat_width_um),
            "large_air_area_um2": self.air_area_um2("large"),
            "small_air_area_um2": self.air_area_um2("small"),
            "ideal_mesh_area_um2": float(self.ideal_mesh_area_um2),
            "diffusion_um2_per_ms": float(self.diffusion_um2_per_ms),
            "bulk_t2_ms": float(self.bulk_t2_ms),
            "rho_solid_um_per_ms": float(self.rho_solid_um_per_ms),
            "t_max_ms": axis["t_max_ms"],
            "dt_ms": axis["dt_ms"],
        }


def water_configuration(saturation: float) -> str:
    """'full', 'bubble' (central gas) or 'corner' (water only in the corners)."""

    if saturation >= 1.0 - 1e-9:
        return "full"
    return "bubble" if saturation > CORNER_WATER_SATURATION + 0.001 else "corner"


def wetted_solid_perimeter_um(side_um: float, saturation: float) -> float:
    """Solid-water contact length; gas-water interfaces do not relax."""

    if water_configuration(saturation) != "corner":
        return 3.0 * float(side_um)
    water_area = max(saturation, 1e-9) * triangle_area_um2(side_um)
    meniscus_radius = math.sqrt((water_area / 3.0) / (math.sqrt(3.0) - math.pi / 3.0))
    return 6.0 * meniscus_radius * math.sqrt(3.0)


def estimate_pore_t2_ms(config: IdealRunConfig, pore: str) -> float:
    """Fast-diffusion estimate 1/T2 = 1/T2_bulk + rho * S/V for one pore."""

    side = config.large_side_um if pore == "large" else config.small_side_um
    saturation = config.large_water_saturation if pore == "large" else config.small_water_saturation
    water_area = max(saturation, 1e-9) * triangle_area_um2(side)
    surface_to_volume = wetted_solid_perimeter_um(side, saturation) / water_area
    return 1.0 / (1.0 / config.bulk_t2_ms + config.rho_solid_um_per_ms * surface_to_volume)


def _nice_number(value: float) -> float:
    if value <= 0:
        return 1.0
    exponent = math.floor(math.log10(value))
    fraction = value / 10**exponent
    nice = 1.0 if fraction <= 1.0 else 2.0 if fraction <= 2.0 else 5.0 if fraction <= 5.0 else 10.0
    return nice * 10**exponent


def recommend_time_axis(estimated_t2_ms: float, steps: int = 400) -> dict[str, float]:
    """Simulate about five estimated T2 so the decay reaches the baseline."""

    t_max = float(min(30000.0, max(200.0, _nice_number(5.0 * estimated_t2_ms))))
    return {"t_max_ms": t_max, "dt_ms": max(0.1, _nice_number(t_max / steps))}


def validate_config(config: IdealRunConfig, language: str = "中文") -> list[str]:
    """Problems that block a run; an empty list means the configuration is usable."""

    english = _english(language)
    problems: list[str] = []
    if config.shape not in SUPPORTED_SHAPES:
        problems.append("Only the equilateral-triangle pore pair is supported." if english else "目前只支持等边三角形双孔结构。")
    if config.small_side_um >= config.large_side_um:
        problems.append("The small pore side must be shorter than the large pore side." if english else "小孔边长必须小于大孔边长。")
    for pore in ("large", "small"):
        saturation = config.large_water_saturation if pore == "large" else config.small_water_saturation
        if saturation <= 0.02:
            problems.append(
                f"The {pore} pore holds almost no water (Sw ≤ 0.02); it cannot be meshed." if english else f"{'大' if pore == 'large' else '小'}孔几乎不含水（Sw ≤ 0.02），无法划分网格。"
            )
    if config.coupled:
        if config.throat_width_um >= config.small_side_um / 2.0:
            problems.append("The throat must be narrower than half the small pore side." if english else "喉道宽度必须小于小孔边长的一半。")
        corner_pores = [pore for pore in ("large", "small") if water_configuration(config.large_water_saturation if pore == "large" else config.small_water_saturation) == "corner"]
        if corner_pores:
            problems.append(
                (
                    f"With Sw ≤ {CORNER_WATER_SATURATION:.3f} the water sits only in the triangle corners and no longer touches the throat, so the pores cannot exchange water. Use the uncoupled case or raise Sw."
                )
                if english
                else f"Sw ≤ {CORNER_WATER_SATURATION:.3f} 时水只留在三角形角隅，不再接触喉道，两孔无法交换。请改为非耦合，或提高含水饱和度。"
            )
    return problems


# ---------------------------------------------------------------------------
# Prompt parsing
# ---------------------------------------------------------------------------

_UNCOUPLED_PATTERN = re.compile(r"(不耦合|非耦合|无耦合|不连通|没有喉道|无喉道|uncoupled|not coupled|without (a )?throat|isolated pores)", re.I)
_COUPLED_PATTERN = re.compile(r"(耦合|连通|喉道|coupled|throat|connected)", re.I)
_SATURATION_PATTERN = re.compile(r"(?:S_?w|含水饱和度|饱和度|water saturation)\s*[=:：为是]?\s*([01](?:\.\d+)?|\d{1,3}\s*%)", re.I)


def parse_prompt(user_text: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    text = user_text or ""
    if _UNCOUPLED_PATTERN.search(text):
        values["coupled"] = False
    elif _COUPLED_PATTERN.search(text):
        values["coupled"] = True
    match = _SATURATION_PATTERN.search(text)
    if match:
        raw = match.group(1).replace(" ", "")
        saturation = float(raw[:-1]) / 100.0 if raw.endswith("%") else float(raw)
        if 0.0 < saturation <= 1.0:
            values["large_water_saturation"] = saturation
            values["small_water_saturation"] = saturation
    if re.search(r"(全饱和|完全饱和|饱水|fully saturated|full saturation)", text, re.I):
        values.setdefault("large_water_saturation", 1.0)
        values.setdefault("small_water_saturation", 1.0)
    return values


def collect_prefill(user_text: str, args: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Merge prompt values and tool arguments; return them and the stated fields."""

    values = parse_prompt(user_text)
    for key in (*IDEAL_PARAM_FIELDS, "defaults_accepted"):
        if args.get(key) is not None:
            values[key] = args[key]
    # Older argument names: gas area inside each pore.
    for pore in ("large", "small"):
        air = args.get(f"{pore}_air_area_um2")
        if air is not None and f"{pore}_water_saturation" not in values:
            side = float(values.get(f"{pore}_side_um", getattr(IdealRunConfig, f"{pore}_side_um")))
            values[f"{pore}_water_saturation"] = max(0.0, 1.0 - float(air) / triangle_area_um2(side))
    if values.get("regularization") is not None and "run_lcurve" not in values:
        values["run_lcurve"] = False
    explicit = [key for key in values if key in IDEAL_PARAM_FIELDS or key == "defaults_accepted"]
    return values, explicit


def missing_confirmation_fields(prefill: dict[str, Any], explicit: list[str]) -> list[str]:
    """Groups the dialog must confirm because the prompt did not state them."""

    missing: list[str] = []
    if not any(field in explicit for field in GEOMETRY_FIELDS):
        missing.append("geometry")
    if "coupled" not in explicit:
        missing.append("coupling")
    if not any(field in explicit for field in SATURATION_FIELDS):
        missing.append("saturation")
    accepted = bool(prefill.get("defaults_accepted"))
    if not accepted and not any(field in explicit for field in SIMULATION_CORE_FIELDS):
        missing.append("simulation_core")
    if "run_lcurve" not in explicit:
        missing.append("run_lcurve")
    if "run_gaussian" not in explicit:
        missing.append("run_gaussian")
    return missing


# ---------------------------------------------------------------------------
# Agent tool and state
# ---------------------------------------------------------------------------


def _agent_summary(state: dict[str, Any]) -> dict[str, Any]:
    config = IdealRunConfig.from_mapping(state.get("prefill"))
    return {
        "stage": "ideal_parameter_confirmation",
        "step": state.get("step"),
        "missing_fields": state.get("missing_fields", []),
        "explicit_fields": state.get("explicit_fields", []),
        "prefill": config.to_dict(),
        "supported_shapes": list(SUPPORTED_SHAPES),
    }


def confirm_ideal_parameters(context: "AgentRuntimeContext", params: dict[str, Any]) -> None:
    state = dict(context.ideal_state or {})
    state["prefill"] = dict(state.get("prefill", {})) | dict(params)
    state["params_confirmed"] = True
    state["missing_fields"] = []
    state["step"] = "ready"
    state["open_dialog"] = None
    state["confirmed_at"] = datetime.now().isoformat(timespec="seconds")
    context.ideal_state = state


def request_ideal_run(
    context: "AgentRuntimeContext",
    args: dict[str, Any],
    language: str = "中文",
    on_stage: StageCallback | None = None,
) -> AgentToolResult:
    """Agent tool: run the ideal-structure workflow once its parameters are confirmed."""

    english = _english(language)
    state = dict(context.ideal_state or {})
    if not (state.get("params_confirmed") and state.get("step") == "ready"):
        prefill, explicit = collect_prefill(context.last_user_goal or "", args)
        state = {
            "step": "params",
            "prefill": prefill,
            "explicit_fields": sorted(set(explicit)),
            "missing_fields": missing_confirmation_fields(prefill, explicit),
            "params_confirmed": False,
            "open_dialog": None,
        }
        state["missing_fields_at_request"] = list(state["missing_fields"])
        config = IdealRunConfig.from_mapping(prefill)
        problems = validate_config(config, language)
        if state["missing_fields"] or problems:
            state["open_dialog"] = "ideal_params"
            context.ideal_state = state
            missing = ", ".join(state["missing_fields"])
            message = (
                "Waiting for the user to confirm the ideal-structure parameters (shape, pore sizes, coupling, water saturation, physics and inversion) in the dialog."
                + (f" Not stated in the prompt: {missing}." if missing else "")
                + (f" Problems to fix: {' '.join(problems)}" if problems else "")
                if english
                else "等待用户在参数确认窗口中确认理想结构参数（形状、孔隙尺寸、是否耦合、含水饱和度、物理参数与反演设置）。"
                + (f"提示词未给出：{missing}。" if missing else "")
                + (f"需要修正：{''.join(problems)}" if problems else "")
            )
            return AgentToolResult("needs_confirmation", message, summary=_agent_summary(state), error="needs_ideal_parameter_confirmation")
        state["params_confirmed"] = True
        state["step"] = "ready"
        context.ideal_state = state
    return run_ideal_pipeline(context, language=language, on_stage=on_stage)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def _emit(context: "AgentRuntimeContext", result: AgentToolResult, on_stage: StageCallback | None) -> AgentToolResult:
    context.results.append(result)
    context.tool_history.append(result)
    if on_stage is not None:
        on_stage(result)
    return result


def _run_dir(context: "AgentRuntimeContext", config: IdealRunConfig) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    tag = "coupled" if config.coupled else "uncoupled"
    sw = f"Sw{config.large_water_saturation:.2f}_{config.small_water_saturation:.2f}".replace(".", "p")
    path = context.workspace / "ideal_simulation" / f"{tag}__{sw}__run_{stamp}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_geometry_preview(config: IdealRunConfig, output_path: Path) -> Path:
    """Draw the confirmed geometry with its water configuration (no pyGIMLi)."""

    import matplotlib.pyplot as plt

    fig = draw_geometry_figure(config)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def _triangle_vertices(side: float, inverted: bool, y_shift: float) -> list[tuple[float, float]]:
    height = side * math.sqrt(3.0) / 2.0
    sign = -1.0 if inverted else 1.0
    return [(0.0, height * sign + y_shift), (-side / 2.0, y_shift), (side / 2.0, y_shift)]


def _water_patches(side: float, saturation: float, inverted: bool, y_shift: float):
    """Return (water polygons, gas polygons) for one pore, matching the mesher."""

    vertices = _triangle_vertices(side, inverted, y_shift)
    configuration = water_configuration(saturation)
    if configuration == "full":
        return [vertices], []
    sign = -1.0 if inverted else 1.0
    center = (0.0, side * math.sqrt(3.0) / 6.0 * sign + y_shift)
    total = triangle_area_um2(side)
    if configuration == "bubble":
        radius = math.sqrt((1.0 - saturation) * total / math.pi)
        circle = [(center[0] + radius * math.cos(2 * math.pi * i / 60), center[1] + radius * math.sin(2 * math.pi * i / 60)) for i in range(60)]
        return [vertices], [circle]
    water_area = saturation * total
    radius = math.sqrt((water_area / 3.0) / (math.sqrt(3.0) - math.pi / 3.0))
    contact = radius * math.sqrt(3.0)
    corners = []
    for index, vertex in enumerate(vertices):
        others = [vertices[j] for j in range(3) if j != index]
        dirs = []
        for other in others:
            dx, dy = other[0] - vertex[0], other[1] - vertex[1]
            norm = math.hypot(dx, dy)
            dirs.append((dx / norm, dy / norm))
        p1 = (vertex[0] + contact * dirs[0][0], vertex[1] + contact * dirs[0][1])
        p2 = (vertex[0] + contact * dirs[1][0], vertex[1] + contact * dirs[1][1])
        bx, by = center[0] - vertex[0], center[1] - vertex[1]
        bnorm = math.hypot(bx, by)
        arc_center = (vertex[0] + 2.0 * radius * bx / bnorm, vertex[1] + 2.0 * radius * by / bnorm)
        a1 = math.atan2(p1[1] - arc_center[1], p1[0] - arc_center[0])
        a2 = math.atan2(p2[1] - arc_center[1], p2[0] - arc_center[0])
        if a2 - a1 > math.pi:
            a2 -= 2 * math.pi
        elif a1 - a2 > math.pi:
            a2 += 2 * math.pi
        arc = [(arc_center[0] + radius * math.cos(a1 + (a2 - a1) * i / 29), arc_center[1] + radius * math.sin(a1 + (a2 - a1) * i / 29)) for i in range(30)]
        corners.append([vertex, *arc])
    return corners, [vertices]


def draw_geometry_figure(config: IdealRunConfig, language: str = "中文"):
    """Matplotlib figure of the geometry; used by the dialog preview and the run folder."""

    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Polygon

    # Figure text stays in English: the deployment image has no CJK font.
    fig, ax = plt.subplots(figsize=(3.6, 4.5))
    shift = config.throat_length_um / 2.0 if config.coupled else 0.0
    gap = 0.0 if config.coupled else max(2.0, 0.15 * config.large_side_um)
    pores = [
        ("large", config.large_side_um, config.large_water_saturation, False, shift + gap / 2.0),
        ("small", config.small_side_um, config.small_water_saturation, True, -shift - gap / 2.0),
    ]
    water_color, gas_color, wall_color = "#3B7DD8", "#F2F2F2", "#333333"
    for _name, side, saturation, inverted, y_shift in pores:
        outline = _triangle_vertices(side, inverted, y_shift)
        ax.add_patch(Polygon(outline, closed=True, facecolor=gas_color, edgecolor=wall_color, linewidth=1.2, zorder=1))
        water, gas = _water_patches(side, saturation, inverted, y_shift)
        for patch in water:
            ax.add_patch(Polygon(patch, closed=True, facecolor=water_color, edgecolor="none", zorder=2))
        if water_configuration(saturation) != "corner":
            for patch in gas:
                ax.add_patch(Polygon(patch, closed=True, facecolor=gas_color, edgecolor="#888888", linewidth=0.6, zorder=3))
    if config.coupled:
        half_w, half_l = config.throat_width_um / 2.0, config.throat_length_um / 2.0
        ax.add_patch(Polygon([(-half_w, -half_l), (half_w, -half_l), (half_w, half_l), (-half_w, half_l)], closed=True, facecolor=water_color, edgecolor=wall_color, linewidth=0.8, zorder=2))
    span_y_top = shift + gap / 2.0 + config.large_side_um * math.sqrt(3.0) / 2.0
    span_y_bottom = -shift - gap / 2.0 - config.small_side_um * math.sqrt(3.0) / 2.0
    margin = 0.08 * config.large_side_um
    ax.set_xlim(-config.large_side_um / 2.0 - margin, config.large_side_um / 2.0 + margin)
    ax.set_ylim(span_y_bottom - margin, span_y_top + margin)
    ax.set_aspect("equal")
    ax.set_xlabel("x (μm)")
    ax.set_ylabel("y (μm)")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    handles = [
        Patch(facecolor=water_color, label="Water"),
        Patch(facecolor=gas_color, edgecolor="#888888", label="Gas"),
        Patch(facecolor="white", edgecolor=wall_color, label="Solid wall (relaxing)"),
    ]
    ax.legend(handles=handles, loc="upper center", fontsize=7, frameon=False, ncol=3, bbox_to_anchor=(0.45, -0.16), handlelength=1.2, columnspacing=0.8)
    fig.tight_layout()
    return fig


def run_ideal_pipeline(
    context: "AgentRuntimeContext",
    language: str = "中文",
    on_stage: StageCallback | None = None,
) -> AgentToolResult:
    """Geometry -> pyGIMLi mesh + decay -> T2 inversion -> Gaussian -> interpretation."""

    from .tools import interpret_results, run_2d_mesh_and_decay, run_fixed_nnls, run_gaussian_peaks, run_lcurve

    english = _english(language)
    state = dict(context.ideal_state or {})
    config = IdealRunConfig.from_mapping(state.get("prefill"))
    problems = validate_config(config, language)
    if problems:
        state.update({"step": "params", "params_confirmed": False, "open_dialog": "ideal_params"})
        context.ideal_state = state
        return AgentToolResult("needs_confirmation", " ".join(problems), summary=_agent_summary(state), error="needs_ideal_parameter_confirmation")

    run_dir = _run_dir(context, config)
    tool_args = config.to_tool_args()
    stage_results: list[AgentToolResult] = []
    state.update({"step": "running", "run_dir": str(run_dir)})
    context.ideal_state = state

    def finish(status: str, message: str, error: str | None = None) -> AgentToolResult:
        # A new request must be confirmed again; the last run stays listed.
        state.update({"step": "done" if status == "success" else "failed", "params_confirmed": False, "last_run_dir": str(run_dir)})
        context.ideal_state = state
        stages: dict[str, list[str]] = {}
        for item in stage_results:
            for stage_name, paths in item.summary.get("simulation_stages", {}).items():
                stages.setdefault(stage_name, []).extend(str(path) for path in paths)
        compact: dict[str, Any] = {
            "stage": "ideal_full_workflow",
            "run_dir": str(run_dir),
            "config": config.to_dict(),
            "tool_args": tool_args,
            "estimated_t2_ms": {"large": estimate_pore_t2_ms(config, "large"), "small": estimate_pore_t2_ms(config, "small")},
            "water_configuration": {"large": water_configuration(config.large_water_saturation), "small": water_configuration(config.small_water_saturation)},
            "stage_status": [{"stage": item.summary.get("stage"), "status": item.status, "message": item.message} for item in stage_results],
            "simulation_decay_xlsx": str(context.simulation_decay_path) if context.simulation_decay_path else None,
            "spectrum_xlsx": str(context.spectrum_path) if context.spectrum_path else None,
            "simulation_stages": stages,
        }
        for item in stage_results:
            # Literature-based findings and AGU references from the interpretation stage.
            for key in ("literature_findings", "literature_references"):
                if item.summary.get(key):
                    compact[key] = item.summary[key]
        for item in stage_results:
            if item.summary.get("stage") == "ideal_t2_inversion":
                for key in ("metrics_xlsx", "parameters", "summary_csv", "inversion_mode", "fit_xlsx", "trimmed_xlsx"):
                    if item.summary.get(key) is not None:
                        compact[key] = item.summary[key]
        return AgentToolResult(
            "success" if status == "success" else "failed",
            message,
            artifacts=[artifact for item in stage_results for artifact in item.artifacts],
            summary=compact,
            error=error,
        )

    # 1. Geometry --------------------------------------------------------
    try:
        geometry_dir = run_dir / "00_geometry"
        preview = save_geometry_preview(config, geometry_dir / "ideal_geometry_preview.png")
        config_json = geometry_dir / "ideal_run_config.json"
        config_json.write_text(
            json.dumps(
                {
                    "confirmed_config": config.to_dict(),
                    "tool_args": tool_args,
                    "explicit_fields": state.get("explicit_fields", []),
                    "fields_filled_by_default": state.get("missing_fields_at_request", []),
                    "confirmed_at": state.get("confirmed_at"),
                    "water_configuration": {"large": water_configuration(config.large_water_saturation), "small": water_configuration(config.small_water_saturation)},
                    "corner_water_saturation_threshold": CORNER_WATER_SATURATION,
                    "boundary_conditions": {
                        "solid_water": "Robin, rho_solid",
                        "gas_water": "no flux (rho_gas is not applied in the ideal geometry)",
                        "throat_walls": "no flux",
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        large_t2 = estimate_pore_t2_ms(config, "large")
        small_t2 = estimate_pore_t2_ms(config, "small")
        message = (
            f"Ideal geometry: large side {config.large_side_um:g} μm (Sw {config.large_water_saturation:.2f}), small side {config.small_side_um:g} μm (Sw {config.small_water_saturation:.2f}), "
            + ("coupled through a throat" if config.coupled else "uncoupled")
            + f". Fast-diffusion estimates: large ≈ {large_t2:.0f} ms, small ≈ {small_t2:.0f} ms; simulated {tool_args['t_max_ms']:g} ms with dt {tool_args['dt_ms']:g} ms."
            if english
            else f"理想几何：大孔边长 {config.large_side_um:g} μm（Sw {config.large_water_saturation:.2f}），小孔边长 {config.small_side_um:g} μm（Sw {config.small_water_saturation:.2f}），"
            + ("经喉道耦合" if config.coupled else "不耦合")
            + f"。快扩散估计：大孔约 {large_t2:.0f} ms，小孔约 {small_t2:.0f} ms；模拟 {tool_args['t_max_ms']:g} ms，步长 {tool_args['dt_ms']:g} ms。"
        )
        stage_results.append(
            _emit(
                context,
                AgentToolResult(
                    "success",
                    message,
                    artifacts=[str(preview), str(config_json)],
                    summary={
                        "stage": "ideal_geometry",
                        "ideal_config": config.to_dict(),
                        "estimated_t2_ms": {"large": large_t2, "small": small_t2},
                        "water_configuration": {"large": water_configuration(config.large_water_saturation), "small": water_configuration(config.small_water_saturation)},
                        "simulation_stages": {"geometry": [str(preview), str(config_json)]},
                    },
                ),
                on_stage,
            )
        )
    except Exception as exc:
        stage_results.append(_emit(context, AgentToolResult("failed", "Ideal geometry preparation failed." if english else "理想几何准备失败。", summary={"stage": "ideal_geometry"}, error=str(exc)), on_stage))
        return finish("failed", stage_results[-1].message, str(exc))

    # 2. Mesh and decay --------------------------------------------------
    mesh = run_2d_mesh_and_decay(None, run_dir / "01_mesh_decay", tool_args, language=language)
    # Keep the mesh/decay/t2 stage grouping that the results panel already understands.
    mesh.summary = dict(mesh.summary) | {"stage": "ideal_mesh_decay", "simulation_stages": mesh.summary.get("simulation_stages") or {"mesh": list(mesh.artifacts)}}
    stage_results.append(_emit(context, mesh, on_stage))
    decay_xlsx = mesh.summary.get("standard_decay_xlsx")
    if mesh.status != "success" or not decay_xlsx:
        return finish("failed", mesh.message, mesh.error or "missing_simulation_decay")
    context.simulation_decay_path = Path(str(decay_xlsx))
    context.repaired_path = Path(str(decay_xlsx))

    # 3. T2 inversion ----------------------------------------------------
    inversion_dir = run_dir / "02_t2_inversion"
    if config.run_lcurve:
        inversion = run_lcurve(
            context.repaired_path,
            inversion_dir / "lcurve",
            {
                "time_to_ms_scale": 1.0,
                "num_bins": int(config.num_bins),
                "t2_min_ms": 1e-2,
                "t2_max_ms": 1e5,
                "alpha_min": 1e-5 if config.lcurve_criterion == "curvature" else 1e-6,
                "alpha_max": 1e2,
                "alpha_count": 36 if config.lcurve_criterion == "curvature" else 60,
                "criterion": config.lcurve_criterion,
            },
            language=language,
        )
    else:
        inversion = run_fixed_nnls(
            context.repaired_path,
            inversion_dir / "nnls",
            {"time_to_ms_scale": 1.0, "regularization": float(config.regularization), "num_bins": int(config.num_bins), "t2_min_ms": 1.0, "t2_max_ms": 1e4},
            language=language,
        )
    inversion.summary = dict(inversion.summary) | {
        "stage": "ideal_t2_inversion",
        "inversion_mode": "lcurve" if config.run_lcurve else "fixed_nnls",
        "simulation_decay_xlsx": str(context.repaired_path),
        "simulation_stages": {"inversion": list(inversion.artifacts)},
    }
    stage_results.append(_emit(context, inversion, on_stage))
    if inversion.status != "success" or not inversion.summary.get("spectrum_xlsx"):
        return finish("failed", inversion.message, inversion.error)
    context.spectrum_path = Path(str(inversion.summary["spectrum_xlsx"]))

    # 4. Gaussian --------------------------------------------------------
    if config.run_gaussian:
        gaussian = run_gaussian_peaks(context.spectrum_path, run_dir / "03_gaussian", {"peak_count": int(config.peak_count)}, language=language)
        gaussian.summary = dict(gaussian.summary) | {"stage": "ideal_gaussian", "simulation_stages": {"gaussian": list(gaussian.artifacts)}}
        stage_results.append(_emit(context, gaussian, on_stage))

    # 5. Interpretation --------------------------------------------------
    interpretation = interpret_results(stage_results, run_dir / "04_interpretation", language=language)
    interpretation.summary = dict(interpretation.summary) | {"stage": "ideal_interpretation", "simulation_stages": {"report": list(interpretation.artifacts)}}
    stage_results.append(_emit(context, interpretation, on_stage))

    failed = [item for item in stage_results if item.status != "success"]
    message = (
        "Ideal-structure NMR workflow completed: geometry, pyGIMLi mesh and decay, T2 inversion"
        + (", Gaussian decomposition" if config.run_gaussian else "")
        + " and interpretation."
        if english
        else "理想结构 NMR 流程完成：几何、pyGIMLi 网格与衰减、T2 反演" + ("、高斯分峰" if config.run_gaussian else "") + "和结果解释。"
    )
    if failed:
        message += (" Some later stages failed: " if english else " 部分后续步骤失败：") + ", ".join(str(item.summary.get("stage")) for item in failed)
    return finish("success", message)
