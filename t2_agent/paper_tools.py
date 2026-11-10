"""Agent tools for the paper's controlled-pore cases and the pixel-grid CT solver.

Each tool runs one case of ``t2_agent.paper_sim`` with the manuscript defaults
(Table 1) unless the user states other values, and returns the figure,
workbook and summary as artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .models import AgentToolResult

if TYPE_CHECKING:  # pragma: no cover
    from .agent import AgentRuntimeContext

PAPER_TOOL_NAMES = (
    "simulate_pore_shapes",
    "simulate_saturation_series",
    "simulate_contact_angle_series",
    "simulate_dual_pore_exchange",
    "simulate_ct_slice_pixel_grid",
)

_PHYSICS_PROPERTIES = {
    "diffusion_um2_per_ms": {"type": "number", "description": "Water self-diffusion coefficient; default 2 um^2/ms."},
    "bulk_relaxation_ms": {"type": "number", "description": "Bulk T1 = T2 of water; default 3000 ms."},
    "surface_relaxivity_um_per_ms": {"type": "number", "description": "rho1 = rho2 on solid-water walls; default 0.005 um/ms."},
}
_TWO_D_PROPERTIES = {
    "include_dt2": {"type": "boolean", "description": "Also compute and invert D-T2 maps (narrow-pulse PFG). Default true."},
    "include_t1t2": {"type": "boolean", "description": "Also compute and invert T1-T2 maps (saturation recovery). Default true."},
}


def paper_tool_specs() -> list[dict[str, Any]]:
    def spec(name: str, description: str, properties: dict[str, Any]) -> dict[str, Any]:
        return {"type": "function", "function": {"name": name, "description": description,
                "parameters": {"type": "object", "properties": properties, "required": [], "additionalProperties": False}}}

    return [
        spec(
            "simulate_pore_shapes",
            "Paper case (Fig. 4): fully saturated circle, equilateral triangle and 30-60-90 triangle of equal area. Solves T2 (and optionally D-T2, T1-T2) with consistent-mass FEM on pyGIMLi meshes, inverts with the manuscript settings and draws the manuscript-style figure.",
            {"area_um2": {"type": "number", "description": "Common pore area; default 173.21 um^2 (equilateral side 20 um)."}, **_TWO_D_PROPERTIES, **_PHYSICS_PROPERTIES},
        ),
        spec(
            "simulate_saturation_series",
            "Paper case (Fig. 6): drained equilateral pore with water in the three corners at several saturations (plus Sw = 1), meniscus at a given contact angle, water-air menisci no-flux. Solves T2, D-T2 and T1-T2 and draws the manuscript-style figure.",
            {"saturations": {"type": "array", "items": {"type": "number"}, "description": "Water saturations as fractions (0-1), e.g. [0.0226, 0.153, 0.38, 1.0] (default). Corner states must be below the corner-water limit (0.395 at 0 degrees)."},
             "contact_angle_deg": {"type": "number", "description": "Contact angle of the menisci; default 0."},
             "side_um": {"type": "number", "description": "Triangle side; default 20 um."}, **_TWO_D_PROPERTIES, **_PHYSICS_PROPERTIES},
        ),
        spec(
            "simulate_contact_angle_series",
            "Paper case (Fig. 7): several contact angles at the same water saturation in an equilateral pore; the meniscus radius is solved so that the water area is identical. Solves T2, D-T2 and T1-T2 and draws the manuscript-style figure.",
            {"saturation": {"type": "number", "description": "Common water saturation as a fraction; default 0.153."},
             "contact_angles_deg": {"type": "array", "items": {"type": "number"}, "description": "Contact angles in degrees; default [0, 30, 45]. Must be below 60 degrees."},
             "side_um": {"type": "number", "description": "Triangle side; default 20 um."}, **_TWO_D_PROPERTIES, **_PHYSICS_PROPERTIES},
        ),
        spec(
            "simulate_dual_pore_exchange",
            "Paper case (Fig. 5): two saturated equilateral pores as well-mixed compartments exchanging magnetization at k_ex = D_eff / l_c^2 (effective compartment model, not a meshed throat). Returns uncoupled and coupled T2 spectra, fast-exchange limit and the k_ex / rate-difference ratio.",
            {"large_side_um": {"type": "number", "description": "Default 20 um."}, "small_side_um": {"type": "number", "description": "Default 8 um."},
             "exchange_length_um": {"type": "number", "description": "Channel length l_c; default 5 um."},
             "effective_diffusion_um2_per_ms": {"type": "number", "description": "D_eff in the channel; default 1.667 um^2/ms (k_ex = 0.0667 1/ms)."},
             **_PHYSICS_PROPERTIES},
        ),
        spec(
            "simulate_ct_slice_pixel_grid",
            "Paper solver for a segmented CT slice (Fig. 9): finite-volume scheme on the full pixel grid with surface relaxation on water faces against solid, background and the image edge; L-curve (maximum curvature) inversion on the extended 150-bin grid; local pore-size distribution. Needs an uploaded TIF, its pixel size and the phase labels (taken from the confirmed CT phase markers if available).",
            {"pixel_size_um": {"type": "number", "description": "CT resolution in um per pixel, as stated by the user."},
             "phase_labels": {"type": "object", "description": "Label values, e.g. {\"solid\": 255, \"water\": 102, \"air\": 153, \"background\": 0}; only values the user stated.",
                              "properties": {"solid": {"type": "integer"}, "water": {"type": "integer"}, "air": {"type": "integer"}, "background": {"type": "integer"}},
                              "additionalProperties": False},
             "clean_labels": {"type": "boolean", "description": "Smooth interfaces and remove single-pixel noise as in the paper; default true."},
             "fixed_alpha": {"type": "number", "description": "Alpha of the comparison fixed-alpha inversion; default 1."}},
        ),
    ]


PAPER_SKILLS = [
    {"name": "simulate_pore_shapes", "purpose": "Equal-area circle / equilateral / right-triangle pores with T2, D-T2 and T1-T2 and the manuscript figure.",
     "when_to_use": "User asks how pore shape changes T2, or for the paper's pore-shape comparison."},
    {"name": "simulate_saturation_series", "purpose": "Corner-water states of a drained triangular pore at several saturations with T2, D-T2 and T1-T2.",
     "when_to_use": "User asks how drainage/partial saturation shifts T2, or why a saturated calibration fails for corner water."},
    {"name": "simulate_contact_angle_series", "purpose": "Several contact angles at equal water area with T2, D-T2 and T1-T2.",
     "when_to_use": "User asks about wettability or contact angle effects on T2."},
    {"name": "simulate_dual_pore_exchange", "purpose": "Two pores with and without diffusive exchange (compartment model) and the fast-exchange limit.",
     "when_to_use": "User asks about pore coupling, exchange, or why two pore sizes give one peak."},
    {"name": "simulate_ct_slice_pixel_grid", "purpose": "Paper's pixel-grid finite-volume solution of a segmented CT slice with L-curve inversion and the Fig. 9 figure.",
     "when_to_use": "User uploaded a segmented TIF and asks for the paper's pixel-grid method or a reproduction of the glass-bead slice; the default CT route remains run_ct_simulation_workflow (triangular mesh)."},
]


def _english(language: str) -> bool:
    return str(language).lower().startswith("en")


def _settings(args: dict[str, Any]):
    from .paper_sim.settings import PaperSettings

    values: dict[str, Any] = {}
    if args.get("diffusion_um2_per_ms"):
        values["diffusion_um2_per_ms"] = float(args["diffusion_um2_per_ms"])
    if args.get("bulk_relaxation_ms"):
        values["t1_bulk_ms"] = values["t2_bulk_ms"] = float(args["bulk_relaxation_ms"])
    if args.get("surface_relaxivity_um_per_ms") is not None:
        values["rho1_um_per_ms"] = values["rho2_um_per_ms"] = float(args["surface_relaxivity_um_per_ms"])
    return PaperSettings(**values)


def _fractions(values: list[Any] | None) -> list[float] | None:
    if not values:
        return None
    out = []
    for value in values:
        value = float(value)
        out.append(value / 100.0 if value > 1.0 else value)
    return out


def _compact(summary: dict[str, Any]) -> dict[str, Any]:
    skip = {"settings", "inversion", "meshes", "dimensions"}
    return {k: v for k, v in summary.items() if k not in skip}


def _message(name: str, summary: dict[str, Any], english: bool) -> str:
    if name == "simulate_dual_pore_exchange":
        unc = ", ".join(f"{v:.0f}" for v in summary["uncoupled_peaks_ms"])
        cpl = ", ".join(f"{v:.0f}" for v in summary["coupled_peaks_ms"])
        if english:
            return (f"Dual pore: uncoupled peaks at {unc} ms, coupled peaks at {cpl} ms; fast-exchange limit {summary['fast_exchange_limit_T2_ms']:.0f} ms; "
                    f"k_ex is {summary['k_ex_over_rate_difference']:.1f} times the relaxation-rate difference.")
        return (f"双孔：非耦合峰 {unc} ms，耦合峰 {cpl} ms；快交换极限 {summary['fast_exchange_limit_T2_ms']:.0f} ms；"
                f"k_ex 是两孔弛豫速率差的 {summary['k_ex_over_rate_difference']:.1f} 倍。")
    if name == "simulate_ct_slice_pixel_grid":
        stats = summary["statistics"]
        if english:
            return (f"Pixel-grid slice: 2D porosity {stats['porosity_2d']:.1%}, Sw {stats['water_saturation']:.1%}, "
                    f"T2 peak {summary['peak_T2_ms']:.0f} ms (L-curve alpha {summary['selected_alpha']:.3g}).")
        return (f"像素网格切片：二维孔隙度 {stats['porosity_2d']:.1%}，含水饱和度 {stats['water_saturation']:.1%}，"
                f"T2 峰 {summary['peak_T2_ms']:.0f} ms（L-curve alpha {summary['selected_alpha']:.3g}）。")
    rows = summary.get("results", [])
    label = {"simulate_pore_shapes": "case", "simulate_saturation_series": "saturation", "simulate_contact_angle_series": "contact_angle_deg"}[name]
    parts = []
    for row in rows:
        key = row[label]
        if label == "saturation":
            key = f"Sw {100 * key:g}%"
        elif label == "contact_angle_deg":
            key = f"{key:g}°"
        parts.append(f"{key}: {row['peak_T2_ms']:.0f} ms")
    return ("T2 peaks — " if english else "T2 峰位——") + "; ".join(parts)


def _ct_inputs(context: "AgentRuntimeContext", args: dict[str, Any]) -> tuple[dict[str, int] | None, float | None]:
    labels: dict[str, int] | None = None
    if args.get("phase_labels"):
        labels = {k: int(v) for k, v in args["phase_labels"].items() if v is not None}
    state = context.ct_state or {}
    if labels is None and state.get("phase_confirmed") and state.get("image_path") == str(Path(context.uploaded_path or "")):
        labels = {phase: int(value) for value, phase in state.get("assignment", {}).items()}
    pixel = args.get("pixel_size_um") or (state.get("prefill") or {}).get("pixel_size_um")
    return labels, float(pixel) if pixel else None


def run_paper_tool(name: str, args: dict[str, Any], context: "AgentRuntimeContext", language: str = "中文") -> AgentToolResult:
    from .paper_sim import workflows as W
    from .paper_sim.settings import ExchangeSettings

    english = _english(language)
    base = Path(context.workspace) / "paper_cases"
    progress = getattr(context, "stage_callback", None)

    def note(text: str) -> None:
        if callable(progress):
            try:
                progress(AgentToolResult("success", text, summary={"stage": "paper_case"}))
            except Exception:
                pass

    try:
        if name == "simulate_pore_shapes":
            run = W.run_shape_comparison(base, area_um2=args.get("area_um2"), include_dt2=args.get("include_dt2", True),
                                         include_t1t2=args.get("include_t1t2", True), settings=_settings(args), progress=note)
        elif name == "simulate_saturation_series":
            run = W.run_saturation_series(base, saturations=_fractions(args.get("saturations")), contact_angle_deg=float(args.get("contact_angle_deg", 0.0)),
                                          side_um=float(args.get("side_um", 20.0)), include_dt2=args.get("include_dt2", True),
                                          include_t1t2=args.get("include_t1t2", True), settings=_settings(args), progress=note)
        elif name == "simulate_contact_angle_series":
            saturation = float(args.get("saturation", 0.153))
            run = W.run_contact_angle_series(base, saturation=saturation / 100.0 if saturation > 1 else saturation,
                                             contact_angles_deg=args.get("contact_angles_deg"), side_um=float(args.get("side_um", 20.0)),
                                             include_dt2=args.get("include_dt2", True), include_t1t2=args.get("include_t1t2", True),
                                             settings=_settings(args), progress=note)
        elif name == "simulate_dual_pore_exchange":
            exchange = ExchangeSettings(exchange_length_um=float(args.get("exchange_length_um", 5.0)),
                                        effective_diffusion_um2_per_ms=float(args.get("effective_diffusion_um2_per_ms", 1.667)))
            run = W.run_dual_pore_exchange(base, large_side_um=float(args.get("large_side_um", 20.0)), small_side_um=float(args.get("small_side_um", 8.0)),
                                           exchange=exchange, settings=_settings(args), progress=note)
        elif name == "simulate_ct_slice_pixel_grid":
            upload = context.uploaded_path
            if upload is None or Path(upload).suffix.lower() not in {".tif", ".tiff"}:
                return AgentToolResult("failed", "Upload a segmented CT TIF first." if english else "请先上传分割好的 CT TIF 图像。", error="not_ct_tif")
            labels, pixel = _ct_inputs(context, args)
            missing = [item for item, ok in (("pixel_size_um", pixel), ("phase_labels", labels and "solid" in labels and "water" in labels)) if not ok]
            if missing:
                text = ("Ask the user for: " + ", ".join(missing) + " (pixel size in um per pixel; label values of solid, water, air and background)."
                        if english else "需要用户提供：" + "、".join(missing) + "（像素尺寸 μm/像素；固体、水、空气和背景的标签值）。")
                return AgentToolResult("failed", text, error="missing_ct_inputs", summary={"missing": missing})
            run = W.run_slice_pixel_fv(base, Path(upload), pixel_size_um=pixel, phase_values=labels, clean=bool(args.get("clean_labels", True)),
                                       fixed_alpha=float(args.get("fixed_alpha", 1.0)), progress=note)
        else:
            return AgentToolResult("failed", f"Unknown paper tool {name}", error="unknown_tool")
    except ValueError as exc:
        return AgentToolResult("failed", str(exc), error="invalid_parameters")
    except Exception as exc:  # solver or plotting failure
        return AgentToolResult("failed", (f"The calculation failed: {exc}" if english else f"计算失败：{exc}"), error="paper_case_failed")
    summary = run["summary"]
    return AgentToolResult("success", _message(name, summary, english), artifacts=run["artifacts"],
                           summary={"stage": name, "run_dir": run["run_dir"], **_compact(summary)})
