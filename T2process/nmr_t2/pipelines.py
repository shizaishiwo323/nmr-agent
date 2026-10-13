"""High-level pipelines that orchestrate NMR T2 processing tasks.

This module is the main entry point for application users. It combines
I/O parsing, inversion, plotting, and exports into consistent workflows.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .config import GaussianConfig, LCurveConfig, NnlsConfig, PlotConfig
from .gaussian import decompose_spectrum_as_gaussians
from .io_utils import (
    dataframe_columns_to_numeric_xy,
    export_sheet_map_to_excel,
    find_numeric_pair_columns,
    load_decay_table_multi_column,
    read_sheet_map_from_excel,
    safe_token,
    sort_and_filter_signal,
    timestamped_name,
    trim_signal_from_global_peak,
)
from .lcurve import invert_single_signal_lcurve
from .models import TrimmedSignal
from .nnls import estimate_noise_vector, invert_single_signal_nnls


def _build_output_path(output_dir: Path, dataset_name: str, artifact_name: str, suffix: str) -> Path:
    """Build standardized output path as `<dataset>__<artifact>__timestamp.<suffix>`."""

    safe_dataset = safe_token(dataset_name)
    safe_artifact = safe_token(artifact_name)
    candidate = output_dir / timestamped_name(f"{safe_dataset}__{safe_artifact}", suffix)
    if len(str(candidate)) <= 240:
        return candidate

    digest = hashlib.sha1(safe_dataset.encode("utf-8")).hexdigest()[:8]
    short_dataset = f"d_{digest}"
    short_artifact = safe_artifact[:12]
    return output_dir / timestamped_name(f"{short_dataset}__{short_artifact}", suffix)


def _regularization_filename_token(value: float) -> str:
    text = f"{float(value):.6g}".replace("-", "m").replace("+", "p").replace(".", "p")
    return safe_token(f"alpha_{text}")


def _selected_alpha_filename_token(values: list[float]) -> str:
    finite_values = [float(value) for value in values if np.isfinite(float(value))]
    if not finite_values:
        return "alpha_unknown"
    if len(finite_values) == 1 or np.allclose(finite_values, finite_values[0], rtol=1e-9, atol=1e-12):
        return _regularization_filename_token(finite_values[0])
    return safe_token(
        f"{_regularization_filename_token(min(finite_values))}_to_"
        f"{_regularization_filename_token(max(finite_values)).removeprefix('alpha_')}"
    )


def _build_decay_fit_noise_frame(
    fit_time_ms: np.ndarray,
    fit_amplitude: np.ndarray,
    residual: np.ndarray,
) -> pd.DataFrame:
    """Return inversion-sampled decay, fit, and residual noise in one table."""

    fit = np.asarray(fit_amplitude, dtype=float)
    noise = np.asarray(residual, dtype=float)
    return pd.DataFrame(
        {
            "fit_time_ms": np.asarray(fit_time_ms, dtype=float),
            "decay_amplitude": fit + noise,
            "fit_amplitude": fit,
            "noise_amplitude": noise,
            "residual": noise,
        }
    )


def _add_inversion_fit_and_noise(
    frame: pd.DataFrame,
    trimmed: TrimmedSignal,
    *,
    t2_bins_ms: np.ndarray,
    spectrum: np.ndarray,
    baseline_amplitude: float,
) -> None:
    """Add full-resolution fit and the noise estimate used for weighting."""

    time_ms = np.asarray(trimmed.trimmed_time_ms, dtype=float)
    amplitude = np.asarray(trimmed.trimmed_amplitude, dtype=float)
    fitted = np.exp(-time_ms[:, None] / np.asarray(t2_bins_ms, dtype=float)[None, :]) @ np.asarray(
        spectrum,
        dtype=float,
    )
    fitted += float(baseline_amplitude)
    noise = estimate_noise_vector(amplitude)
    frame.loc[: time_ms.size - 1, "trimmed_fit_amplitude"] = fitted
    frame.loc[: time_ms.size - 1, "trimmed_inversion_noise"] = noise


def _prepare_signal_for_inversion(
    signal_name: str,
    time_ms: np.ndarray,
    amplitude: np.ndarray,
    *,
    trim_from_peak: bool,
    min_points_after_trim: int,
) -> TrimmedSignal:
    """Return either the post-peak decay segment or the full sorted signal."""

    if trim_from_peak:
        return trim_signal_from_global_peak(
            signal_name,
            time_ms,
            amplitude,
            min_points_after_trim=int(min_points_after_trim),
        )

    sorted_time, sorted_amp = sort_and_filter_signal(time_ms, amplitude, minimum_points=int(min_points_after_trim))
    peak_idx = int(np.argmax(sorted_amp)) if sorted_amp.size else -1
    return TrimmedSignal(
        signal_name=signal_name,
        raw_time_ms=sorted_time,
        raw_amplitude=sorted_amp,
        trimmed_time_ms=sorted_time,
        trimmed_amplitude=sorted_amp,
        peak_index_in_sorted_raw=peak_idx,
    )


def run_nnls_workbook(
    input_workbook: Path,
    output_dir: Path,
    *,
    config: Optional[NnlsConfig] = None,
    time_to_ms_scale: float = 1.0,
    trim_from_peak: bool = True,
) -> Dict[str, Path]:
    """Run fixed-regularization NNLS inversion for all valid signals in a workbook."""

    cfg = config or NnlsConfig()
    if not input_workbook.exists():
        raise FileNotFoundError(f"Input workbook not found: {input_workbook}")

    dataset_name = input_workbook.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    time_ms, signal_matrix, signal_names, _ = load_decay_table_multi_column(
        input_workbook,
        time_to_ms_scale=float(time_to_ms_scale),
        signal_name_prefix="col",
    )

    spectrum_sheets: Dict[str, pd.DataFrame] = {}
    trimmed_sheets: Dict[str, pd.DataFrame] = {}
    fit_sheets: Dict[str, pd.DataFrame] = {}
    summary_rows: list[dict] = []

    for idx, signal_name in enumerate(signal_names):
        signal = signal_matrix[:, idx]

        trimmed = _prepare_signal_for_inversion(
            signal_name,
            time_ms,
            signal,
            trim_from_peak=bool(trim_from_peak),
            min_points_after_trim=int(cfg.min_points_after_trim),
        )

        inversion = invert_single_signal_nnls(
            trimmed.trimmed_time_ms,
            trimmed.trimmed_amplitude,
            signal_name=signal_name,
            config=cfg,
        )

        spectrum_sheets[signal_name] = pd.DataFrame(
            {
                "t2_ms": inversion.t2_bins_ms,
                "amplitude": inversion.spectrum,
            }
        )

        trimmed_frame = pd.DataFrame(
            {
                "raw_time_ms": trimmed.raw_time_ms,
                "raw_amplitude": trimmed.raw_amplitude,
                "trimmed_time_ms": np.nan,
                "trimmed_amplitude": np.nan,
            }
        )
        trimmed_frame.loc[: trimmed.trimmed_time_ms.size - 1, "trimmed_time_ms"] = trimmed.trimmed_time_ms
        trimmed_frame.loc[: trimmed.trimmed_amplitude.size - 1, "trimmed_amplitude"] = trimmed.trimmed_amplitude
        _add_inversion_fit_and_noise(
            trimmed_frame,
            trimmed,
            t2_bins_ms=inversion.t2_bins_ms,
            spectrum=inversion.spectrum,
            baseline_amplitude=float(inversion.metadata.get("baseline_amplitude", 0.0)),
        )
        trimmed_sheets[signal_name] = trimmed_frame

        fit_sheets[signal_name] = _build_decay_fit_noise_frame(
            inversion.fit_time_ms,
            inversion.fit_amplitude,
            inversion.residual,
        )

        summary_rows.append(
            {
                "signal_name": signal_name,
                "regularization": inversion.regularization,
                "residual_norm": inversion.residual_norm,
                "roughness_norm": inversion.roughness_norm,
                "raw_points": int(trimmed.raw_time_ms.size),
                "trimmed_points": int(trimmed.trimmed_time_ms.size),
                "peak_index_in_sorted_raw": int(trimmed.peak_index_in_sorted_raw),
            }
        )

    alpha_token = _regularization_filename_token(cfg.regularization)
    spectrum_path = _build_output_path(output_dir, dataset_name, f"nnls_spectrum__{alpha_token}", "xlsx")
    trimmed_path = _build_output_path(output_dir, dataset_name, f"nnls_trimmed_decay__{alpha_token}", "xlsx")
    fit_path = _build_output_path(output_dir, dataset_name, f"nnls_fit__{alpha_token}", "xlsx")
    summary_csv = _build_output_path(output_dir, dataset_name, f"nnls_summary__{alpha_token}", "csv")
    summary_xlsx = _build_output_path(output_dir, dataset_name, f"nnls_summary__{alpha_token}", "xlsx")

    export_sheet_map_to_excel(spectrum_sheets, spectrum_path)
    export_sheet_map_to_excel(trimmed_sheets, trimmed_path)
    export_sheet_map_to_excel(fit_sheets, fit_path)

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(summary_csv, index=False, encoding="utf-8-sig")
    summary_df.to_excel(summary_xlsx, index=False)

    return {
        "spectrum_xlsx": spectrum_path,
        "trimmed_xlsx": trimmed_path,
        "fit_xlsx": fit_path,
        "summary_csv": summary_csv,
        "summary_xlsx": summary_xlsx,
    }


def run_lcurve_workbook(
    input_workbook: Path,
    output_dir: Path,
    *,
    config: Optional[LCurveConfig] = None,
    plot_config: Optional[PlotConfig] = None,
    time_to_ms_scale: float = 1.0,
    trim_from_peak: bool = True,
) -> Dict[str, Path]:
    """Run L-curve inversion for all valid signals in a workbook."""

    cfg = config or LCurveConfig()
    if not input_workbook.exists():
        raise FileNotFoundError(f"Input workbook not found: {input_workbook}")

    dataset_name = input_workbook.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir = output_dir / "lcurve_figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    time_ms, signal_matrix, signal_names, _ = load_decay_table_multi_column(
        input_workbook,
        time_to_ms_scale=float(time_to_ms_scale),
        signal_name_prefix="col",
    )

    spectrum_sheets: Dict[str, pd.DataFrame] = {}
    metrics_sheets: Dict[str, pd.DataFrame] = {}
    trimmed_sheets: Dict[str, pd.DataFrame] = {}
    fit_sheets: Dict[str, pd.DataFrame] = {}
    summary_rows: list[dict] = []

    for idx, signal_name in enumerate(signal_names):
        signal = signal_matrix[:, idx]

        trimmed = _prepare_signal_for_inversion(
            signal_name,
            time_ms,
            signal,
            trim_from_peak=bool(trim_from_peak),
            min_points_after_trim=int(cfg.min_points_after_trim),
        )

        result = invert_single_signal_lcurve(
            trimmed.trimmed_time_ms,
            trimmed.trimmed_amplitude,
            signal_name=signal_name,
            config=cfg,
        )

        spectrum_sheets[signal_name] = pd.DataFrame(
            {
                "t2_ms": result.t2_bins_ms,
                "amplitude": result.spectrum,
            }
        )

        metrics_sheets[signal_name] = pd.DataFrame(
            {
                "alpha_regularization": result.alpha_values,
                "zeta": result.zeta_values,
                "eta": result.eta_values,
                "residual_norm": result.residual_norms,
                "roughness_norm": result.roughness_norms,
                "slope_reciprocal": result.slope_reciprocal_values,
                "is_best": np.arange(result.alpha_values.size) == int(result.best_index),
            }
        )

        trimmed_frame = pd.DataFrame(
            {
                "raw_time_ms": trimmed.raw_time_ms,
                "raw_amplitude": trimmed.raw_amplitude,
                "trimmed_time_ms": np.nan,
                "trimmed_amplitude": np.nan,
            }
        )
        trimmed_frame.loc[: trimmed.trimmed_time_ms.size - 1, "trimmed_time_ms"] = trimmed.trimmed_time_ms
        trimmed_frame.loc[: trimmed.trimmed_amplitude.size - 1, "trimmed_amplitude"] = trimmed.trimmed_amplitude
        _add_inversion_fit_and_noise(
            trimmed_frame,
            trimmed,
            t2_bins_ms=result.t2_bins_ms,
            spectrum=result.spectrum,
            baseline_amplitude=float(result.metadata.get("baseline_amplitude", 0.0)),
        )
        trimmed_sheets[signal_name] = trimmed_frame

        fit_sheets[signal_name] = _build_decay_fit_noise_frame(
            result.fit_time_ms,
            result.fit_amplitude,
            result.residual,
        )

        alpha_token = _regularization_filename_token(result.best_regularization)
        figure_path = _build_output_path(
            figure_dir,
            signal_name,
            f"lcurve__{alpha_token}",
            "png",
        )
        if len(str(figure_path)) > 240:
            figure_dir = output_dir / "f"
            figure_dir.mkdir(parents=True, exist_ok=True)
            figure_path = figure_dir / timestamped_name(alpha_token, "png")
        from .plotting import plot_lcurve_result

        plot_lcurve_result(result, output_path=figure_path, config=plot_config)

        summary_rows.append(
            {
                "signal_name": signal_name,
                "best_regularization": result.best_regularization,
                "best_index": int(result.best_index),
                "best_residual_norm": float(result.residual_norms[result.best_index]),
                "best_roughness_norm": float(result.roughness_norms[result.best_index]),
                "best_slope_reciprocal": float(result.slope_reciprocal_values[result.best_index]),
                "used_range_filter": bool(result.used_range_filter),
                "raw_points": int(trimmed.raw_time_ms.size),
                "trimmed_points": int(trimmed.trimmed_time_ms.size),
                "lcurve_figure": str(figure_path),
            }
        )

    alpha_token = _selected_alpha_filename_token([float(row["best_regularization"]) for row in summary_rows])
    spectrum_path = _build_output_path(output_dir, dataset_name, f"lcurve_spectrum__{alpha_token}", "xlsx")
    metrics_path = _build_output_path(output_dir, dataset_name, f"lcurve_metrics__{alpha_token}", "xlsx")
    trimmed_path = _build_output_path(output_dir, dataset_name, f"lcurve_trimmed_decay__{alpha_token}", "xlsx")
    fit_path = _build_output_path(output_dir, dataset_name, f"lcurve_fit__{alpha_token}", "xlsx")
    summary_csv = _build_output_path(output_dir, dataset_name, f"lcurve_summary__{alpha_token}", "csv")
    summary_xlsx = _build_output_path(output_dir, dataset_name, f"lcurve_summary__{alpha_token}", "xlsx")

    export_sheet_map_to_excel(spectrum_sheets, spectrum_path)
    export_sheet_map_to_excel(metrics_sheets, metrics_path)
    export_sheet_map_to_excel(trimmed_sheets, trimmed_path)
    export_sheet_map_to_excel(fit_sheets, fit_path)

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(summary_csv, index=False, encoding="utf-8-sig")
    summary_df.to_excel(summary_xlsx, index=False)

    return {
        "spectrum_xlsx": spectrum_path,
        "metrics_xlsx": metrics_path,
        "trimmed_xlsx": trimmed_path,
        "fit_xlsx": fit_path,
        "summary_csv": summary_csv,
        "summary_xlsx": summary_xlsx,
        "figure_dir": figure_dir,
    }


def run_plotting_workbook_pair(
    raw_decay_workbook: Path,
    spectrum_workbook: Path,
    output_dir: Path,
    *,
    plot_config: Optional[PlotConfig] = None,
    time_to_ms_scale: float = 1.0,
    filename_tag: str | None = None,
) -> Dict[str, Path]:
    """Generate paired decay/T2 figures from raw and spectrum workbooks."""

    if not raw_decay_workbook.exists():
        raise FileNotFoundError(f"Raw decay workbook not found: {raw_decay_workbook}")
    if not spectrum_workbook.exists():
        raise FileNotFoundError(f"Spectrum workbook not found: {spectrum_workbook}")

    output_dir.mkdir(parents=True, exist_ok=True)

    raw_time_ms, raw_matrix, raw_signal_names, _ = load_decay_table_multi_column(
        raw_decay_workbook,
        time_to_ms_scale=float(time_to_ms_scale),
        signal_name_prefix="col",
    )
    raw_map = {name: raw_matrix[:, idx] for idx, name in enumerate(raw_signal_names)}

    spectrum_map = read_sheet_map_from_excel(spectrum_workbook)
    generated: Dict[str, Path] = {}

    for signal_name, raw_signal in raw_map.items():
        if signal_name not in spectrum_map:
            continue

        spectrum_df = spectrum_map[signal_name]
        x_col, y_col = find_numeric_pair_columns(
            spectrum_df,
            candidate_x=("t2_ms", "time_ms", "time", "t2"),
            candidate_y=("amplitude", "peak", "signal"),
        )
        t2_bins, spectrum = dataframe_columns_to_numeric_xy(spectrum_df, x_col, y_col)

        figure_stem = f"{safe_token(raw_decay_workbook.stem)}__{safe_token(signal_name)}__decay_t2"
        if filename_tag:
            figure_stem = f"{figure_stem}__{safe_token(filename_tag)}"
        figure_path = output_dir / timestamped_name(figure_stem, "png")
        from .plotting import plot_decay_and_spectrum_pair

        plot_decay_and_spectrum_pair(
            signal_name=signal_name,
            raw_time_ms=raw_time_ms,
            raw_amplitude=raw_signal,
            t2_bins_ms=t2_bins,
            spectrum=spectrum,
            output_path=figure_path,
            config=plot_config,
        )
        generated[signal_name] = figure_path

    return generated


def run_gaussian_decomposition_on_spectrum_workbook(
    spectrum_workbook: Path,
    output_dir: Path,
    *,
    config: Optional[GaussianConfig] = None,
    plot_config: Optional[PlotConfig] = None,
) -> Dict[str, Path]:
    """Run Gaussian decomposition for each spectrum sheet in a workbook."""

    cfg = config or GaussianConfig()
    if not spectrum_workbook.exists():
        raise FileNotFoundError(f"Spectrum workbook not found: {spectrum_workbook}")

    dataset_name = spectrum_workbook.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir = output_dir / f"{safe_token(dataset_name)}__gaussian_figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    spectrum_map = read_sheet_map_from_excel(spectrum_workbook)
    component_sheets: Dict[str, pd.DataFrame] = {}
    fit_sheets: Dict[str, pd.DataFrame] = {}
    summary_rows: list[dict] = []

    for signal_name, spectrum_df in spectrum_map.items():
        x_col, y_col = find_numeric_pair_columns(
            spectrum_df,
            candidate_x=("t2_ms", "time_ms", "time", "t2"),
            candidate_y=("amplitude", "peak", "signal"),
        )
        t2_bins, spectrum = dataframe_columns_to_numeric_xy(spectrum_df, x_col, y_col)

        result = decompose_spectrum_as_gaussians(
            t2_bins,
            spectrum,
            signal_name=signal_name,
            config=cfg,
        )

        fit_frame = pd.DataFrame(
            {
                "t2_ms": result.t2_bins_ms,
                "original_spectrum": result.original_spectrum,
                "fitted_spectrum": result.fitted_spectrum,
            }
        )
        for idx in range(result.component_matrix.shape[0]):
            fit_frame[f"component_{idx + 1}"] = result.component_matrix[idx, :]
        fit_sheets[signal_name] = fit_frame
        component_sheets[signal_name] = result.peak_table

        figure_path = figure_dir / timestamped_name(f"{safe_token(signal_name)}__gaussian", "png")
        from .plotting import plot_gaussian_decomposition

        plot_gaussian_decomposition(result, output_path=figure_path, config=plot_config)

        for _, row in result.peak_table.iterrows():
            summary_rows.append(
                {
                    "signal_name": signal_name,
                    "peak_id": int(row["peak_id"]),
                    "height": float(row["height"]),
                    "position_ms": float(row["position_ms"]),
                    "width_log10": float(row["width_log10"]),
                    "area": float(row["area"]),
                    "area_fraction": float(row["area_fraction"]),
                    "objective_value": float(result.objective_value),
                    "gaussian_figure": str(figure_path),
                }
            )

    peak_table_path = _build_output_path(output_dir, dataset_name, "gaussian_peak_table", "xlsx")
    fit_table_path = _build_output_path(output_dir, dataset_name, "gaussian_fit", "xlsx")
    summary_csv = _build_output_path(output_dir, dataset_name, "gaussian_summary", "csv")
    summary_xlsx = _build_output_path(output_dir, dataset_name, "gaussian_summary", "xlsx")

    export_sheet_map_to_excel(component_sheets, peak_table_path)
    export_sheet_map_to_excel(fit_sheets, fit_table_path)

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(summary_csv, index=False, encoding="utf-8-sig")
    summary_df.to_excel(summary_xlsx, index=False)

    return {
        "peak_table_xlsx": peak_table_path,
        "fit_xlsx": fit_table_path,
        "summary_csv": summary_csv,
        "summary_xlsx": summary_xlsx,
        "figure_dir": figure_dir,
    }
