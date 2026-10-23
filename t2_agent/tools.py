"""Whitelisted local tools for the Streamlit T2 agent."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .models import AgentToolResult


REPO_ROOT = Path(__file__).resolve().parents[1]
T2PROCESS_ROOT = REPO_ROOT / "T2process"
if str(T2PROCESS_ROOT) not in sys.path:
    sys.path.insert(0, str(T2PROCESS_ROOT))

from nmr_t2.config import GaussianConfig, LCurveConfig, NnlsConfig, PlotConfig  # noqa: E402
from nmr_t2.io_utils import cell_to_float, parse_time_cell, read_source_table, safe_token, timestamped_name  # noqa: E402


def _is_english(language: str) -> bool:
    return language.lower().startswith("english")


def _load_simulation_2d():
    try:
        return importlib.import_module("t2_agent.simulation_2d")
    except ModuleNotFoundError as exc:
        missing = exc.name or "a required simulation dependency"
        raise RuntimeError(
            "The 2D NMR simulation workflow is unavailable because "
            f"`{missing}` is not installed. Install the full conda/Docker "
            "environment to run meshing and simulation; T2 inversion workflows "
            "can still run without this optional simulation stack."
        ) from exc


def _load_t2_pipelines():
    try:
        return importlib.import_module("nmr_t2.pipelines")
    except ModuleNotFoundError as exc:
        missing = exc.name or "a required T2 processing dependency"
        raise RuntimeError(
            "The T2 processing workflow is unavailable because "
            f"`{missing}` is not installed. Install the full application "
            "environment before running inversion, plotting, or Gaussian decomposition."
        ) from exc


def run_gaussian_decomposition_on_spectrum_workbook(*args, **kwargs):
    return _load_t2_pipelines().run_gaussian_decomposition_on_spectrum_workbook(*args, **kwargs)


def run_lcurve_workbook(*args, **kwargs):
    return _load_t2_pipelines().run_lcurve_workbook(*args, **kwargs)


def run_nnls_workbook(*args, **kwargs):
    return _load_t2_pipelines().run_nnls_workbook(*args, **kwargs)


def run_plotting_workbook_pair(*args, **kwargs):
    return _load_t2_pipelines().run_plotting_workbook_pair(*args, **kwargs)


def inspect_png_phase_map(*args, **kwargs):
    return _load_simulation_2d().inspect_png_phase_map(*args, **kwargs)


def normalize_png_phase_colors(*args, **kwargs):
    return _load_simulation_2d().normalize_png_phase_colors(*args, **kwargs)


def run_png_mesh_decay(*args, **kwargs):
    return _load_simulation_2d().run_png_mesh_decay(*args, **kwargs)


def run_rule_geometry_mesh_decay(*args, **kwargs):
    return _load_simulation_2d().run_rule_geometry_mesh_decay(*args, **kwargs)


def run_reduced_t2_t2_from_spectrum_workbook(*args, **kwargs):
    return _load_simulation_2d().run_reduced_t2_t2_from_spectrum_workbook(*args, **kwargs)


def write_standard_decay_workbook(path: Path, time_ms: np.ndarray, signal: np.ndarray) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(
        {
            "time_ms": np.asarray(time_ms, dtype=float),
            "signal": np.asarray(signal, dtype=float),
        }
    )
    frame.to_excel(output_path, index=False)
    return output_path


def _trapezoid_area(y: np.ndarray, x: np.ndarray) -> float:
    y_arr = np.asarray(y, dtype=float).ravel()
    x_arr = np.asarray(x, dtype=float).ravel()
    if y_arr.size < 2 or x_arr.size < 2:
        return 0.0
    return float(np.sum((y_arr[1:] + y_arr[:-1]) * 0.5 * np.diff(x_arr)))


def _read_first_table(path: Path) -> pd.DataFrame | None:
    try:
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path)
        if path.suffix.lower() in {".xlsx", ".xls"}:
            return pd.read_excel(path)
    except Exception:
        return None
    return None


def _find_artifact(results: list[AgentToolResult], contains: str, suffixes: tuple[str, ...]) -> Path | None:
    for result in results:
        for artifact in result.artifacts:
            path = Path(artifact)
            if contains in path.name and path.suffix.lower() in suffixes and path.exists():
                return path
    return None


def _find_artifacts(results: list[AgentToolResult], contains: str, suffixes: tuple[str, ...]) -> list[Path]:
    matches: list[Path] = []
    seen: set[tuple[Path, str]] = set()
    for result in results:
        for artifact in result.artifacts:
            path = Path(artifact)
            if contains not in path.name or path.suffix.lower() not in suffixes or not path.exists():
                continue
            dedupe_key = (path.resolve().parent, path.stem)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            matches.append(path)
    return matches


def _summary_path_candidates(results: list[AgentToolResult], keys: tuple[str, ...], suffixes: tuple[str, ...]) -> list[Path]:
    matches: list[Path] = []
    seen: set[str] = set()

    def visit(value: Any, key: str | None = None) -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                visit(child_value, str(child_key))
            return
        if isinstance(value, (list, tuple)):
            for child_value in value:
                visit(child_value, key)
            return
        if key not in keys or value is None:
            return
        path = Path(str(value))
        if path.suffix.lower() not in suffixes or not path.exists() or not path.is_file():
            return
        resolved = str(path.resolve())
        if resolved in seen:
            return
        seen.add(resolved)
        matches.append(path)

    for result in results:
        if result.summary:
            visit(result.summary)
    return matches


def _dedupe_run_artifact_paths(paths: list[Path]) -> list[Path]:
    deduped: list[Path] = []
    seen: set[tuple[Path, str]] = set()
    for path in paths:
        key = (path.resolve().parent, path.stem)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(path)
    return deduped


def _safe_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except Exception:
        return None
    return parsed if np.isfinite(parsed) else None


def _param_token(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    try:
        number = float(value)
    except Exception:
        return safe_token(str(value))
    if not np.isfinite(number):
        return safe_token(str(value))
    return safe_token(f"{number:.6g}".replace("-", "m").replace("+", "p"))


def _regularization_filename_token(value: float) -> str:
    text = f"{float(value):.6g}".replace("-", "m").replace("+", "p").replace(".", "p")
    return safe_token(f"alpha_{text}")


def _selected_alpha_filename_token_from_summary(summary_path: Path | str | None) -> str | None:
    if summary_path is None:
        return None
    path = Path(summary_path)
    if not path.exists():
        return None
    try:
        table = pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_excel(path)
    except Exception:
        return None

    column = "best_regularization" if "best_regularization" in table.columns else "regularization"
    if column not in table.columns:
        return None
    values = [float(value) for value in pd.to_numeric(table[column], errors="coerce").dropna()]
    if not values:
        return None
    if len(values) == 1 or np.allclose(values, values[0], rtol=1e-9, atol=1e-12):
        return _regularization_filename_token(values[0])
    return safe_token(
        f"{_regularization_filename_token(min(values))}_to_"
        f"{_regularization_filename_token(max(values)).removeprefix('alpha_')}"
    )


def _alpha_filename_token_from_path(path: Path | str) -> str | None:
    for part in Path(path).stem.split("__"):
        if part.startswith("alpha_"):
            return safe_token(part)
    return None


def _inversion_run_output_dir(output_dir: Path, method: str, params: dict[str, Any]) -> Path:
    output_path = Path(output_dir)
    if method == "lcurve":
        digest_source = repr(
            [
                ("num_bins", params.get("num_bins", 200)),
                ("t2_min_ms", params.get("t2_min_ms", 1e-2)),
                ("t2_max_ms", params.get("t2_max_ms", 1e5)),
                ("alpha_min", params.get("alpha_min", 1e-3)),
                ("alpha_max", params.get("alpha_max", 1e4)),
                ("alpha_count", params.get("alpha_count", 300)),
                ("trim_from_peak", params.get("trim_from_peak", True)),
            ]
        ).encode("utf-8")
        digest = hashlib.sha1(digest_source).hexdigest()[:8]
        run_folder = "__".join(
            [
                f"bins_{_param_token(params.get('num_bins', 200))}",
                f"alpha_n_{_param_token(params.get('alpha_count', 300))}",
                f"p_{digest}",
            ]
        )
    elif method == "nnls":
        run_folder = "__".join(
            [
                f"reg_{_param_token(params.get('regularization', 1.0))}",
                f"bins_{_param_token(params.get('num_bins', 200))}",
                f"t2_{_param_token(params.get('t2_min_ms', 1.0))}_{_param_token(params.get('t2_max_ms', 1e4))}",
                f"trim_{_param_token(params.get('trim_from_peak', True))}",
            ]
        )
    else:
        run_folder = safe_token(method)
    return output_path if output_path.name == run_folder else output_path / run_folder


def _infer_peak_count_from_gaussian_summary_path(path: Path) -> int | None:
    for part in reversed(path.parts):
        if part.startswith("peaks_"):
            value = part.removeprefix("peaks_")
            if value.isdigit():
                return int(value)
    return None


def _gaussian_run_output_dir(output_dir: Path, peak_count: int) -> Path:
    output_path = Path(output_dir)
    run_folder = f"peaks_{int(peak_count)}"
    return output_path if output_path.name == run_folder else output_path / run_folder


def _plot_run_output_dir(output_dir: Path, spectrum_workbook: Path) -> Path:
    source_folder = safe_token(Path(spectrum_workbook).parent.name)
    output_path = Path(output_dir)
    return output_path if output_path.name == source_folder else output_path / source_folder


def _simulation_params_from_args(args: dict[str, Any]) -> Simulation2DParams:
    Simulation2DParams = _load_simulation_2d().Simulation2DParams
    max_grid_size = args.get("max_grid_size", 500)
    return Simulation2DParams(
        pixel_size_x_um=float(args.get("pixel_size_x_um", args.get("pixel_size_um", 1.0))),
        pixel_size_y_um=float(args.get("pixel_size_y_um", args.get("pixel_size_um", 1.0))),
        diffusion_um2_per_ms=float(args.get("diffusion_um2_per_ms", 2.0)),
        bulk_t2_ms=float(args.get("bulk_t2_ms", 3000.0)),
        rho_solid_um_per_ms=float(args.get("rho_solid_um_per_ms", 0.005)),
        rho_gas_um_per_ms=float(args.get("rho_gas_um_per_ms", 0.0)),
        dt_ms=float(args.get("dt_ms", 5.0)),
        t_max_ms=float(args.get("t_max_ms", 1500.0)),
        max_grid_size=None if max_grid_size in {"none", "None", None} else int(max_grid_size),
        solver="triangular",
        mesh_bulk_size_um=float(args.get("mesh_bulk_size_um", 8.0)),
        mesh_boundary_size_um=float(args.get("mesh_boundary_size_um", 2.0)),
        mesh_max_points=int(args.get("mesh_max_points", 25000)),
    )


def _positive_arg(args: dict[str, Any], key: str) -> bool:
    if key not in args or args.get(key) is None:
        return False
    try:
        return float(args[key]) > 0.0
    except Exception:
        return False


def png_physical_scale_provided(args: dict[str, Any]) -> bool:
    """Return whether a PNG simulation has an explicit physical scale."""

    return (
        _positive_arg(args, "pixel_size_um")
        or (_positive_arg(args, "pixel_size_x_um") and _positive_arg(args, "pixel_size_y_um"))
        or (_positive_arg(args, "physical_size_x_um") and _positive_arg(args, "physical_size_y_um"))
    )


def png_physical_scale_error(language: str = "中文") -> AgentToolResult:
    message = (
        "PNG phase-map simulation needs the sample scale before meshing. Please provide the cropped sample width and height, for example `300 x 300 um`. I can still use default inversion settings after that."
        if _is_english(language)
        else "PNG 相图模拟在网格划分前需要样品尺寸。请补充裁剪后样品区域的宽和高，例如 `300 x 300 μm`。反演参数可以继续用默认值，不需要额外补充。"
    )
    return AgentToolResult(
        "failed",
        message,
        summary={"stage": "geometry", "required_fields": ["physical_size_x_um", "physical_size_y_um"]},
        error="missing_png_physical_scale",
    )


def _rule_geometry_from_args(args: dict[str, Any]) -> RuleGeometry2D:
    RuleGeometry2D = _load_simulation_2d().RuleGeometry2D
    return RuleGeometry2D(
        coupled=bool(args.get("coupled", True)),
        canvas_width_px=int(args.get("canvas_width_px", 160)),
        canvas_height_px=int(args.get("canvas_height_px", 100)),
        large_pore_radius_px=int(args.get("large_pore_radius_px", 24)),
        small_pore_radius_px=int(args.get("small_pore_radius_px", 16)),
        throat_length_px=int(args.get("throat_length_px", 30)),
        throat_width_px=int(args.get("throat_width_px", 8)),
        large_side_um=float(args.get("large_side_um", 20.0)),
        small_side_um=float(args.get("small_side_um", 8.0)),
        large_depth_um=float(args.get("large_depth_um", 20.0)),
        small_depth_um=float(args.get("small_depth_um", 8.0)),
        throat_length_um=float(args.get("throat_length_um", 5.0)),
        throat_width_um=float(args.get("throat_width_um", 1.0)),
        large_air_area_um2=float(args.get("large_air_area_um2", 0.0)),
        small_air_area_um2=float(args.get("small_air_area_um2", 0.0)),
        ideal_mesh_area_um2=float(args.get("ideal_mesh_area_um2", 0.05)),
        ideal_mesh_quality=float(args.get("ideal_mesh_quality", 34.0)),
    )


def _simulation_artifacts_from_summary(summary: dict[str, Any]) -> list[str]:
    artifacts: list[str] = []
    for key, value in summary.items():
        if key.endswith(("_png", "_csv", "_xlsx", "_bms", "_json")) and value:
            artifacts.append(str(value))
    return artifacts


def run_local_nmr_triangle_t2_t2(output_dir: Path, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the repository-bundled ideal-triangle NMR demo.

    The public app must not depend on a separately cloned NMR project or Git
    submodule. This wrapper intentionally delegates to the built-in 2D
    simulation workflow so missing external directories never become a public
    deployment failure.
    """

    params = params or {}
    output_path = Path(output_dir)
    builtin_output = output_path / "builtin_ideal_triangle"
    builtin_summary = run_rule_geometry_mesh_decay(
        _rule_geometry_from_args(params),
        builtin_output,
        _simulation_params_from_args(params),
    )
    artifacts = _simulation_artifacts_from_summary(builtin_summary)
    stages = dict(builtin_summary.get("simulation_stages", {}))
    return {
        **builtin_summary,
        "status": "success",
        "stage": "builtin_ideal_triangle_t2_workflow",
        "model_dimension": "2D",
        "geometry_source": "builtin_ideal_triangle",
        "local_nmr_available": True,
        "external_nmr_project_required": False,
        "message": "Using the repository-bundled ideal-triangle 2D T2 workflow; no external NMR subproject is required.",
        "standard_decay_source_csv": builtin_summary.get("curve_csv"),
        "manifest_json": builtin_summary.get("summary_json"),
        "pygimli_mesh_bms": builtin_summary.get("pygimli_mesh_bms"),
        "t2_t2_png": None,
        "t2_t2_signal_csv": None,
        "t2_t2_map_csv": None,
        "simulation_stages": stages,
        "artifacts": artifacts,
    }


def inspect_2d_geometry_input(
    input_path: Path | None,
    output_dir: Path,
    params: dict[str, Any] | None = None,
    language: str = "中文",
) -> AgentToolResult:
    params = params or {}
    mode = str(params.get("geometry_mode", "png")).lower()
    try:
        if mode == "rule":
            geometry = _rule_geometry_from_args(params)
            return AgentToolResult(
                "success",
                "理想三角孔模拟参数已读取。未上传 PNG 时会直接使用 pyGIMLi 构建三角孔网格。"
                if not _is_english(language)
                else "Ideal triangular-pore simulation parameters were read. Without a PNG upload, pyGIMLi will build the triangular-pore mesh directly.",
                summary={
                    "stage": "geometry",
                    "geometry_mode": "rule",
                    "geometry_source": "builtin_ideal_triangle",
                    "rule_geometry": geometry.__dict__,
                },
            )
        if input_path is None:
            return AgentToolResult(
                "failed",
                "请先上传 PNG 相图。" if not _is_english(language) else "Please upload a PNG phase map first.",
                error="missing_upload",
            )
        original_input = Path(input_path)
        inspect_input = original_input
        normalization_summary: dict[str, Any] | None = None
        if bool(params.get("normalize_phase_colors", False)):
            normalization_summary = normalize_png_phase_colors(original_input, Path(output_dir) / "geometry")
            inspect_input = Path(normalization_summary["normalized_png"])
        inspection = inspect_png_phase_map(inspect_input, Path(output_dir) / "geometry")
        artifacts = [str(path) for path in (inspection.cropped_png, inspection.preview_png) if path.exists()]
        if normalization_summary is not None:
            artifacts.insert(0, normalization_summary["normalized_png"])
        summary = inspection.summary() | {
            "stage": "geometry",
            "geometry_mode": "png",
            "original_input_path": str(original_input.resolve()),
            "simulation_input_path": str(inspect_input.resolve()),
            "simulation_stages": {"geometry": artifacts},
        }
        if normalization_summary is not None:
            summary["normalization"] = normalization_summary
            summary["normalized_png"] = normalization_summary["normalized_png"]
        return AgentToolResult(
            "success" if inspection.status == "success" else "failed",
            inspection.message,
            artifacts=artifacts,
            summary=summary,
            error=inspection.error,
        )
    except Exception as exc:
        return AgentToolResult(
            "failed",
            "二维几何输入检查失败。" if not _is_english(language) else "2D geometry inspection failed.",
            error=str(exc),
        )


def run_2d_mesh_and_decay(
    input_path: Path | None,
    output_dir: Path,
    params: dict[str, Any] | None = None,
    language: str = "中文",
) -> AgentToolResult:
    params = params or {}
    mode = str(params.get("geometry_mode", "png")).lower()
    try:
        sim_params = _simulation_params_from_args(params)
        if mode == "rule":
            result = run_rule_geometry_mesh_decay(_rule_geometry_from_args(params), Path(output_dir), sim_params)
        else:
            if input_path is None:
                return AgentToolResult(
                    "failed",
                    "请先上传 PNG 相图。" if not _is_english(language) else "Please upload a PNG phase map first.",
                    error="missing_upload",
                )
            if not png_physical_scale_provided(params):
                return png_physical_scale_error(language)
            result = run_png_mesh_decay(
                Path(input_path),
                Path(output_dir),
                sim_params,
                normalize_phase_colors=bool(params.get("normalize_phase_colors", False)),
                physical_size_x_um=(
                    float(params["physical_size_x_um"]) if params.get("physical_size_x_um") is not None else None
                ),
                physical_size_y_um=(
                    float(params["physical_size_y_um"]) if params.get("physical_size_y_um") is not None else None
                ),
            )
        artifacts = _simulation_artifacts_from_summary(result)
        status = "success" if result.get("status") == "success" else "failed"
        if status == "success":
            message = (
                "2D 网格划分和 NMR 衰减求解完成。"
                if not _is_english(language)
                else "2D mesh generation and NMR decay solve completed."
            )
        else:
            message = (
                "2D 网格划分或衰减求解失败。"
                if not _is_english(language)
                else "2D mesh generation or decay solve failed."
            )
        return AgentToolResult(status, message, artifacts=artifacts, summary=result, error=result.get("error"))
    except Exception as exc:
        return AgentToolResult(
            "failed",
            "2D 网格划分或衰减求解失败。" if not _is_english(language) else "2D mesh generation or decay solve failed.",
            error=str(exc),
        )


def run_reduced_t2_t2(
    spectrum_workbook: Path | None,
    output_dir: Path,
    params: dict[str, Any] | None = None,
    language: str = "中文",
) -> AgentToolResult:
    params = params or {}
    if spectrum_workbook is None:
        return AgentToolResult(
            "failed",
            "需要先生成 T2 谱，才能计算 T2-T2 图。"
            if not _is_english(language)
            else "A T2 spectrum must exist before computing a T2-T2 map.",
            error="missing_spectrum",
        )
    try:
        result = run_reduced_t2_t2_from_spectrum_workbook(
            Path(spectrum_workbook),
            Path(output_dir),
            alpha=float(params.get("t2_t2_alpha", params.get("alpha", 0.05))),
            t1_points=int(params.get("t2_t2_t1_points", 18)),
            t2_points=int(params.get("t2_t2_t2_points", 24)),
            bin_points=int(params.get("t2_t2_bin_points", 28)),
        )
        artifacts = _simulation_artifacts_from_summary(result)
        return AgentToolResult(
            "success",
            "T2-T2 简化交换图已生成。"
            if not _is_english(language)
            else "Reduced T2-T2 exchange map generated.",
            artifacts=artifacts,
            summary=result,
        )
    except Exception as exc:
        return AgentToolResult(
            "failed",
            "T2-T2 简化交换图生成失败。"
            if not _is_english(language)
            else "Reduced T2-T2 exchange-map generation failed.",
            error=str(exc),
        )


def _literature_section(
    results: list[AgentToolResult],
    summary: dict[str, Any],
    t2: np.ndarray,
    amp: np.ndarray,
    gaussian_runs: list[dict[str, Any]],
    language: str,
    sample_context: str = "",
) -> tuple[list[str], list[str]]:
    """Collect the numbers of this analysis and write the literature-based section."""

    from .literature import (
        AnalysisFacts,
        build_findings,
        early_time_misfit,
        echo_timing,
        gaussian_fit_r2,
        render_section,
        spectrum_peaks,
        wall_coverage_from_labels,
    )

    stages = [str(item.summary.get("stage", "")) for item in results]
    workflow = "ideal" if any(stage.startswith("ideal_") for stage in stages) else "ct" if any(stage.startswith("ct_") for stage in stages) else "measured"
    facts = AnalysisFacts(workflow=workflow, t2_ms=t2, spectrum=amp, sample_context=sample_context or "")
    facts.main_peak_ms = summary.get("main_peak_t2_ms")
    facts.short_fraction = summary.get("short_t2_fraction_lt_10ms")
    facts.long_fraction = summary.get("long_t2_fraction_ge_1000ms")
    facts.peak_positions_ms = spectrum_peaks(t2, amp)
    for item in reversed(results):
        params = item.summary.get("parameters") if isinstance(item.summary.get("parameters"), dict) else None
        if item.summary.get("metrics_xlsx") or (params and "alpha_count" in params):
            facts.inversion_mode = "lcurve"
            facts.selection_rule = (params or {}).get("criterion", "ratio")
            break
        if item.summary.get("regularization") is not None and item.summary.get("spectrum_xlsx"):
            facts.inversion_mode = "fixed_nnls"
            facts.alpha = float(item.summary["regularization"])
            break
    if facts.inversion_mode == "lcurve":
        facts.alpha = summary.get("best_regularization")
    trimmed = next((item.summary.get("trimmed_xlsx") for item in reversed(results) if item.summary.get("trimmed_xlsx")), None)
    if trimmed and Path(str(trimmed)).exists() and workflow == "measured":
        facts.early_misfit_fraction, facts.decay_end_fraction = early_time_misfit(Path(str(trimmed)))
        facts.first_echo_ms, facts.echo_spacing_ms = echo_timing(Path(str(trimmed)))
    if gaussian_runs:
        facts.gaussian_peaks = [peak for peak in gaussian_runs[-1]["peaks"] if peak.get("position_ms") is not None]
        fit_xlsx = gaussian_runs[-1].get("fit_file")
        if fit_xlsx and Path(fit_xlsx).exists():
            facts.gaussian_r2 = gaussian_fit_r2(Path(fit_xlsx))
    for item in results:
        if item.summary.get("stage") == "ideal_geometry" and item.summary.get("ideal_config"):
            facts.ideal = {
                "config": item.summary["ideal_config"],
                "estimated_t2_ms": item.summary.get("estimated_t2_ms", {}),
                "water_configuration": item.summary.get("water_configuration", {}),
            }
            facts.bulk_t2_ms = float(item.summary["ideal_config"].get("bulk_t2_ms", 3000.0))
        if item.summary.get("stage") == "ct_geometry":
            facts.ct = (facts.ct or {}) | {
                "water_saturation_2d": item.summary.get("water_saturation_2d"),
                "porosity_2d": item.summary.get("porosity_2d"),
                "pixel_size_um": item.summary.get("pixel_size_um"),
            }
            labels_npy = item.summary.get("labels_npy")
            if labels_npy and Path(str(labels_npy)).exists():
                labels = np.load(str(labels_npy))
                facts.ct["labels"] = labels
                facts.ct["wall_coverage"] = wall_coverage_from_labels(labels)
        if item.summary.get("stage") == "ct_mesh" and item.summary.get("solid_liquid_boundary_length_um") is not None:
            mesh = item.summary
            relaxing = float(mesh["solid_liquid_boundary_length_um"]) + float(mesh.get("relaxing_edge_length_um") or 0.0)
            facts.ct = (facts.ct or {}) | {"relaxing_boundary_um": relaxing}
        if item.summary.get("stage") == "ct_decay":
            used = item.summary.get("params_used") or {}
            facts.bulk_t2_ms = used.get("bulk_t2_ms")
            facts.rho_um_per_ms = used.get("rho_solid_um_per_ms")
            facts.diffusion_um2_per_ms = used.get("diffusion_um2_per_ms")
            facts.decay_end_fraction = item.summary.get("final_normalized_signal")
            facts.ct = (facts.ct or {}) | {"pixel_surface_to_volume_per_um": item.summary.get("surface_to_volume_per_um")}
            # The unnormalised magnetisation at t = 0 is the meshed water area (M0 = 1 per unit area).
            curve_csv = next((path for path in (item.summary.get("simulation_stages") or {}).get("decay", []) if str(path).endswith(".csv")), None)
            if curve_csv and Path(str(curve_csv)).exists():
                first = pd.read_csv(str(curve_csv), nrows=1)
                if "signal" in first:
                    facts.ct["water_area_um2"] = float(first["signal"].iloc[0])
    facts.pore_diameter_um = summary.get("local_pore_diameter_um")
    return render_section(build_findings(facts, language), language)


def _add_simulation_report_figure(
    results: list[AgentToolResult],
    output_dir: Path,
    lines: list[str],
    summary: dict[str, Any],
    gaussian_runs: list[dict[str, Any]],
    english: bool,
) -> str | None:
    """Five-panel figure for CT or ideal-structure runs: phases, water domain, pore sizes, decay, T2."""

    stage = {str(item.summary.get("stage")): item.summary for item in results}
    geometry = stage.get("ct_geometry") or stage.get("ideal_geometry")
    inversion = stage.get("ct_t2_inversion") or stage.get("ideal_t2_inversion")
    if not geometry or not inversion or not inversion.get("spectrum_xlsx"):
        return None
    gaussian = stage.get("ct_gaussian") or stage.get("ideal_gaussian") or {}
    try:
        from . import simulation_figure as sf

        decay = inversion.get("simulation_decay_xlsx")
        series = sf.load_inversion_series(
            Path(str(decay)),
            Path(str(inversion["spectrum_xlsx"])),
            Path(str(inversion["fit_xlsx"])) if inversion.get("fit_xlsx") else None,
            Path(str(inversion["summary_csv"])) if inversion.get("summary_csv") else None,
            Path(str(gaussian["fit_xlsx"])) if gaussian.get("fit_xlsx") else None,
        )
        series["inversion_label"] = "L-curve" if inversion.get("inversion_mode", "lcurve") == "lcurve" else "Fixed NNLS"
        if gaussian_runs:
            series["gaussian_positions_ms"] = [float(peak["position_ms"]) for peak in gaussian_runs[-1]["peaks"] if peak.get("position_ms") is not None]
        if "ct_geometry" in stage:
            mesh_files = [Path(path) for path in (stage.get("ct_mesh") or {}).get("simulation_stages", {}).get("mesh", []) if str(path).endswith(".bms")]
            data = sf.ct_figure_data(Path(str(geometry["labels_npy"])), float(geometry["pixel_size_um"]), series, mesh_files[0] if mesh_files else None)
        else:
            data = sf.ideal_figure_data(geometry["ideal_config"], series, geometry.get("estimated_t2_ms", {}))
        figure_path = sf.save_simulation_figure(data, Path(output_dir) / timestamped_name("simulation_report", "png"))
    except Exception as exc:  # the figure must never block the written interpretation
        summary["simulation_report_figure_error"] = str(exc)
        return None
    summary["simulation_report_figure"] = str(figure_path)
    if data.pore_diameter_um is not None and data.pore_diameter_um.size:
        summary["local_pore_diameter_um"] = {
            "pore_space_median": float(np.median(data.pore_diameter_um)),
            "water_domain_median": float(np.median(data.water_diameter_um)) if data.water_diameter_um is not None and data.water_diameter_um.size else None,
        }
    lines.append("## Simulation Overview Figure" if english else "## 模拟总览图")
    lines.append(f"![{'Simulation overview' if english else '模拟总览'}]({figure_path.name})")
    lines.append(
        "Top: three-phase map, water-filled domain used by the forward model, and area-weighted local pore diameter (largest inscribed disk) of the pore space and the water domain. "
        "Bottom: simulated echo envelope with the spectral reconstruction, and the peak-normalized T2 spectrum; the T2 axis shows the non-zero part of the inversion grid plus one decade."
        if english
        else "上排：三相分布、正演使用的含水域，以及孔隙空间与含水域的局部孔径分布（最大内切圆直径，按面积加权）。"
        "下排：模拟回波包络与谱重建，以及按峰值归一化的 T2 谱；T2 轴显示反演网格中幅值非零的范围并向两侧各延伸一个十进位。"
    )
    lines.append("")
    return str(figure_path)


def _lcurve_report_inputs(results: list[AgentToolResult]) -> dict[str, Path] | None:
    """Return the four L-curve workbooks of the latest L-curve run, if all exist."""

    keys = ("spectrum_xlsx", "metrics_xlsx", "trimmed_xlsx", "fit_xlsx")
    for result in reversed(results):
        summary = result.summary or {}
        if all(key in summary for key in keys):
            paths = {key: Path(str(summary[key])) for key in keys}
            if all(path.exists() for path in paths.values()):
                return paths
    return None


def _add_inversion_report_figure(
    results: list[AgentToolResult], output_dir: Path, lines: list[str], summary: dict[str, Any], english: bool
) -> str | None:
    """Draw the four-panel inversion figure and reference it in the report lines."""

    inputs = _lcurve_report_inputs(results)
    if inputs is None:
        return None
    try:
        from nmr_t2.report_figure import plot_inversion_report

        figure_path = plot_inversion_report(
            inputs["spectrum_xlsx"],
            inputs["metrics_xlsx"],
            inputs["trimmed_xlsx"],
            inputs["fit_xlsx"],
            Path(output_dir) / timestamped_name("inversion_report", "png"),
        )
    except Exception as exc:  # the figure must never block the written interpretation
        summary["inversion_report_figure_error"] = str(exc)
        return None
    summary["inversion_report_figure"] = str(figure_path)
    lines.append("## Inversion Overview Figure" if english else "## 反演总览图")
    lines.append(f"![{'Inversion overview' if english else '反演总览'}]({figure_path.name})")
    lines.append(
        "Measured and fitted decay with residuals (left); recovered T2 spectrum and L-curve with the selected smoothing factor (right)."
        if english
        else "左：实测与拟合衰减及残差；右：反演得到的 T2 谱，以及 L-curve 和选定的平滑因子。"
    )
    lines.append("")
    return str(figure_path)


def interpret_results(results: list[AgentToolResult], output_dir: Path, language: str = "中文", sample_context: str = "") -> AgentToolResult:
    """Summarize generated T2 artifacts into a user-facing interpretation.

    ``sample_context`` is the user's description of the sample (for example "biomass-containing soil");
    it selects material-specific literature rules such as the soil water-state classes.
    """

    try:
        english = _is_english(language)
        lines = ["# T2 Result Interpretation" if english else "# T2 结果解释", ""]
        summary: dict[str, Any] = {}

        summary_candidates = _summary_path_candidates(
            results,
            ("summary_csv", "summary_xlsx", "lcurve_summary_csv", "lcurve_summary_xlsx", "nnls_summary_csv", "nnls_summary_xlsx"),
            (".csv", ".xlsx"),
        )
        # Gaussian summaries inherit "lcurve" from the spectrum file name; they are not inversion runs.
        lcurve_summary_paths = _dedupe_run_artifact_paths([
            *_find_artifacts(results, "lcurve_summary", (".csv", ".xlsx")),
            *[path for path in summary_candidates if "lcurve" in path.name.lower() and "gaussian" not in path.name.lower()],
        ])
        nnls_summary_paths = _dedupe_run_artifact_paths([
            *_find_artifacts(results, "nnls_summary", (".csv", ".xlsx")),
            *[path for path in summary_candidates if "nnls" in path.name.lower()],
        ])
        if not lcurve_summary_paths and not nnls_summary_paths:
            lcurve_summary_paths = _dedupe_run_artifact_paths(
                [path for path in summary_candidates if _read_first_table(path) is not None]
            )
        lcurve_summary_path = lcurve_summary_paths[0] if lcurve_summary_paths else None
        nnls_summary_path = nnls_summary_paths[0] if nnls_summary_paths else None
        spectrum_candidates = _summary_path_candidates(
            results,
            ("spectrum_xlsx", "spectrum_workbook", "lcurve_spectrum_xlsx", "nnls_spectrum_xlsx"),
            (".xlsx", ".xls"),
        )
        lcurve_spectrum_path = _find_artifact(results, "lcurve_spectrum", (".xlsx", ".xls")) or next(
            (path for path in spectrum_candidates if "lcurve" in path.name.lower()),
            None,
        )
        nnls_spectrum_path = _find_artifact(results, "nnls_spectrum", (".xlsx", ".xls")) or next(
            (path for path in spectrum_candidates if "nnls" in path.name.lower()),
            None,
        )
        if lcurve_spectrum_path is None and nnls_spectrum_path is None and spectrum_candidates:
            lcurve_spectrum_path = spectrum_candidates[0]
        # Long run folders shorten file names to "..._gaussian_sum__..."; match both forms.
        gaussian_summary_paths = _find_artifacts(results, "gaussian_sum", (".csv", ".xlsx"))

        inversion_summary_path = lcurve_summary_path or nnls_summary_path
        spectrum_path = lcurve_spectrum_path or nnls_spectrum_path

        if inversion_summary_path:
            inversion_summary = _read_first_table(inversion_summary_path)
            if inversion_summary is not None and not inversion_summary.empty:
                row = inversion_summary.iloc[0].to_dict()
                best_regularization = _safe_float(row.get("best_regularization", row.get("regularization")))
                residual_norm = _safe_float(row.get("best_residual_norm", row.get("residual_norm")))
                roughness_norm = _safe_float(row.get("best_roughness_norm", row.get("roughness_norm")))
                summary.update(
                    {
                        "inversion_summary_file": str(inversion_summary_path),
                        "best_regularization": best_regularization,
                        "residual_norm": residual_norm,
                        "roughness_norm": roughness_norm,
                    }
                )
                lines.append("## Inversion Quality and Smoothing Factor" if english else "## 反演质量与平滑因子")
                if best_regularization is not None:
                    if english:
                        lines.append(f"- The best smoothing factor is about `{best_regularization:.4g}`. This is the L-curve compromise between fitting error and spectrum smoothness.")
                    else:
                        lines.append(f"- 最佳平滑因子约为 `{best_regularization:.4g}`。它是 L-curve 在拟合误差和谱线平滑之间选出的折中值。")
                if residual_norm is not None:
                    if english:
                        lines.append(f"- The residual norm is about `{residual_norm:.4g}`. Smaller values mean the fit is closer to the data, but this alone does not prove the result is best.")
                    else:
                        lines.append(f"- 残差范数约为 `{residual_norm:.4g}`，数值越小说明拟合越贴近数据，但不能单独用它判断结果是否最好。")
                if roughness_norm is not None:
                    if english:
                        lines.append(f"- The roughness norm is about `{roughness_norm:.4g}`. It measures how strongly the T2 spectrum fluctuates.")
                    else:
                        lines.append(f"- 粗糙度范数约为 `{roughness_norm:.4g}`，用于衡量 T2 谱是否过度起伏。")
                lines.append("")

        inversion_run_rows = []
        for method, summary_paths in (("L-curve", lcurve_summary_paths), ("Fixed NNLS", nnls_summary_paths)):
            for summary_path in summary_paths:
                table = _read_first_table(summary_path)
                if table is None or table.empty:
                    continue
                row = table.iloc[0].to_dict()
                inversion_run_rows.append(
                    {
                        "method": method,
                        "summary_file": str(summary_path),
                        "run_folder": summary_path.parent.name,
                        "regularization": _safe_float(row.get("best_regularization", row.get("regularization"))),
                        "residual_norm": _safe_float(row.get("best_residual_norm", row.get("residual_norm"))),
                        "roughness_norm": _safe_float(row.get("best_roughness_norm", row.get("roughness_norm"))),
                    }
                )
        if len(inversion_run_rows) > 1:
            summary["inversion_runs"] = inversion_run_rows
            lines.append("## Parameter Run Comparison" if english else "## 不同反演参数结果对比")
            for row in inversion_run_rows:
                if english:
                    lines.append(
                        f"- {row['method']} `{row['run_folder']}`: regularization `{row['regularization']:.4g}`"
                        if row["regularization"] is not None
                        else f"- {row['method']} `{row['run_folder']}`"
                    )
                else:
                    lines.append(
                        f"- {row['method']} `{row['run_folder']}`：平滑因子 `{row['regularization']:.4g}`"
                        if row["regularization"] is not None
                        else f"- {row['method']} `{row['run_folder']}`"
                    )
                if row["residual_norm"] is not None and row["roughness_norm"] is not None:
                    if english:
                        lines.append(f"  Residual norm `{row['residual_norm']:.4g}`, roughness norm `{row['roughness_norm']:.4g}`.")
                    else:
                        lines.append(f"  残差范数 `{row['residual_norm']:.4g}`，粗糙度范数 `{row['roughness_norm']:.4g}`。")
            lines.append("")

        spectrum_t2 = spectrum_amp = None
        if spectrum_path:
            sheets = pd.read_excel(spectrum_path, sheet_name=None)
            first_sheet_name, spectrum_df = next(iter(sheets.items()))
            t2_col = "t2_ms" if "t2_ms" in spectrum_df.columns else spectrum_df.columns[0]
            amp_col = "amplitude" if "amplitude" in spectrum_df.columns else spectrum_df.columns[1]
            t2 = pd.to_numeric(spectrum_df[t2_col], errors="coerce").to_numpy(dtype=float)
            amp = pd.to_numeric(spectrum_df[amp_col], errors="coerce").to_numpy(dtype=float)
            mask = np.isfinite(t2) & np.isfinite(amp) & (t2 > 0)
            t2 = t2[mask]
            amp = amp[mask]
            spectrum_t2, spectrum_amp = t2, amp
            if t2.size and amp.size:
                from .literature import class_fractions

                max_idx = int(np.argmax(amp))
                # Bin sums on the logarithmic grid, so the three classes add up to 100%.
                short_fraction, mid_fraction, long_fraction = class_fractions(t2, amp, (10.0, 1000.0))
                summary.update(
                    {
                        "spectrum_file": str(spectrum_path),
                        "signal_name": first_sheet_name,
                        "main_peak_t2_ms": float(t2[max_idx]),
                        "main_peak_amplitude": float(amp[max_idx]),
                        "short_t2_fraction_lt_10ms": short_fraction,
                        "middle_t2_fraction_10_1000ms": mid_fraction,
                        "long_t2_fraction_ge_1000ms": long_fraction,
                    }
                )
                lines.append("## T2 Spectrum Interpretation" if english else "## T2 谱解释")
                if english:
                    lines.append(f"- The main peak is around `{float(t2[max_idx]):.4g} ms`, which is the strongest T2 component in the current spectrum.")
                    lines.append(f"- Area below 10 ms, 10-1000 ms and above 1000 ms: `{short_fraction:.1%}`, `{mid_fraction:.1%}`, `{long_fraction:.1%}`. These fixed bounds are an empirical division (short T2: bound fluid or strong surface relaxation; long T2: freer fluid); the material-specific classes, where they apply, are in the literature section below.")
                else:
                    lines.append(f"- 主峰位置约在 `{float(t2[max_idx]):.4g} ms`，这是当前谱中幅值最高的 T2 组分。")
                    lines.append(f"- <10 ms、10–1000 ms、≥1000 ms 的面积占比分别约为 `{short_fraction:.1%}`、`{mid_fraction:.1%}`、`{long_fraction:.1%}`。这三个固定区间是经验划分（短 T2 偏束缚流体或强表面弛豫，长 T2 偏自由流体），边界随材料而变；适用时，按材料的分类见下方文献依据部分。")
                lines.append("")

        gaussian_runs = []
        for gaussian_summary_path in gaussian_summary_paths:
            gaussian_summary = _read_first_table(gaussian_summary_path)
            if gaussian_summary is None or gaussian_summary.empty:
                continue
            peak_rows = []
            for _, row in gaussian_summary.iterrows():
                peak_rows.append(
                    {
                        "peak_id": int(row.get("peak_id", len(peak_rows) + 1)),
                        "signal_name": str(row.get("signal_name", "")),
                        "position_ms": _safe_float(row.get("position_ms")),
                        "width_log10": _safe_float(row.get("width_log10")),
                        "area_fraction": _safe_float(row.get("area_fraction")),
                    }
                )
            peak_count = _infer_peak_count_from_gaussian_summary_path(gaussian_summary_path) or len({row["peak_id"] for row in peak_rows})
            stamp = gaussian_summary_path.stem.split("__")[-1]
            fit_file = next(iter(sorted(gaussian_summary_path.parent.glob(f"*gaussian_f*{stamp}.xlsx"))), None)
            gaussian_runs.append(
                {
                    "summary_file": str(gaussian_summary_path),
                    "fit_file": str(fit_file) if fit_file else None,
                    "peak_count": peak_count,
                    "peaks": peak_rows,
                }
            )

        if gaussian_runs:
            lines.append("## Gaussian Peak Interpretation" if english else "## Gaussian 分峰解释")
            summary["gaussian_runs"] = gaussian_runs
            if len(gaussian_runs) == 1:
                summary["gaussian_peaks"] = gaussian_runs[0]["peaks"]
            for run in gaussian_runs:
                peak_count = run["peak_count"]
                if len(gaussian_runs) > 1:
                    if english:
                        lines.append(f"### {peak_count}-Peak Fit")
                    else:
                        lines.append(f"### {peak_count} 峰拟合")
                for peak in run["peaks"]:
                    position = peak["position_ms"]
                    fraction = peak["area_fraction"]
                    if position is not None and fraction is not None:
                        if english:
                            lines.append(f"- Peak {peak['peak_id']}: position about `{position:.4g} ms`, area fraction about `{fraction:.1%}`.")
                        else:
                            lines.append(f"- 峰 {peak['peak_id']}：位置约 `{position:.4g} ms`，面积占比约 `{fraction:.1%}`。")
                lines.append("")

        # Simulated runs get the five-panel simulation figure; measured data the inversion overview.
        report_figure = _add_simulation_report_figure(results, output_dir, lines, summary, gaussian_runs, english)
        if report_figure is None:
            report_figure = _add_inversion_report_figure(results, output_dir, lines, summary, english)

        if spectrum_t2 is not None:
            try:
                literature_lines, cited = _literature_section(results, summary, spectrum_t2, spectrum_amp, gaussian_runs, language, sample_context)
                lines.extend(literature_lines)
                summary["literature_citations"] = cited
                # Structured copies so the model can quote them without the truncated message.
                summary["literature_findings"] = [line[2:] for line in literature_lines if line.startswith("- ")]
                from .literature import load_references

                summary["literature_references"] = [load_references()[key]["reference_agu"] for key in cited]
            except Exception as exc:  # citations must never block the interpretation
                summary["literature_error"] = str(exc)

        if len(lines) <= 2:
            message = "There are not enough inversion results to interpret yet. Run L-curve or NNLS first." if english else "还没有足够的反演结果可解释。请先运行 L-curve 或 NNLS。"
            return AgentToolResult("failed", message, error="missing_result_artifacts")

        output_path = Path(output_dir) / timestamped_name("interpretation", "md")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")

        message = "\n".join(line for line in lines if line != "")[:3000]
        artifacts = [str(output_path)] + ([report_figure] if report_figure else [])
        return AgentToolResult("success", message, artifacts=artifacts, summary=summary)
    except Exception as exc:
        message = "Result interpretation failed." if _is_english(language) else "结果解释失败。"
        return AgentToolResult("failed", message, error=str(exc))


def _profile_columns(table: pd.DataFrame) -> list[dict[str, Any]]:
    layout_candidates: list[dict[str, Any]] = []
    for col_idx in range(table.shape[1]):
        label = _column_label(table, col_idx)
        numeric = _numeric_column(table, col_idx)
        finite = numeric[np.isfinite(numeric)]
        positive = finite[finite > 0]
        layout_candidates.append(
            {
                "excel_index": int(col_idx + 1),
                "label": label,
                "finite_numeric_count": int(finite.size),
                "positive_numeric_count": int(positive.size),
                "min": float(np.min(finite)) if finite.size else None,
                "max": float(np.max(finite)) if finite.size else None,
                "first_numeric_values": [float(value) for value in finite[:5]],
                "monotonic_increasing_score": _monotonic_increasing_score(numeric),
            }
        )
    return layout_candidates


def inspect_workbook_schema(input_workbook: Path, preview_rows: int = 8, language: str = "中文") -> AgentToolResult:
    """Return uploaded table preview and column profiles for AI reasoning."""

    try:
        english = _is_english(language)
        input_path = Path(input_workbook)
        if not input_path.exists():
            message = f"Uploaded file not found: {input_path}" if english else f"找不到上传文件：{input_path}"
            return AgentToolResult("failed", message, error="file_not_found")

        workbook = pd.ExcelFile(input_path) if input_path.suffix.lower() in {".xlsx", ".xls"} else None
        sheet_name = workbook.sheet_names[0] if workbook else input_path.name
        table = read_source_table(input_path)
        preview = table.head(int(preview_rows)).where(pd.notnull(table.head(int(preview_rows))), None).values.tolist()
        profiles = _profile_columns(table)
        preliminary_data_kind = "unknown"
        try:
            layout = _infer_layout(table)
            times, signals = _parsed_rows_by_layout(table, layout)
            preliminary_data_kind = _infer_data_kind(
                input_path,
                table,
                layout=layout,
                time_values=np.asarray(times, dtype=float),
                signal_matrix=np.asarray(signals, dtype=float),
            )
        except Exception:
            preliminary_data_kind = "unknown"
        if english:
            message = (
                f"Workbook structure loaded. The first sheet is {sheet_name}, with {table.shape[0]} rows x {table.shape[1]} columns. "
                f"Preliminary data kind: {preliminary_data_kind}. I will identify the time or T2-axis column and signal-amplitude columns from labels, monotonicity, numeric ranges, preview rows, and curve shape."
            )
        else:
            kind_label = {"decay": "原始衰减数据", "spectrum": "T2 谱表"}.get(preliminary_data_kind, "暂不确定")
            message = (
                f"已读取工作簿结构。第一个 sheet 为 {sheet_name}，形状为 {table.shape[0]} 行 x {table.shape[1]} 列。"
                f"初步判断为：{kind_label}。我会根据列名、单调性、数值范围、预览行和曲线形态综合判断。"
            )
        return AgentToolResult(
            "success",
            message,
            summary={
                "sheet_names": workbook.sheet_names if workbook else [input_path.name],
                "active_sheet": sheet_name,
                "shape": [int(table.shape[0]), int(table.shape[1])],
                "preliminary_data_kind": preliminary_data_kind,
                "preview_rows": preview,
                "column_profiles": profiles,
            },
        )
    except Exception as exc:
        message = "Workbook structure inspection failed." if _is_english(language) else "工作簿结构检查失败。"
        return AgentToolResult("failed", message, error=str(exc))


def _as_artifacts(paths: dict[str, Path] | list[Path]) -> list[str]:
    if isinstance(paths, dict):
        values = list(paths.values())
    else:
        values = paths

    artifacts: list[str] = []
    for value in values:
        path = Path(value)
        if path.is_dir():
            artifacts.extend(str(item) for item in sorted(path.glob("*")) if item.is_file())
        else:
            artifacts.append(str(path))
    return artifacts


def _summary_column_artifacts(summary_path: Path | str | None, column_name: str) -> list[str]:
    if summary_path is None:
        return []

    path = Path(summary_path)
    if not path.exists():
        return []

    try:
        if path.suffix.lower() == ".csv":
            table = pd.read_csv(path)
        else:
            table = pd.read_excel(path)
    except Exception:
        return []

    if column_name not in table.columns:
        return []

    artifacts: list[str] = []
    seen: set[str] = set()
    for value in table[column_name].dropna():
        artifact = Path(str(value))
        if not artifact.exists() or not artifact.is_file():
            continue
        resolved = str(artifact.resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        artifacts.append(str(artifact))
    return artifacts


def _add_pair_plot_artifacts(
    *,
    raw_decay_workbook: Path,
    spectrum_workbook: Path | None,
    output_dir: Path,
    artifacts: list[str],
    summary: dict[str, Any],
    filename_tag: str | None = None,
) -> None:
    """Append decay + T2 spectrum figures without failing the inversion result."""

    if spectrum_workbook is None:
        return

    try:
        paired = run_plotting_workbook_pair(
            Path(raw_decay_workbook),
            Path(spectrum_workbook),
            Path(output_dir) / "paired_plots",
            plot_config=PlotConfig(),
            time_to_ms_scale=1.0,
            filename_tag=filename_tag,
        )
    except Exception as exc:
        summary["paired_plot_warning"] = str(exc)
        return

    pair_artifacts = _as_artifacts(list(paired.values()))
    artifacts.extend(pair_artifacts)
    summary["paired_plot_count"] = len(pair_artifacts)


def _read_raw_table(input_workbook: Path) -> pd.DataFrame:
    return read_source_table(input_workbook)


def _column_label(table: pd.DataFrame, column_idx: int) -> str:
    if table.empty:
        return f"col_{column_idx + 1}"
    first = table.iat[0, column_idx]
    if isinstance(first, str) and cell_to_float(first) != cell_to_float(first):
        return first.strip() or f"col_{column_idx + 1}"
    return f"col_{column_idx + 1}"


def _numeric_column(table: pd.DataFrame, column_idx: int) -> np.ndarray:
    return np.asarray([cell_to_float(value) for value in table.iloc[:, column_idx]], dtype=float)


def _monotonic_increasing_score(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    if finite.size < 3:
        return 0.0
    diffs = np.diff(finite)
    return float(np.sum(diffs > 0) / diffs.size)


def _signal_column_shape(
    time_values: np.ndarray,
    signal_values: np.ndarray,
) -> dict[str, Any]:
    """Score whether one numeric column behaves like a T2 signal amplitude."""

    t = np.asarray(time_values, dtype=float)
    y = np.asarray(signal_values, dtype=float)
    mask = np.isfinite(t) & np.isfinite(y) & (t > 0)
    t = t[mask]
    y = y[mask]

    if t.size < 3:
        return {
            "valid_pair_count": int(t.size),
            "positive_fraction": 0.0,
            "decay_like_score": 0.0,
            "spectrum_like_score": 0.0,
            "residual_like": False,
            "keep": False,
        }

    order = np.argsort(t)
    y = y[order]
    diffs = np.diff(y)
    positive_fraction = float(np.sum(y > 0) / y.size)
    negative_fraction = float(np.sum(y < 0) / y.size)
    decreasing_score = float(np.sum(diffs < 0) / diffs.size) if diffs.size else 0.0
    sign_crossings = int(np.sum(np.signbit(y[1:]) != np.signbit(y[:-1]))) if y.size > 1 else 0

    y_min = float(np.min(y))
    y_max = float(np.max(y))
    y_range = y_max - y_min
    abs_peak = float(np.max(np.abs(y)))
    median_abs = float(np.median(np.abs(y)))
    median_y = float(np.median(y))
    max_idx = int(np.argmax(y))
    n = int(y.size)
    edge_count = max(3, n // 10)
    head = y[:edge_count]
    tail = y[-edge_count:]
    head_median = float(np.median(head))
    tail_median = float(np.median(tail))
    head_median_abs = float(np.median(np.abs(head)))
    tail_median_abs = float(np.median(np.abs(tail)))
    head_positive_fraction = float(np.sum(head > 0) / head.size) if head.size else 0.0
    envelope_abs_ratio = head_median_abs / max(tail_median_abs, max(abs_peak, 1.0) * 1e-9)
    decaying_positive_envelope = bool(
        head_positive_fraction >= 0.80
        and head_median > 0
        and envelope_abs_ratio >= 3.0
        and (head_median - tail_median) >= max(tail_median_abs * 3.0, max(abs_peak, 1.0) * 0.03)
    )

    if not np.isfinite(y_range) or y_range <= max(abs_peak, 1.0) * 1e-9:
        y_range = 0.0

    end_drop_fraction = ((float(y[max_idx]) - float(np.median(tail))) / y_range) if y_range > 0 else 0.0
    near_start_peak = max_idx <= max(2, int(0.08 * n))
    decay_like_score = 0.0
    if near_start_peak:
        decay_like_score += 0.45
    decay_like_score += max(0.0, min(1.0, (decreasing_score - 0.45) / 0.35)) * 0.35
    decay_like_score += max(0.0, min(1.0, end_drop_fraction / 0.25)) * 0.20

    spectrum_like_score = 0.0
    if max(2, int(0.05 * n)) <= max_idx <= min(n - 3, int(0.95 * n)):
        before = np.diff(y[: max_idx + 1])
        after = np.diff(y[max_idx:])
        before_increasing = float(np.sum(before > 0) / before.size) if before.size else 0.0
        after_decreasing = float(np.sum(after < 0) / after.size) if after.size else 0.0
        edge_level = max(float(np.median(head)), float(np.median(tail)))
        prominence_fraction = ((float(y[max_idx]) - edge_level) / y_range) if y_range > 0 else 0.0
        spectrum_like_score = (
            max(0.0, min(1.0, (before_increasing - 0.45) / 0.35)) * 0.35
            + max(0.0, min(1.0, (after_decreasing - 0.45) / 0.35)) * 0.35
            + max(0.0, min(1.0, prominence_fraction / 0.18)) * 0.30
        )

    balanced_signs = 0.25 <= positive_fraction <= 0.75 and negative_fraction >= 0.20
    small_center = abs(median_y) <= max(abs_peak, 1.0) * 0.20
    frequent_crossings = sign_crossings >= max(3, int(0.08 * n))
    residual_like = bool(balanced_signs and small_center and frequent_crossings and not decaying_positive_envelope)

    mostly_positive = positive_fraction >= 0.80 and median_y > 0
    clearly_shaped = decay_like_score >= 0.55 or spectrum_like_score >= 0.55
    keep = bool((decaying_positive_envelope or mostly_positive or clearly_shaped) and not residual_like)

    return {
        "valid_pair_count": int(t.size),
        "positive_fraction": positive_fraction,
        "decreasing_score": decreasing_score,
        "decay_like_score": float(decay_like_score),
        "spectrum_like_score": float(spectrum_like_score),
        "sign_crossings": sign_crossings,
        "median_abs": median_abs,
        "decaying_positive_envelope": decaying_positive_envelope,
        "envelope_abs_ratio": float(envelope_abs_ratio),
        "residual_like": residual_like,
        "keep": keep,
    }


def _infer_layout(table: pd.DataFrame) -> dict[str, Any]:
    """Infer time/T2 column and signal columns from headers plus numeric shape."""

    candidates: list[dict[str, Any]] = []
    for col_idx in range(table.shape[1]):
        label = _column_label(table, col_idx)
        label_key = label.lower()
        numeric = _numeric_column(table, col_idx)
        finite = numeric[np.isfinite(numeric)]
        positive_count = int(np.sum(finite > 0))
        finite_count = int(finite.size)
        increasing = _monotonic_increasing_score(numeric)

        time_score = finite_count * 0.01 + increasing * 50.0
        if any(token in label_key for token in ("time", "t2", "时间")):
            time_score += 120.0
        if any(token in label_key for token in ("peak", "amplitude", "signal", "幅", "峰")):
            time_score -= 80.0
        if positive_count < 2:
            time_score -= 100.0

        candidates.append(
            {
                "index": col_idx,
                "label": label,
                "numeric": numeric,
                "finite_count": finite_count,
                "positive_count": positive_count,
                "increasing_score": increasing,
                "time_score": time_score,
            }
        )

    if not candidates:
        raise ValueError("Workbook has no columns.")

    time_candidate = max(candidates, key=lambda item: item["time_score"])
    if time_candidate["positive_count"] < 2:
        raise ValueError("No valid time/T2 column was detected.")

    signal_candidates = [
        item
        for item in candidates
        if item["index"] != time_candidate["index"] and item["finite_count"] > 0
    ]
    scored_signal_candidates: list[dict[str, Any]] = []
    ignored_signal_candidates: list[dict[str, Any]] = []
    for item in signal_candidates:
        shape = _signal_column_shape(time_candidate["numeric"], item["numeric"])
        enriched = item | {"signal_shape": shape}
        if shape["keep"]:
            scored_signal_candidates.append(enriched)
        else:
            ignored_signal_candidates.append(enriched)

    if not scored_signal_candidates:
        raise ValueError("No valid signal columns were detected.")

    return {
        "time_column": time_candidate,
        "signal_columns": scored_signal_candidates,
        "ignored_signal_columns": ignored_signal_candidates,
        "all_columns": candidates,
    }


def _parsed_rows(table: pd.DataFrame) -> tuple[list[float], list[list[float]]]:
    matrix = table.values
    times: list[float] = []
    signals: list[list[float]] = []

    for row_idx in range(matrix.shape[0]):
        ok, time_value = parse_time_cell(matrix[row_idx, 0])
        if not ok:
            continue
        row_signals = [cell_to_float(matrix[row_idx, col_idx]) for col_idx in range(1, matrix.shape[1])]
        times.append(float(time_value))
        signals.append(row_signals)
    return times, signals


def _parsed_rows_by_layout(table: pd.DataFrame, layout: dict[str, Any]) -> tuple[list[float], list[list[float]]]:
    matrix = table.values
    time_col = int(layout["time_column"]["index"])
    signal_cols = [int(item["index"]) for item in layout["signal_columns"]]
    times: list[float] = []
    signals: list[list[float]] = []

    for row_idx in range(matrix.shape[0]):
        ok, time_value = parse_time_cell(matrix[row_idx, time_col])
        if not ok:
            continue
        row_signals = [cell_to_float(matrix[row_idx, col_idx]) for col_idx in signal_cols]
        times.append(float(time_value))
        signals.append(row_signals)
    return times, signals


def _recommend_time_scale(time_values: np.ndarray) -> tuple[float, str]:
    positive = time_values[np.isfinite(time_values) & (time_values > 0)]
    if positive.size == 0:
        return 1.0, "没有足够的正时间点，暂时按 ms 处理。"

    max_time = float(np.max(positive))
    diffs = np.diff(np.sort(positive))
    median_step = float(np.median(diffs[diffs > 0])) if np.any(diffs > 0) else np.nan

    if max_time <= 10 and (not np.isfinite(median_step) or median_step < 0.1):
        return 1000.0, "时间数值整体很小，更像是秒；建议乘以 1000 转成 ms。"
    return 1.0, "时间范围更像已经是 ms；建议保持 1:1。"


def _curve_shape_data_kind(time_values: np.ndarray, signal_matrix: np.ndarray) -> str | None:
    """Classify decay vs spectrum from curve shape when the data are clear."""

    if time_values.size < 8 or signal_matrix.size == 0:
        return None

    finite_column_counts = np.sum(np.isfinite(signal_matrix), axis=0)
    if finite_column_counts.size == 0 or int(np.max(finite_column_counts)) < 8:
        return None

    signal_idx = int(np.argmax(finite_column_counts))
    x = np.asarray(time_values, dtype=float)
    y = np.asarray(signal_matrix[:, signal_idx], dtype=float)
    mask = np.isfinite(x) & np.isfinite(y) & (x > 0)
    x = x[mask]
    y = y[mask]
    if x.size < 8:
        return None

    order = np.argsort(x)
    x = x[order]
    y = y[order]
    diffs = np.diff(y)
    if diffs.size == 0:
        return None

    y_min = float(np.min(y))
    y_max = float(np.max(y))
    y_range = y_max - y_min
    if not np.isfinite(y_range) or y_range <= max(abs(y_max), 1.0) * 1e-9:
        return None

    n = int(y.size)
    max_idx = int(np.argmax(y))
    decreasing_score = float(np.sum(diffs < 0) / diffs.size)
    near_start_peak = max_idx <= max(2, int(0.08 * n))
    end_drop_fraction = (float(y[max_idx]) - float(np.median(y[-max(3, n // 10) :]))) / y_range
    if near_start_peak and decreasing_score >= 0.62 and end_drop_fraction >= 0.25:
        return "decay"

    if max(2, int(0.05 * n)) <= max_idx <= min(n - 3, int(0.95 * n)):
        before = np.diff(y[: max_idx + 1])
        after = np.diff(y[max_idx:])
        before_increasing = float(np.sum(before > 0) / before.size) if before.size else 0.0
        after_decreasing = float(np.sum(after < 0) / after.size) if after.size else 0.0
        edge_level = max(float(np.median(y[: max(3, n // 10)])), float(np.median(y[-max(3, n // 10) :])))
        prominence_fraction = (float(y[max_idx]) - edge_level) / y_range
        if before_increasing >= 0.55 and after_decreasing >= 0.55 and prominence_fraction >= 0.18:
            return "spectrum"

    return None


def _infer_data_kind(
    input_workbook: Path,
    table: pd.DataFrame,
    layout: dict[str, Any] | None = None,
    time_values: np.ndarray | None = None,
    signal_matrix: np.ndarray | None = None,
) -> str:
    first_row_values = [str(value).strip().lower() for value in table.iloc[0].tolist()] if not table.empty else []
    first_row = " ".join(first_row_values)
    name = input_workbook.name.lower()

    if time_values is None or signal_matrix is None:
        try:
            inferred_layout = layout or _infer_layout(table)
            times, signals = _parsed_rows_by_layout(table, inferred_layout)
            time_values = np.asarray(times, dtype=float)
            signal_matrix = np.asarray(signals, dtype=float)
        except Exception:
            time_values = None
            signal_matrix = None

    if time_values is not None and signal_matrix is not None:
        shape_kind = _curve_shape_data_kind(time_values, signal_matrix)
        if shape_kind is not None:
            return shape_kind

    has_t2_axis_label = any(
        token in first_row
        for token in ("t2", "t₂", "relaxation", "弛豫")
    )
    has_spectrum_amplitude_label = any(
        token in first_row
        for token in ("amplitude", "spectrum", "intensity", "distribution", "peak", "谱", "幅", "峰")
    )
    if has_t2_axis_label and has_spectrum_amplitude_label:
        return "spectrum"
    if "spectrum" in name and has_spectrum_amplitude_label:
        return "spectrum"
    return "decay"


def _workbook_data_kind(input_workbook: Path) -> str:
    """Best-effort workbook kind classification for tool-level safety checks."""

    try:
        table = _read_raw_table(Path(input_workbook))
        if table.empty:
            return "unknown"
        return _infer_data_kind(Path(input_workbook), table)
    except Exception:
        return "unknown"


def _spectrum_input_error(language: str) -> AgentToolResult:
    english = _is_english(language)
    message = (
        "This workbook looks like an existing T2 spectrum, not raw decay data. I will not run T2 inversion on it; use Gaussian peak decomposition directly, or confirm if you intended to upload raw decay data."
        if english
        else "这个工作簿看起来是已有 T2 谱表，不是原始衰减数据。我不会把它再做 T2 反演；如果你的目标是分峰，可以直接做 Gaussian 分峰，若本意是上传原始衰减数据，请确认文件。"
    )
    return AgentToolResult("failed", message, error="spectrum_input_not_decay")


def validate_workbook(input_workbook: Path, language: str = "中文") -> AgentToolResult:
    """Inspect an uploaded workbook and recommend safe defaults."""

    try:
        english = _is_english(language)
        input_path = Path(input_workbook)
        if not input_path.exists():
            message = f"Uploaded file not found: {input_path}" if english else f"找不到上传文件：{input_path}"
            return AgentToolResult("failed", message, error="file_not_found")

        table = _read_raw_table(input_path)
        if table.empty or table.shape[1] < 2:
            message = "Excel needs at least two columns: the first for time or T2, followed by signal-amplitude columns." if english else "Excel 至少需要两列：第一列为时间或 T2，后续列为信号幅度。"
            return AgentToolResult(
                "failed",
                message,
                error="not_enough_columns",
            )

        try:
            layout = _infer_layout(table)
        except ValueError as exc:
            error_text = str(exc)
            if "No valid time" in error_text:
                message = "No valid numeric time/T2 column was detected." if english else "没有检测到有效时间/T2 数值列。"
                return AgentToolResult("failed", message, error="no_valid_time")
            if "No valid signal" in error_text:
                message = "No valid signal column was detected. Please confirm the data contains numeric amplitudes." if english else "没有检测到有效信号列。请确认数据中包含数值幅度。"
                return AgentToolResult("failed", message, error="no_valid_signal")
            message = "Excel layout recognition failed." if english else "Excel 数据布局识别失败。"
            return AgentToolResult("failed", message, error=error_text)
        times, signals = _parsed_rows_by_layout(table, layout)
        if not times:
            message = "No valid numeric time/T2 column was detected." if english else "没有检测到有效时间/T2 数值列。"
            return AgentToolResult("failed", message, error="no_valid_time")

        time_values = np.asarray(times, dtype=float)
        signal_matrix = np.asarray(signals, dtype=float)
        finite_signal_mask = np.any(np.isfinite(signal_matrix), axis=0)
        signal_column_count = int(np.sum(finite_signal_mask))
        if signal_column_count == 0:
            message = "No valid signal column was detected. Please confirm the data contains numeric amplitudes." if english else "没有检测到有效信号列。请确认数据中包含数值幅度。"
            return AgentToolResult("failed", message, error="no_valid_signal")

        scale, scale_reason = _recommend_time_scale(time_values)
        if english:
            scale_reason = (
                "The time values are very small and look like seconds; I recommend multiplying by 1000 to convert to ms."
                if scale == 1000.0
                else "The time range looks like it is already in ms; I recommend keeping a 1:1 scale."
            )
        data_kind = _infer_data_kind(input_path, table, layout=layout, time_values=time_values, signal_matrix=signal_matrix)
        invalid_signal_cells = int(np.size(signal_matrix) - np.sum(np.isfinite(signal_matrix)))
        valid_rows = int(np.sum(np.isfinite(time_values) & (time_values > 0)))
        time_column = layout["time_column"]
        signal_columns = layout["signal_columns"]
        ignored_signal_columns = layout.get("ignored_signal_columns", [])
        column_order_issue = "time_not_first_column" if int(time_column["index"]) != 0 else "none"

        summary: dict[str, Any] = {
            "data_kind": data_kind,
            "row_count": int(table.shape[0]),
            "column_count": int(table.shape[1]),
            "valid_time_rows": valid_rows,
            "signal_column_count": signal_column_count,
            "recommended_time_to_ms_scale": float(scale),
            "time_scale_reason": scale_reason,
            "invalid_signal_cells": invalid_signal_cells,
            "time_column_excel_index": int(time_column["index"] + 1),
            "time_column_label": str(time_column["label"]),
            "signal_excel_columns": [int(item["index"] + 1) for item in signal_columns],
            "signal_column_labels": [str(item["label"]) for item in signal_columns],
            "ignored_signal_like_excel_columns": [int(item["index"] + 1) for item in ignored_signal_columns],
            "ignored_signal_like_column_labels": [str(item["label"]) for item in ignored_signal_columns],
            "column_order_issue": column_order_issue,
            "valid_signal_excel_columns": [int(item["index"] + 1) for item in signal_columns],
            "column_profiles": _profile_columns(table),
        }
        order_note = ""
        if column_order_issue != "none":
            if english:
                order_note = (
                    f" Note: the detected time/T2 column is not the first column; it is column {summary['time_column_excel_index']} "
                    f"({summary['time_column_label']}). Columns {summary['signal_excel_columns']} look more like signal amplitudes "
                    f"({', '.join(summary['signal_column_labels'])}). I will reorder the data into time_ms + signal."
                )
            else:
                order_note = (
                    f"注意：我检测到时间/T2 列不是第一列，而是在第 {summary['time_column_excel_index']} 列 "
                    f"({summary['time_column_label']})；第 {summary['signal_excel_columns']} 列更像信号幅值 "
                    f"({', '.join(summary['signal_column_labels'])})。后续会自动重排为 time_ms + signal。"
                )
        kind_note = ""
        if data_kind == "spectrum":
            kind_note = (
                " This looks like an existing T2 spectrum, so inversion should be skipped; Gaussian peak decomposition can run directly if that is your goal."
                if english
                else "这看起来是已有 T2 谱表，应跳过反演；如果目标是分峰，可以直接做 Gaussian 分峰。"
            )
        axis_label = "T2 axis" if data_kind == "spectrum" else "time column"
        axis_label_cn = "T2 轴" if data_kind == "spectrum" else "时间列"
        if english:
            message = (
                f"Excel loaded. Column {summary['time_column_excel_index']} ({summary['time_column_label']}) appears to be the {axis_label}, "
                f"with {valid_rows} valid points. Detected {signal_column_count} valid signal columns: {', '.join(summary['signal_column_labels'])}. "
                f"{scale_reason}{order_note}{kind_note}"
            )
        else:
            message = (
                f"已读取 Excel。检测到第 {summary['time_column_excel_index']} 列 "
                f"({summary['time_column_label']}) 是{axis_label_cn}，共 {valid_rows} 个有效点；"
                f"检测到 {signal_column_count} 个有效信号列：{', '.join(summary['signal_column_labels'])}。"
                f"{scale_reason}{order_note}{kind_note}"
            )
        return AgentToolResult("success", message, summary=summary)
    except Exception as exc:
        message = "Excel data diagnosis failed." if _is_english(language) else "Excel 数据诊断失败。"
        return AgentToolResult("failed", message, error=str(exc))


def repair_workbook(input_workbook: Path, output_dir: Path, time_to_ms_scale: float = 1.0, language: str = "中文") -> AgentToolResult:
    """Write a standardized workbook with `time_ms` plus numeric signal columns."""

    try:
        english = _is_english(language)
        table = _read_raw_table(Path(input_workbook))
        if _infer_data_kind(Path(input_workbook), table) == "spectrum":
            return _spectrum_input_error(language)
        try:
            layout = _infer_layout(table)
        except ValueError as exc:
            error_text = str(exc)
            if "No valid time" in error_text:
                message = "Cannot repair: no valid numeric time/T2 column was detected." if english else "无法修复：没有有效时间/T2 数值列。"
                return AgentToolResult("failed", message, error="no_valid_time")
            if "No valid signal" in error_text:
                message = "Cannot repair: no valid signal column was detected." if english else "无法修复：没有有效信号列。"
                return AgentToolResult("failed", message, error="no_valid_signal")
            message = "Cannot repair: data layout recognition failed." if english else "无法修复：数据布局识别失败。"
            return AgentToolResult("failed", message, error=error_text)
        times, signals = _parsed_rows_by_layout(table, layout)
        if not times:
            message = "Cannot repair: no valid numeric time/T2 column was detected." if english else "无法修复：没有有效时间/T2 数值列。"
            return AgentToolResult("failed", message, error="no_valid_time")

        time_values = np.asarray(times, dtype=float)
        signal_matrix = np.asarray(signals, dtype=float)
        positive_time = np.isfinite(time_values) & (time_values > 0)
        time_values = time_values[positive_time] * float(time_to_ms_scale)
        signal_matrix = signal_matrix[positive_time, :]

        finite_signal_mask = np.any(np.isfinite(signal_matrix), axis=0)
        if not np.any(finite_signal_mask):
            message = "Cannot repair: no valid signal column was detected." if english else "无法修复：没有有效信号列。"
            return AgentToolResult("failed", message, error="no_valid_signal")

        signal_matrix = signal_matrix[:, finite_signal_mask]
        data = {"time_ms": time_values}
        signal_columns = [layout["signal_columns"][idx] for idx, keep in enumerate(finite_signal_mask) if keep]
        for idx, signal_col in enumerate(signal_columns):
            data[str(signal_col["label"])] = signal_matrix[:, idx]

        output_path = Path(output_dir) / timestamped_name(f"{safe_token(Path(input_workbook).stem)}__standardized", "xlsx")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(data).to_excel(output_path, index=False)
        message = "Standardized Excel generated: the first column is time_ms, followed by valid signal columns." if english else "已生成标准化 Excel：第一列为 time_ms，后续列为有效信号。"
        return AgentToolResult(
            "success",
            message,
            artifacts=[str(output_path)],
            summary={
                "standardized_workbook": str(output_path),
                "time_to_ms_scale_applied": float(time_to_ms_scale),
                "signal_column_count": int(signal_matrix.shape[1]),
                "source_time_column_excel_index": int(layout["time_column"]["index"] + 1),
                "source_signal_excel_columns": [int(item["index"] + 1) for item in signal_columns],
                "ignored_signal_like_excel_columns": [
                    int(item["index"] + 1) for item in layout.get("ignored_signal_columns", [])
                ],
            },
        )
    except Exception as exc:
        message = "Excel auto-repair failed." if _is_english(language) else "Excel 自动修复失败。"
        return AgentToolResult("failed", message, error=str(exc))


def run_lcurve(input_workbook: Path, output_dir: Path, params: dict[str, Any] | None = None, language: str = "中文") -> AgentToolResult:
    """Run L-curve inversion and return exported artifacts."""

    params = params or {}
    try:
        english = _is_english(language)
        if _workbook_data_kind(Path(input_workbook)) == "spectrum":
            return _spectrum_input_error(language)
        cfg = LCurveConfig(
            num_bins=int(params.get("num_bins", 200)),
            t2_min_ms=float(params.get("t2_min_ms", 1e-2)),
            t2_max_ms=float(params.get("t2_max_ms", 1e5)),
            alpha_min=float(params.get("alpha_min", 1e-3)),
            alpha_max=float(params.get("alpha_max", 1e4)),
            alpha_count=int(params.get("alpha_count", 300)),
            min_points_after_trim=int(params.get("min_points_after_trim", 10)),
        )
        criterion = str(params.get("criterion", "ratio"))
        if criterion not in ("ratio", "curvature"):
            raise ValueError(f"Unknown L-curve criterion: {criterion}")
        run_output_dir = _inversion_run_output_dir(Path(output_dir), "lcurve", params)
        if criterion == "curvature":
            # Reference route: untrimmed, unweighted normalised decay and maximum L-curve curvature.
            from .reference_inversion import run_reference_lcurve_workbook

            result = run_reference_lcurve_workbook(
                Path(input_workbook),
                run_output_dir,
                {"num_bins": cfg.num_bins, "t2_min_ms": cfg.t2_min_ms, "t2_max_ms": cfg.t2_max_ms,
                 "alpha_min": cfg.alpha_min, "alpha_max": cfg.alpha_max, "alpha_count": cfg.alpha_count},
                time_to_ms_scale=float(params.get("time_to_ms_scale", 1.0)),
            )
        else:
            result = run_lcurve_workbook(
                Path(input_workbook),
                run_output_dir,
                config=cfg,
                plot_config=PlotConfig(),
                time_to_ms_scale=float(params.get("time_to_ms_scale", 1.0)),
                trim_from_peak=bool(params.get("trim_from_peak", True)),
            )
        artifacts = _as_artifacts({key: value for key, value in result.items() if key != "figure_dir"})
        artifacts.extend(_summary_column_artifacts(result.get("summary_csv"), "lcurve_figure"))
        summary = {key: str(value) for key, value in result.items()}
        summary["source_decay_xlsx"] = str(Path(input_workbook))
        if "trimmed_xlsx" in result:
            summary["trimmed_decay_xlsx"] = str(result["trimmed_xlsx"])
        summary["parameters"] = {
            "num_bins": int(cfg.num_bins),
            "t2_min_ms": float(cfg.t2_min_ms),
            "t2_max_ms": float(cfg.t2_max_ms),
            "alpha_min": float(cfg.alpha_min),
            "alpha_max": float(cfg.alpha_max),
            "alpha_count": int(cfg.alpha_count),
            "min_points_after_trim": int(cfg.min_points_after_trim),
            "time_to_ms_scale": float(params.get("time_to_ms_scale", 1.0)),
            "trim_from_peak": bool(params.get("trim_from_peak", True)) and criterion == "ratio",
            "criterion": criterion,
        }
        spectrum_path = Path(result["spectrum_xlsx"]) if "spectrum_xlsx" in result else None
        alpha_token = _selected_alpha_filename_token_from_summary(result.get("summary_csv"))
        _add_pair_plot_artifacts(
            raw_decay_workbook=Path(input_workbook),
            spectrum_workbook=spectrum_path,
            output_dir=run_output_dir,
            artifacts=artifacts,
            summary=summary,
            filename_tag=alpha_token,
        )
        summary["output_dir"] = str(run_output_dir)
        rule = {"ratio": ("slope-reciprocal ratio", "斜率倒数比值"), "curvature": ("maximum curvature", "最大曲率")}[criterion]
        message = (
            f"L-curve inversion completed ({rule[0]} criterion). Outputs are grouped in {run_output_dir.name}."
            if english
            else f"L-curve 反演完成（{rule[1]}判据）。结果已归入 {run_output_dir.name}。"
        )
        return AgentToolResult(
            "success",
            message,
            artifacts=artifacts,
            summary=summary,
        )
    except Exception as exc:
        message = "L-curve inversion failed." if _is_english(language) else "L-curve 反演失败。"
        return AgentToolResult("failed", message, error=str(exc))


def run_fixed_nnls(input_workbook: Path, output_dir: Path, params: dict[str, Any] | None = None, language: str = "中文") -> AgentToolResult:
    """Run fixed-regularization NNLS inversion."""

    params = params or {}
    try:
        english = _is_english(language)
        if _workbook_data_kind(Path(input_workbook)) == "spectrum":
            return _spectrum_input_error(language)
        regularization = float(params.get("regularization", 1.0))
        cfg = NnlsConfig(
            num_bins=int(params.get("num_bins", 200)),
            regularization=regularization,
            t2_min_ms=float(params.get("t2_min_ms", 1.0)),
            t2_max_ms=float(params.get("t2_max_ms", 1e4)),
            min_points_after_trim=int(params.get("min_points_after_trim", 10)),
        )
        run_output_dir = _inversion_run_output_dir(Path(output_dir), "nnls", params)
        result = run_nnls_workbook(
            Path(input_workbook),
            run_output_dir,
            config=cfg,
            time_to_ms_scale=float(params.get("time_to_ms_scale", 1.0)),
            trim_from_peak=bool(params.get("trim_from_peak", True)),
        )
        artifacts = _as_artifacts(result)
        summary = {key: str(value) for key, value in result.items()} | {"regularization": regularization, "output_dir": str(run_output_dir)}
        spectrum_path = Path(result["spectrum_xlsx"]) if "spectrum_xlsx" in result else None
        _add_pair_plot_artifacts(
            raw_decay_workbook=Path(input_workbook),
            spectrum_workbook=spectrum_path,
            output_dir=run_output_dir,
            artifacts=artifacts,
            summary=summary,
            filename_tag=_regularization_filename_token(regularization),
        )
        message = (
            f"Fixed-regularization NNLS inversion completed with smoothing factor {regularization:g}. Outputs are grouped in {run_output_dir.name}."
            if english
            else f"固定 NNLS 反演完成，使用平滑因子 {regularization:g}。结果已归入 {run_output_dir.name}。"
        )
        return AgentToolResult(
            "success",
            message,
            artifacts=artifacts,
            summary=summary,
        )
    except Exception as exc:
        message = "Fixed-regularization NNLS inversion failed." if _is_english(language) else "固定 NNLS 反演失败。"
        return AgentToolResult("failed", message, error=str(exc))


def plot_decay_spectrum(
    raw_decay_workbook: Path,
    spectrum_workbook: Path,
    output_dir: Path,
    params: dict[str, Any] | None = None,
    language: str = "中文",
) -> AgentToolResult:
    """Generate paired decay/T2 spectrum plots."""

    params = params or {}
    try:
        english = _is_english(language)
        run_output_dir = _plot_run_output_dir(Path(output_dir), Path(spectrum_workbook))
        result = run_plotting_workbook_pair(
            Path(raw_decay_workbook),
            Path(spectrum_workbook),
            run_output_dir,
            plot_config=PlotConfig(),
            time_to_ms_scale=float(params.get("time_to_ms_scale", 1.0)),
            filename_tag=_alpha_filename_token_from_path(spectrum_workbook),
        )
        message = (
            f"Paired decay-curve and T2-spectrum figures were generated in {run_output_dir.name}."
            if english
            else f"衰减曲线和 T2 谱配对图已生成，并归入 {run_output_dir.name}。"
        )
        return AgentToolResult(
            "success",
            message,
            artifacts=_as_artifacts(list(result.values())),
            summary={"figure_count": len(result), "output_dir": str(run_output_dir)},
        )
    except Exception as exc:
        message = "Paired figure generation failed." if _is_english(language) else "配对图生成失败。"
        return AgentToolResult("failed", message, error=str(exc))


def run_gaussian_peaks(spectrum_workbook: Path, output_dir: Path, params: dict[str, Any] | None = None, language: str = "中文") -> AgentToolResult:
    """Run Gaussian peak decomposition on a spectrum workbook."""

    params = params or {}
    try:
        english = _is_english(language)
        peak_count = int(params.get("peak_count", 2))
        run_output_dir = _gaussian_run_output_dir(Path(output_dir), peak_count)
        result = run_gaussian_decomposition_on_spectrum_workbook(
            Path(spectrum_workbook),
            run_output_dir,
            config=GaussianConfig(peak_count=peak_count),
            plot_config=PlotConfig(),
        )
        artifacts = _as_artifacts({key: value for key, value in result.items() if key != "figure_dir"})
        artifacts.extend(_summary_column_artifacts(result.get("summary_csv"), "gaussian_figure"))
        summary = {key: str(value) for key, value in result.items()} | {"peak_count": peak_count, "output_dir": str(run_output_dir)}
        dropped = 0
        table = _read_first_table(Path(result["summary_csv"])) if result.get("summary_csv") else None
        if table is not None and "dropped_component_count" in table.columns and not table.empty:
            dropped = int(table.groupby("signal_name")["dropped_component_count"].first().sum())
            summary["kept_peak_count"] = int(len(table))
            summary["dropped_component_count"] = dropped
        note_en = f" {dropped} component(s) below 1% of the area were dropped." if dropped else ""
        note_zh = f"已自动剔除 {dropped} 个面积占比低于 1% 的分量。" if dropped else ""
        message = (
            f"Gaussian peak decomposition completed with {peak_count} peaks.{note_en} Outputs are grouped in {run_output_dir.name}."
            if english
            else f"Gaussian 分峰完成，使用 {peak_count} 个峰。{note_zh}结果已归入 {run_output_dir.name}。"
        )
        return AgentToolResult(
            "success",
            message,
            artifacts=artifacts,
            summary=summary,
        )
    except Exception as exc:
        message = "Gaussian peak decomposition failed." if _is_english(language) else "Gaussian 分峰失败。"
        return AgentToolResult("failed", message, error=str(exc))


def generate_report(
    output_dir: Path,
    *,
    user_goal: str,
    validation: AgentToolResult,
    workflow_results: list[AgentToolResult],
    parameter_notes: str,
    language: str = "中文",
) -> AgentToolResult:
    """Generate a Markdown report from tool results."""

    try:
        english = _is_english(language)
        output_path = Path(output_dir) / timestamped_name("report", "md")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if english:
            lines = [
                "# T2 Inversion Agent Report",
                "",
                "## User Goal",
                user_goal.strip() or "The user did not provide an additional goal, so the default T2 inversion workflow was used.",
                "",
                "## Data Diagnosis",
                validation.message,
                "",
                "```text",
                str(validation.summary),
                "```",
                "",
                "## Parameter Explanation and Selection",
                parameter_notes,
                "",
                "## Tool Results",
            ]
        else:
            lines = [
                "# T2 反演智能体报告",
                "",
                "## 用户目标",
                user_goal.strip() or "用户未提供额外目标，按默认 T2 反演流程处理。",
                "",
                "## 数据诊断",
                validation.message,
                "",
                "```text",
                str(validation.summary),
                "```",
                "",
                "## 参数解释与选择",
                parameter_notes,
                "",
                "## 工具运行结果",
            ]

        for idx, result in enumerate(workflow_results, start=1):
            if english:
                lines.extend(
                    [
                        f"### Step {idx}",
                        f"- Status: {result.status}",
                        f"- Description: {result.message}",
                        f"- Output count: {len(result.artifacts)}",
                    ]
                )
            else:
                lines.extend(
                    [
                        f"### 步骤 {idx}",
                        f"- 状态：{result.status}",
                        f"- 说明：{result.message}",
                        f"- 输出数量：{len(result.artifacts)}",
                    ]
                )
            if result.error:
                lines.append(f"- Error: {result.error}" if english else f"- 错误：{result.error}")
            if result.summary:
                lines.extend(["", "```text", str(result.summary), "```"])
            lines.append("")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        message = "English Markdown report generated." if english else "中文 Markdown 报告已生成。"
        return AgentToolResult("success", message, artifacts=[str(output_path)], summary={"report": str(output_path)})
    except Exception as exc:
        message = "Report generation failed." if _is_english(language) else "报告生成失败。"
        return AgentToolResult("failed", message, error=str(exc))
