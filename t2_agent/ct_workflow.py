"""Agent tools and staged pipeline for segmented CT TIF -> NMR simulation -> T2.

State for one uploaded CT image lives in ``AgentRuntimeContext.ct_state`` so the
language agent (chat) and the Streamlit widgets (background question, phase
marker preview, parameter dialog) drive the same workflow:

``background`` -> ``phases`` -> ``params`` -> ``running`` -> ``done``

Only the user can confirm the phase assignment (through the preview). The
pipeline itself is deterministic and reuses the PyGIMLi mesh/solver helpers in
:mod:`t2_agent.simulation_2d` and the mature T2 tools in :mod:`t2_agent.tools`.
"""

from __future__ import annotations

from datetime import datetime
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import numpy as np
import pandas as pd

from .models import AgentToolResult

if TYPE_CHECKING:  # pragma: no cover
    from .agent import AgentRuntimeContext


StageCallback = Callable[[AgentToolResult], None]

CT_PARAM_FIELDS = (
    "pixel_size_um",
    "diffusion_um2_per_ms",
    "bulk_t2_ms",
    "rho_solid_um_per_ms",
    "rho_gas_um_per_ms",
    "dt_ms",
    "t_max_ms",
    "mesh_boundary_px",
    "mesh_bulk_px",
    "run_lcurve",
    "regularization",
    "num_bins",
    "t2_min_ms",
    "t2_max_ms",
    "run_gaussian",
    "peak_count",
    "relaxing_edges",
    "lcurve_criterion",
)
SIMULATION_CORE_FIELDS = ("diffusion_um2_per_ms", "bulk_t2_ms", "rho_solid_um_per_ms")


def _english(language: str) -> bool:
    return str(language).lower().startswith("english")


def _ct():
    try:
        from . import ct_phase
    except ImportError as exc:
        raise RuntimeError(
            "The segmented-CT simulation workflow is unavailable because the simulation "
            f"modules could not be imported ({exc}). Install the full conda/Docker environment "
            "or restart the app after an update; T2 inversion workflows still work."
        ) from exc
    return ct_phase


def is_ct_upload(path: Path | str | None) -> bool:
    return path is not None and Path(path).suffix.lower() in {".tif", ".tiff"}


# ---------------------------------------------------------------------------
# Prompt / argument merging
# ---------------------------------------------------------------------------


def collect_prefill(user_text: str, args: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Merge parameters stated in the prompt and in tool arguments.

    Returns the values and the list of fields the user actually provided.
    Tool arguments from the model win over regex parsing because the model sees
    the whole conversation; regex parsing guards against omitted arguments.
    """

    ct = _ct()
    values: dict[str, Any] = {}
    explicit: list[str] = []
    pixel = ct.parse_pixel_size_um(user_text)
    if pixel is not None:
        values["pixel_size_um"] = pixel
    values.update({key: value for key, value in ct.parse_run_preferences(user_text).items()})
    for key in (*CT_PARAM_FIELDS, "defaults_accepted"):
        if args.get(key) is not None:
            values[key] = args[key]
    if args.get("pixel_size_x_um") and "pixel_size_um" not in values:
        values["pixel_size_um"] = args["pixel_size_x_um"]
    explicit = [key for key in values if key in CT_PARAM_FIELDS or key == "defaults_accepted"]
    if values.get("regularization") is not None and "run_lcurve" not in values:
        values["run_lcurve"] = False
        explicit.append("run_lcurve")
    return values, explicit


def missing_confirmation_fields(prefill: dict[str, Any], explicit: list[str]) -> list[str]:
    """Fields the parameter dialog must confirm because the prompt did not give them."""

    missing: list[str] = []
    if "pixel_size_um" not in explicit:
        missing.append("pixel_size_um")
    if "run_lcurve" not in explicit:
        missing.append("run_lcurve")
    if "run_gaussian" not in explicit:
        missing.append("run_gaussian")
    accepted = bool(prefill.get("defaults_accepted"))
    if not accepted and not any(field in explicit for field in SIMULATION_CORE_FIELDS):
        missing.append("simulation_core")
    if prefill.get("run_lcurve") is False and "regularization" not in explicit and not accepted:
        missing.append("regularization")
    return missing


# ---------------------------------------------------------------------------
# Agent tools
# ---------------------------------------------------------------------------


def _phase_summary_for_agent(state: dict[str, Any], language: str) -> str:
    ct = _ct()
    lines = []
    for value, phase in sorted(state.get("assignment", {}).items(), key=lambda item: int(item[0])):
        stats = state.get("value_stats", {}).get(str(value), {})
        lines.append(f"{value} -> {ct.phase_name(phase, language)} ({float(stats.get('fraction', 0.0)):.1%})")
    return "; ".join(lines)


def inspect_ct_phase_image(
    context: "AgentRuntimeContext",
    args: dict[str, Any],
    language: str = "中文",
) -> AgentToolResult:
    """Analyse an uploaded segmented CT label TIF and set up phase confirmation."""

    try:
        ct = _ct()
    except RuntimeError as exc:
        message = "CT simulation modules are unavailable." if _english(language) else "CT 模拟模块不可用。"
        return AgentToolResult("failed", message, error=str(exc))
    if not is_ct_upload(context.uploaded_path):
        message = (
            "The active upload is not a TIF/TIFF segmented CT image."
            if _english(language)
            else "当前激活文件不是 TIF/TIFF 分割 CT 图像。"
        )
        return AgentToolResult("failed", message, error="not_ct_tif")

    user_text = context.last_user_goal or ""
    previous = dict(context.ct_state or {})
    same_image = previous.get("image_path") == str(Path(context.uploaded_path))

    has_background = ct.parse_background_statement(user_text)
    source = "prompt" if has_background is not None else None
    if has_background is None and args.get("has_background") is not None:
        has_background = bool(args["has_background"])
        source = "agent"
    if has_background is None and same_image and previous.get("has_background") is not None:
        has_background = bool(previous["has_background"])
        source = previous.get("has_background_source", "previous")

    explicit_labels: dict[str, int] = {}
    labels_arg = args.get("phase_labels")
    if isinstance(labels_arg, dict):
        for phase, value in labels_arg.items():
            if phase in ct.PHASES and value is not None:
                try:
                    explicit_labels[phase] = int(value)
                except (TypeError, ValueError):
                    continue

    try:
        array, _meta = ct.load_label_image(Path(context.uploaded_path))
        values = [int(value) for value in np.unique(array)]
    except Exception as exc:
        message = "Could not read the TIF image." if _english(language) else "无法读取 TIF 图像。"
        return AgentToolResult("failed", message, error=str(exc))

    parsed_labels = ct.parse_phase_labels(user_text, values)
    for phase, value in parsed_labels.items():
        explicit_labels.setdefault(phase, value)
    if source is None and explicit_labels:
        source = "prompt_labels"

    if (
        same_image
        and previous.get("phase_confirmed")
        and (has_background is None or has_background == previous.get("has_background"))
        and not explicit_labels
    ):
        # Re-inspecting must not silently discard a phase assignment the user confirmed.
        prefill, explicit = collect_prefill(user_text, args)
        previous["prefill"] = dict(previous.get("prefill", {})) | prefill
        previous["explicit_fields"] = sorted(set(previous.get("explicit_fields", [])) | set(explicit))
        context.ct_state = previous
        message = (
            "The user already confirmed the phase assignment for this image; keep it and continue with run_ct_simulation_workflow."
            if _english(language)
            else "用户已确认过该图像的相态判定，保持不变，可继续调用 run_ct_simulation_workflow。"
        )
        return AgentToolResult("success", message, summary=_agent_summary(previous))

    output_dir = context.workspace / "ct_simulation" / "phase_check"
    analysis = ct.analyze_ct_label_image(
        Path(context.uploaded_path),
        output_dir,
        has_background=has_background,
        explicit_labels=explicit_labels or None,
    )
    if len(values) == 2:
        source = "not_needed_two_values"

    prefill, explicit = collect_prefill(user_text, args)
    if same_image:
        previous_prefill = dict(previous.get("prefill", {}))
        previous_explicit = list(previous.get("explicit_fields", []))
        prefill = previous_prefill | prefill
        explicit = sorted(set(previous_explicit) | set(explicit))

    state: dict[str, Any] = {
        "image_path": str(Path(context.uploaded_path)),
        "values": analysis.get("values", values),
        "value_stats": analysis.get("value_stats", {}),
        "display_png": analysis.get("display_png"),
        "display_gray_levels": analysis.get("display_gray_levels", {}),
        "has_background": analysis.get("has_background"),
        "has_background_source": source,
        "prefill": prefill,
        "explicit_fields": explicit,
        "missing_fields": missing_confirmation_fields(prefill, explicit),
        "revision": int(previous.get("revision", 0)) + 1,
        "last_event_id": previous.get("last_event_id"),
        "phase_confirmed": False,
        "params_confirmed": False,
        "analysis_status": analysis["status"],
    }
    artifacts = [path for path in analysis.get("artifacts", []) if path]

    if analysis["status"] == "failed":
        state["step"] = "failed"
        context.ct_state = state
        return AgentToolResult("failed", analysis["message"], artifacts=artifacts, summary=_agent_summary(state, analysis), error=analysis.get("error"))

    if analysis["status"] == "needs_background_answer":
        state["step"] = "background"
        state["suggested_has_background"] = analysis.get("suggested_has_background")
        context.ct_state = state
        message = (
            f"The TIF has {len(values)} pixel values {values}. Ask the user whether it contains background (outside-sample) pixels before assigning phases. The UI shows two buttons for this answer."
            if _english(language)
            else f"该 TIF 含 {len(values)} 种像素值 {values}。在判定相态前必须先询问用户：图像中是否含有背景（样品外部）像素？右侧面板也提供了两个按钮供用户回答。"
        )
        return AgentToolResult(
            "needs_confirmation",
            message,
            artifacts=artifacts,
            summary=_agent_summary(state, analysis) | {"question": "has_background", "suggested_has_background": analysis.get("suggested_has_background")},
            error="needs_background_answer",
        )

    state.update(
        {
            "step": "phases",
            "ai_assignment": analysis["ai_assignment"],
            "assignment": analysis["assignment"],
            "assignment_source": analysis["assignment_source"],
            "ai_reasons": analysis["ai_reasons"],
            "ai_confidence": analysis["ai_confidence"],
            "prompt_agrees_with_ai": analysis.get("prompt_agrees_with_ai"),
            "markers": analysis["markers"],
            "value_points": analysis["value_points"],
            "preview_png": analysis["preview_png"],
            "open_dialog": "phases",
        }
    )
    context.ct_state = state
    message = (
        "Phase preview is ready. The user must check the AI markers on the CT image and confirm or drag-correct them; meshing waits for that confirmation. "
        f"Current assignment: {_phase_summary_for_agent(state, language)}."
        if _english(language)
        else "相态预览已生成。用户需要在 CT 图像预览中检查 AI 标记，确认或拖拽纠正后才会网格划分。"
        f"当前判定：{_phase_summary_for_agent(state, language)}。"
    )
    return AgentToolResult(
        "needs_confirmation",
        message,
        artifacts=artifacts,
        summary=_agent_summary(state, analysis),
        error="needs_phase_confirmation",
    )


def _agent_summary(state: dict[str, Any], analysis: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = {
        "stage": "ct_phase_check",
        "workflow_step": state.get("step"),
        "values": state.get("values"),
        "value_fractions": {key: round(float(item.get("fraction", 0.0)), 4) for key, item in state.get("value_stats", {}).items()},
        "has_background": state.get("has_background"),
        "has_background_source": state.get("has_background_source"),
        "assignment": state.get("assignment"),
        "ai_assignment": state.get("ai_assignment"),
        "assignment_source": state.get("assignment_source"),
        "ai_confidence": state.get("ai_confidence"),
        "ai_reasons": state.get("ai_reasons"),
        "prompt_agrees_with_ai": state.get("prompt_agrees_with_ai"),
        "phase_confirmed": state.get("phase_confirmed"),
        "params_prefill": state.get("prefill"),
        "params_missing_for_dialog": state.get("missing_fields"),
        "simulation_stages": {"geometry": [path for path in (state.get("display_png"), state.get("preview_png")) if path]},
    }
    if analysis and analysis.get("message") and analysis.get("status") == "failed":
        summary["failure"] = analysis.get("message")
    return summary


def set_background_answer(context: "AgentRuntimeContext", has_background: bool, language: str = "中文") -> AgentToolResult:
    """UI callback for the background question; re-runs the analysis."""

    state = dict(context.ct_state or {})
    context.ct_state = state | {"has_background": bool(has_background), "has_background_source": "user_ui"}
    args = {"has_background": bool(has_background)}
    saved_goal = context.last_user_goal
    context.last_user_goal = ""
    try:
        result = inspect_ct_phase_image(context, args, language)
    finally:
        context.last_user_goal = saved_goal
    if context.ct_state:
        context.ct_state["has_background_source"] = "user_ui"
    return result


def confirm_phase_assignment(context: "AgentRuntimeContext", assignment: dict[str, str], language: str = "中文") -> AgentToolResult:
    """Persist the user-confirmed phase assignment (called by the preview dialog)."""

    ct = _ct()
    state = dict(context.ct_state or {})
    problems = ct.validate_assignment(assignment, state.get("values", []), bool(state.get("has_background")))
    if problems:
        return AgentToolResult("failed", " ".join(problems), error="invalid_assignment")
    corrected = {
        value: {"ai": state.get("ai_assignment", {}).get(value), "confirmed": phase}
        for value, phase in assignment.items()
        if state.get("ai_assignment", {}).get(value) != phase
    }
    try:
        array, _meta = ct.load_label_image(Path(state["image_path"]))
        labels = ct.apply_phase_assignment(array, assignment)
        # S/V in 1/pixel; divide by the pixel size (um) for 1/um in the parameter dialog.
        state["surface_to_volume_per_px"] = ct.estimate_surface_t2(labels, 1.0, 3000.0, 0.0)["surface_to_volume_per_um"]
    except Exception:
        state["surface_to_volume_per_px"] = None
    state.update(
        {
            "assignment": dict(assignment),
            "phase_confirmed": True,
            "user_corrections": corrected,
            "confirmed_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    state["step"] = "params" if state.get("missing_fields") else "ready"
    state["open_dialog"] = "params" if state["step"] == "params" else None
    context.ct_state = state
    if _english(language):
        message = "Phase assignment confirmed" + (f" with {len(corrected)} manual correction(s)." if corrected else "; the AI guess was accepted.")
    else:
        message = "相态判定已确认" + (f"，用户手动纠正了 {len(corrected)} 处。" if corrected else "，采用 AI 初判。")
    return AgentToolResult("success", message, summary={"stage": "ct_phase_confirmed", "assignment": assignment, "user_corrections": corrected})


def confirm_run_parameters(context: "AgentRuntimeContext", params: dict[str, Any]) -> None:
    state = dict(context.ct_state or {})
    state["prefill"] = dict(state.get("prefill", {})) | dict(params)
    state["params_confirmed"] = True
    state["missing_fields"] = []
    state["step"] = "ready"
    state["open_dialog"] = None
    context.ct_state = state


def request_ct_run(
    context: "AgentRuntimeContext",
    args: dict[str, Any],
    language: str = "中文",
    on_stage: StageCallback | None = None,
) -> AgentToolResult:
    """Agent tool: run the CT pipeline when phases and parameters are confirmed."""

    state = dict(context.ct_state or {})
    if not state or state.get("image_path") != str(Path(context.uploaded_path or "")):
        result = inspect_ct_phase_image(context, args, language)
        if result.status == "failed":
            return result
        state = dict(context.ct_state or {})

    if state.get("step") == "background":
        return AgentToolResult(
            "needs_confirmation",
            "The user still has to say whether the image contains background pixels." if _english(language) else "还需要用户回答图像是否含有背景像素。",
            summary=_agent_summary(state),
            error="needs_background_answer",
        )

    prefill, explicit = collect_prefill(context.last_user_goal or "", args)
    state["prefill"] = dict(state.get("prefill", {})) | prefill
    state["explicit_fields"] = sorted(set(state.get("explicit_fields", [])) | set(explicit))
    if not state.get("params_confirmed"):
        state["missing_fields"] = missing_confirmation_fields(state["prefill"], state["explicit_fields"])
    context.ct_state = state

    if not state.get("phase_confirmed"):
        state["open_dialog"] = "phases"
        context.ct_state = state
        return AgentToolResult(
            "needs_confirmation",
            "Waiting for the user to confirm the phase markers in the CT preview dialog." if _english(language) else "等待用户在 CT 相态预览窗口中确认（或拖拽纠正）相态标记。",
            summary=_agent_summary(state),
            error="needs_phase_confirmation",
        )
    if state.get("missing_fields") and not state.get("params_confirmed"):
        state["step"] = "params"
        state["open_dialog"] = "params"
        context.ct_state = state
        return AgentToolResult(
            "needs_confirmation",
            (
                f"Waiting for the parameter confirmation dialog; missing: {', '.join(state['missing_fields'])}."
                if _english(language)
                else f"等待用户在参数确认窗口中确认参数；提示词缺少：{', '.join(state['missing_fields'])}。"
            ),
            summary=_agent_summary(state),
            error="needs_parameter_confirmation",
        )
    return run_ct_pipeline(context, language=language, on_stage=on_stage)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def _emit(context: "AgentRuntimeContext", result: AgentToolResult, on_stage: StageCallback | None) -> AgentToolResult:
    context.results.append(result)
    context.tool_history.append(result)
    if on_stage is not None:
        on_stage(result)
    return result


def _run_dir(context: "AgentRuntimeContext") -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    stem = Path(context.uploaded_path or "ct").stem
    path = context.workspace / "ct_simulation" / f"{stem}__run_{stamp}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_ct_pipeline(
    context: "AgentRuntimeContext",
    language: str = "中文",
    on_stage: StageCallback | None = None,
) -> AgentToolResult:
    """Geometry -> PyGIMLi mesh -> decay -> T2 inversion -> Gaussian -> interpretation."""

    from . import simulation_2d as sim
    from .tools import interpret_results, run_fixed_nnls, run_gaussian_peaks, run_lcurve

    ct = _ct()
    english = _english(language)
    state = dict(context.ct_state or {})
    config = ct.CtRunConfig.from_mapping(state.get("prefill"))
    run_dir = _run_dir(context)
    stage_results: list[AgentToolResult] = []
    state["step"] = "running"
    state["run_dir"] = str(run_dir)
    context.ct_state = state

    def finish(status: str, message: str, error: str | None = None) -> AgentToolResult:
        state["step"] = "done" if status == "success" else "failed"
        context.ct_state = state
        stages: dict[str, list[str]] = {}
        for item in stage_results:
            for stage_name, paths in item.summary.get("simulation_stages", {}).items():
                stages.setdefault(stage_name, []).extend(str(path) for path in paths)
        compact = {
            "stage": "ct_full_workflow",
            "run_dir": str(run_dir),
            "config": config.to_dict(),
            "assignment": state.get("assignment"),
            "user_corrections": state.get("user_corrections"),
            "stage_status": [{"stage": item.summary.get("stage"), "status": item.status, "message": item.message} for item in stage_results],
            "simulation_decay_xlsx": str(context.simulation_decay_path) if context.simulation_decay_path else None,
            "spectrum_xlsx": str(context.spectrum_path) if context.spectrum_path else None,
            "simulation_stages": stages,
        }
        for item in stage_results:
            # Literature-based findings and AGU references from the interpretation stage.
            for key in ("literature_findings", "literature_references", "simulation_report_figure", "local_pore_diameter_um"):
                if item.summary.get(key):
                    compact[key] = item.summary[key]
        for item in stage_results:
            # Lets the interactive L-curve alpha picker work on the aggregate result.
            if item.summary.get("stage") == "ct_t2_inversion":
                for key in ("metrics_xlsx", "parameters", "summary_csv", "inversion_mode"):
                    if item.summary.get(key) is not None:
                        compact[key] = item.summary[key]
        for item in stage_results:
            if item.summary.get("stage") == "ct_mesh":
                compact["mesh"] = {key: item.summary.get(key) for key in ("mesh_nodes", "mesh_triangles", "min_element_quality", "mean_element_quality", "solid_liquid_boundary_length_um", "gas_liquid_boundary_length_um", "noflux_boundary_length_um", "relaxing_edge_length_um")}
            if item.summary.get("stage") == "ct_decay":
                compact["decay"] = {key: item.summary.get(key) for key in ("estimated_t2_ms", "surface_to_volume_per_um", "dt_ms", "t_max_ms", "final_normalized_signal")}
                compact["decay"]["bulk_t2_ms"] = config.bulk_t2_ms
                compact["decay"]["rho_solid_um_per_ms"] = config.rho_solid_um_per_ms
                compact["decay"]["estimate_formula"] = "1/T2 = 1/T2_bulk + rho_solid * S/V (2D S/V measured on the confirmed phase image)"
        if context.spectrum_path is not None:
            for item in stage_results:
                if item.summary.get("summary_csv"):
                    compact["inversion_summary_csv"] = item.summary.get("summary_csv")
        return AgentToolResult(
            "success" if status == "success" else "failed",
            message,
            artifacts=[artifact for item in stage_results for artifact in item.artifacts],
            summary=compact,
            error=error,
        )

    # 1. Geometry --------------------------------------------------------
    try:
        array, _meta = ct.load_label_image(Path(state["image_path"]))
        assignment = state["assignment"]
        labels_full = ct.apply_phase_assignment(array, assignment)
        labels, bbox = ct.crop_to_sample(labels_full) if state.get("has_background") else (labels_full, [0, array.shape[0] - 1, 0, array.shape[1] - 1])
        geometry_dir = run_dir / "00_geometry"
        stem = Path(state["image_path"]).stem
        full_png = ct.save_internal_label_png(labels_full, geometry_dir / sim.timestamped_name(f"{stem}__confirmed_phases", "png"))
        cropped_png = ct.save_internal_label_png(labels, geometry_dir / sim.timestamped_name(f"{stem}__cropped_simulation_phases", "png"))
        np.save(geometry_dir / "simulation_labels.npy", labels)
        mapping_json = ct.write_json(
            geometry_dir / sim.timestamped_name(f"{stem}__phase_mapping", "json"),
            {
                "source_image": state["image_path"],
                "assignment": assignment,
                "ai_assignment": state.get("ai_assignment"),
                "user_corrections": state.get("user_corrections"),
                "has_background": state.get("has_background"),
                "has_background_source": state.get("has_background_source"),
                "crop_bbox_rows_cols": bbox,
                "internal_labels": {phase: int(label) for phase, label in ct.PHASE_TO_LABEL.items()},
                "confirmed_at": state.get("confirmed_at"),
            },
        )
        counts = {phase: int(np.count_nonzero(labels == label)) for phase, label in ct.PHASE_TO_LABEL.items()}
        material = max(1, counts["water"] + counts["solid"] + counts["air"])
        geometry_summary = {
            "stage": "ct_geometry",
            "cropped_shape": [int(labels.shape[0]), int(labels.shape[1])],
            "crop_bbox_rows_cols": bbox,
            "phase_pixel_counts": counts,
            "porosity_2d": (counts["water"] + counts["air"]) / material,
            "water_saturation_2d": counts["water"] / max(1, counts["water"] + counts["air"]),
            "pixel_size_um": config.pixel_size_um,
            "physical_size_um": [labels.shape[1] * config.pixel_size_um, labels.shape[0] * config.pixel_size_um],
            "labels_npy": str(geometry_dir / "simulation_labels.npy"),
            "simulation_stages": {"geometry": [str(full_png), str(cropped_png)]},
        }
        message = (
            f"Confirmed phases applied; sample cropped to {labels.shape[1]} x {labels.shape[0]} px "
            f"({labels.shape[1] * config.pixel_size_um:.0f} x {labels.shape[0] * config.pixel_size_um:.0f} um). "
            f"2D porosity {geometry_summary['porosity_2d']:.1%}, water saturation {geometry_summary['water_saturation_2d']:.1%}."
            if english
            else f"已应用确认后的相态；样品区域 {labels.shape[1]} x {labels.shape[0]} 像素"
            f"（{labels.shape[1] * config.pixel_size_um:.0f} x {labels.shape[0] * config.pixel_size_um:.0f} μm）。"
            f"二维孔隙度 {geometry_summary['porosity_2d']:.1%}，含水饱和度 {geometry_summary['water_saturation_2d']:.1%}。"
        )
        stage_results.append(
            _emit(context, AgentToolResult("success", message, artifacts=[str(full_png), str(cropped_png), str(mapping_json)], summary=geometry_summary), on_stage)
        )
    except Exception as exc:
        stage_results.append(_emit(context, AgentToolResult("failed", "CT geometry preparation failed." if english else "CT 几何准备失败。", summary={"stage": "ct_geometry"}, error=str(exc)), on_stage))
        return finish("failed", stage_results[-1].message, str(exc))

    # 2. Mesh ------------------------------------------------------------
    try:
        labels_sim, scale = sim.downsample_nearest(labels, config.max_grid_size)
        params, estimate = ct.simulation_params_for(config, labels_sim, scale)
        mesh_dir = run_dir / "01_mesh"
        classifier = partial(ct.ct_edge_classifier, relaxing_edges=config.relaxing_edges)
        mesh, stiffness, mass, solid_robin, gas_robin, mesh_stats = sim.assemble_triangular_operator(labels_sim, params, classifier)
        mesh_png = ct.save_ct_mesh_plot(mesh, mesh_dir / sim.timestamped_name(f"{stem}_ct_triangular_mesh", "png"))
        mesh_bms = mesh_dir / sim.timestamped_name(f"{stem}_ct_triangular_mesh", "bms")
        sim.save_pygimli_mesh(mesh, mesh_bms)
        quality = sim.triangle_quality_table(mesh)
        quality_csv = mesh_dir / sim.timestamped_name(f"{stem}_mesh_quality", "csv")
        quality.to_csv(quality_csv, index=False)
        quality_png = mesh_dir / sim.timestamped_name(f"{stem}_mesh_quality_histogram", "png")
        sim.save_mesh_quality_histogram(quality, quality_png)
        mesh_stats.update(sim.summarize_mesh_quality(mesh, quality))
        mesh_summary = {
            "stage": "ct_mesh",
            "mesher": "pyGIMLi meshtools / Triangle",
            "downsample_scale": float(scale),
            "simulation_pixel_size_um": float(params.pixel_size_x_um),
            **mesh_stats,
            "simulation_stages": {"mesh": [str(mesh_png), str(mesh_bms), str(quality_csv), str(quality_png)]},
        }
        warn = ""
        if mesh_stats.get("min_element_quality", 1.0) < 0.2:
            warn = " Some elements are thin (min quality < 0.2); check the quality histogram." if english else " 存在细长单元（最小质量 < 0.2），请查看质量直方图。"
        message = (
            f"PyGIMLi mesh generated: {mesh_stats['mesh_nodes']} nodes, {mesh_stats['mesh_triangles']} triangles, mean quality {mesh_stats['mean_element_quality']:.2f}.{warn}"
            if english
            else f"PyGIMLi 网格完成：{mesh_stats['mesh_nodes']} 个节点、{mesh_stats['mesh_triangles']} 个三角形，平均单元质量 {mesh_stats['mean_element_quality']:.2f}。{warn}"
        )
        stage_results.append(_emit(context, AgentToolResult("success", message, artifacts=[str(mesh_png), str(mesh_bms), str(quality_csv), str(quality_png)], summary=mesh_summary), on_stage))
    except Exception as exc:
        hint = (
            "Meshing failed. Typical causes: features smaller than the mesh size, too many nodes (increase mesh size), or pyGIMLi missing from the environment."
            if english
            else "网格划分失败。常见原因：特征尺寸小于网格尺寸、节点数超限（可增大网格尺寸），或环境中缺少 pyGIMLi。"
        )
        stage_results.append(_emit(context, AgentToolResult("failed", hint, summary={"stage": "ct_mesh"}, error=str(exc)), on_stage))
        return finish("failed", hint, str(exc))

    # 3. Decay -----------------------------------------------------------
    try:
        decay_dir = run_dir / "02_decay"
        times, amplitude = sim.time_step_triangular_decay(stiffness, mass, solid_robin, gas_robin, params)
        normalized = amplitude / max(float(amplitude[0]), 1e-30)
        curve_csv = decay_dir / sim.timestamped_name(f"{stem}_nmr_decay", "csv")
        curve_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"time_ms": times, "signal": amplitude, "normalized_signal": normalized}).to_csv(curve_csv, index=False)
        curve_png = decay_dir / sim.timestamped_name(f"{stem}_nmr_decay", "png")
        sim.save_decay_plot(times, normalized, curve_png, title=f"{stem} simulated T2 decay")
        # Inversion uses M(t)/M(0): the raw magnetisation integral scales with the
        # water area (~1e6 um^2) and would otherwise skew the L-curve norms.
        decay_xlsx = sim.write_standard_decay_workbook(decay_dir / sim.timestamped_name(f"{stem}__standard_decay", "xlsx"), times, normalized)
        context.simulation_decay_path = Path(decay_xlsx)
        context.repaired_path = Path(decay_xlsx)
        decay_summary = {
            "stage": "ct_decay",
            "solver": "implicit Euler FEM Bloch-Torrey (Robin surface relaxation)",
            "params_used": {key: getattr(params, key) for key in ("pixel_size_x_um", "diffusion_um2_per_ms", "bulk_t2_ms", "rho_solid_um_per_ms", "rho_gas_um_per_ms", "dt_ms", "t_max_ms", "mesh_bulk_size_um", "mesh_boundary_size_um")},
            "estimated_t2_ms": estimate["estimated_t2_ms"],
            "surface_to_volume_per_um": estimate["surface_to_volume_per_um"],
            "dt_ms": params.dt_ms,
            "t_max_ms": params.t_max_ms,
            "time_point_count": int(times.size),
            "final_normalized_signal": float(normalized[-1]),
            "standard_decay_xlsx": str(decay_xlsx),
            "simulation_stages": {"decay": [str(curve_png), str(curve_csv), str(decay_xlsx)]},
        }
        warn = ""
        if normalized[-1] > 0.2:
            warn = (
                f" The signal only decayed to {normalized[-1]:.2f}; long T2 components may be poorly resolved — consider a larger t_max."
                if english
                else f" 信号在模拟结束时仍有 {normalized[-1]:.2f}，长 T2 组分可能分辨不足，可考虑增大最大模拟时间。"
            )
        message = (
            f"Decay solved over {params.t_max_ms:g} ms (dt {params.dt_ms:g} ms); fast-diffusion estimate T2 ≈ {estimate['estimated_t2_ms']:.0f} ms.{warn}"
            if english
            else f"衰减求解完成：模拟 {params.t_max_ms:g} ms（步长 {params.dt_ms:g} ms）；快扩散估计 T2 ≈ {estimate['estimated_t2_ms']:.0f} ms。{warn}"
        )
        stage_results.append(_emit(context, AgentToolResult("success", message, artifacts=[str(curve_png), str(curve_csv), str(decay_xlsx)], summary=decay_summary), on_stage))
    except Exception as exc:
        message = "Decay solve failed." if english else "衰减求解失败。"
        stage_results.append(_emit(context, AgentToolResult("failed", message, summary={"stage": "ct_decay"}, error=str(exc)), on_stage))
        return finish("failed", message, str(exc))

    # 4. T2 inversion ----------------------------------------------------
    inversion_dir = run_dir / "03_t2_inversion"
    if config.run_lcurve:
        inversion = run_lcurve(
            context.repaired_path,
            inversion_dir / "lcurve",
            {
                "time_to_ms_scale": 1.0,
                "num_bins": config.num_bins,
                "t2_min_ms": float(config.t2_min_ms or 1e-2),
                "t2_max_ms": float(config.t2_max_ms or 1e5),
                # the curvature (reference) route uses the alpha grid of the image-slice reference
                "alpha_min": 1e-5 if config.lcurve_criterion == "curvature" else 1e-6,
                "alpha_max": 1e2,
                "alpha_count": 36 if config.lcurve_criterion == "curvature" else 60,
                "trim_from_peak": True,
                "criterion": config.lcurve_criterion,
            },
            language=language,
        )
    else:
        inversion = run_fixed_nnls(
            context.repaired_path,
            inversion_dir / "nnls",
            {
                "time_to_ms_scale": 1.0,
                "regularization": config.regularization,
                "num_bins": config.num_bins,
                "t2_min_ms": float(config.t2_min_ms or 1.0),
                "t2_max_ms": float(config.t2_max_ms or 1e4),
                "trim_from_peak": True,
            },
            language=language,
        )
    inversion.summary = dict(inversion.summary) | {
        "stage": "ct_t2_inversion",
        "inversion_mode": "lcurve" if config.run_lcurve else "fixed_nnls",
        "simulation_decay_xlsx": str(context.repaired_path),
        "simulation_stages": {"inversion": list(inversion.artifacts)},
    }
    stage_results.append(_emit(context, inversion, on_stage))
    if inversion.status == "success" and inversion.summary.get("spectrum_xlsx"):
        context.spectrum_path = Path(str(inversion.summary["spectrum_xlsx"]))
    else:
        return finish("failed", inversion.message, inversion.error)

    # 5. Gaussian --------------------------------------------------------
    if config.run_gaussian:
        gaussian = run_gaussian_peaks(context.spectrum_path, run_dir / "04_gaussian", {"peak_count": config.peak_count}, language=language)
        gaussian.summary = dict(gaussian.summary) | {"stage": "ct_gaussian", "simulation_stages": {"gaussian": list(gaussian.artifacts)}}
        stage_results.append(_emit(context, gaussian, on_stage))

    # 6. Interpretation --------------------------------------------------
    interpretation = interpret_results(stage_results, run_dir / "05_interpretation", language=language)
    interpretation.summary = dict(interpretation.summary) | {"stage": "ct_interpretation", "simulation_stages": {"report": list(interpretation.artifacts)}}
    stage_results.append(_emit(context, interpretation, on_stage))

    failed = [item for item in stage_results if item.status != "success"]
    message = (
        "CT segmented-image NMR workflow completed: geometry, PyGIMLi mesh, decay, T2 inversion"
        + (", Gaussian decomposition" if config.run_gaussian else "")
        + " and interpretation."
        if english
        else "CT 分割图 NMR 流程完成：几何、PyGIMLi 网格、衰减、T2 反演"
        + ("、高斯分峰" if config.run_gaussian else "")
        + "和结果解释。"
    )
    if failed:
        message += (" Some later stages failed: " if english else " 部分后续步骤失败：") + ", ".join(str(item.summary.get("stage")) for item in failed)
    return finish("success", message)
