from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.text import Annotation

from t2_agent.guidance import build_parameter_guidance, infer_requested_plan
from t2_agent.models import AgentToolResult
from t2_agent.tools import (
    generate_report,
    inspect_workbook_schema,
    interpret_results,
    plot_decay_spectrum,
    repair_workbook,
    run_fixed_nnls,
    run_gaussian_peaks,
    run_lcurve,
    validate_workbook,
)

from T2process.nmr_t2.io_utils import load_decay_table_multi_column
from T2process.nmr_t2.models import LCurveInversionResult
from T2process.nmr_t2.config import LCurveConfig
from T2process.nmr_t2.pipelines import _build_output_path
from T2process.nmr_t2.plotting import plot_lcurve_result
from t2_agent.interactive_lcurve import (
    DEFAULT_EXPLORER_LCURVE_PARAMS,
    alpha_path_figure,
    lcurve_metric_figure,
    selected_alpha_from_plotly_selection,
)
from lcurve_explorer_app import _page_css, _spectrum_figure, _visible_spectrum_source


ROOT = Path(__file__).resolve().parents[1]
SIMULATION = ROOT / "T2process" / "Example data" / "SimulationDecay.xlsx"
SWAPPED_EXPERIMENTAL = ROOT / "T2process" / "Example data" / "ExperimentalDecay.xlsx"
PEA_DECAY = ROOT / "testData" / "standard 30%.1.pea"


def test_guidance_detects_2d_png_simulation_intent():
    plan = infer_requested_plan("上传红黄PNG，帮我做二维NMR模拟并T2反演")

    assert plan.workflow == "simulation_2d_png"
    assert plan.needs_gaussian is False


def test_guidance_detects_rule_geometry_simulation_intent():
    plan = infer_requested_plan("设置规则几何，两个孔耦合，跑一次完整二维模拟")

    assert plan.workflow == "simulation_2d_rule"


def test_validate_workbook_detects_decay_data_and_recommends_seconds_scale():
    result = validate_workbook(SIMULATION)

    assert result.status == "success"
    assert result.summary["data_kind"] == "decay"
    assert result.summary["signal_column_count"] >= 1
    assert result.summary["recommended_time_to_ms_scale"] == 1000.0
    assert "第 1 列" in result.message
    assert "时间列" in result.message
    assert "T2 谱表" not in result.message


def test_repair_workbook_writes_standardized_time_ms_file(tmp_path):
    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path, validation.summary["recommended_time_to_ms_scale"])

    assert repaired.status == "success"
    output_path = Path(repaired.artifacts[0])
    assert output_path.exists()

    frame = pd.read_excel(output_path)
    assert list(frame.columns)[:2] == ["time_ms", "Peak"]
    assert frame["time_ms"].max() > 1.0


def test_pipeline_output_paths_include_millisecond_timestamp(tmp_path):
    output_path = _build_output_path(tmp_path, "sample decay", "lcurve spectrum", "xlsx")

    assert output_path.parent == tmp_path
    assert output_path.name.startswith("sample_decay__lcurve_spectrum__")
    timestamp = output_path.stem.rsplit("__", 1)[-1]
    assert len(timestamp) == 19
    assert timestamp[8] == "_"
    assert timestamp[15] == "_"
    assert timestamp.replace("_", "").isdigit()


def test_validate_and_repair_experimental_decay_fixture(tmp_path):
    schema = inspect_workbook_schema(SWAPPED_EXPERIMENTAL)
    assert schema.status == "success"
    labels = [profile["label"] for profile in schema.summary["column_profiles"]]
    assert "Time" in labels
    assert "Peak" in labels

    result = validate_workbook(SWAPPED_EXPERIMENTAL)

    assert result.status == "success"
    assert result.summary["time_column_label"] == "Time"
    assert result.summary["signal_column_labels"] == ["Peak"]
    assert result.summary["column_order_issue"] == "none"
    assert "Time" in result.message
    assert "Peak" in result.message

    repaired = repair_workbook(SWAPPED_EXPERIMENTAL, tmp_path, result.summary["recommended_time_to_ms_scale"])
    frame = pd.read_excel(repaired.artifacts[0])

    assert list(frame.columns)[:2] == ["time_ms", "Peak"]
    assert frame["time_ms"].iloc[0] == 0.1005
    assert frame["Peak"].iloc[0] == 7282.1999


def test_validate_and_repair_pea_decay_uses_first_two_columns(tmp_path):
    result = validate_workbook(PEA_DECAY)

    assert result.status == "success", result.error
    assert result.summary["data_kind"] == "decay"
    assert result.summary["valid_time_rows"] == 8000
    assert result.summary["recommended_time_to_ms_scale"] == 1.0
    assert result.summary["time_column_label"] == "Time(ms)"
    assert result.summary["signal_column_labels"][0] == "Amplitude"
    assert result.summary["signal_excel_columns"][0] == 2

    repaired = repair_workbook(PEA_DECAY, tmp_path, result.summary["recommended_time_to_ms_scale"])
    frame = pd.read_excel(repaired.artifacts[0])

    assert repaired.status == "success", repaired.error
    assert list(frame.columns)[:2] == ["time_ms", "Amplitude"]
    assert frame["time_ms"].iloc[0] == 0.201001
    assert frame["Amplitude"].iloc[0] == 1098.5267


def test_low_level_pea_decay_loader_keeps_first_two_numeric_columns():
    time_ms, signal_matrix, signal_names, column_ids = load_decay_table_multi_column(PEA_DECAY)

    assert time_ms.shape == (8000,)
    assert signal_matrix.shape[0] == 8000
    assert signal_names[0] == "col_2"
    assert column_ids[0] == 2
    assert time_ms[0] == 0.201001
    assert signal_matrix[0, 0] == 1098.5267


def test_lcurve_plot_labels_best_regularization_at_selected_point(monkeypatch):
    monkeypatch.setattr(plt, "close", lambda figure: None)
    result = LCurveInversionResult(
        signal_name="col_2",
        t2_bins_ms=np.array([1.0, 10.0]),
        spectrum=np.array([0.2, 0.8]),
        fit_time_ms=np.array([1.0, 2.0]),
        fit_amplitude=np.array([1.0, 0.8]),
        residual=np.array([0.0, 0.1]),
        best_regularization=7.609e-2,
        best_index=1,
        alpha_values=np.array([1e-3, 7.609e-2, 1.0]),
        residual_norms=np.array([20.0, 40.0, 120.0]),
        roughness_norms=np.array([300.0, 140.0, 20.0]),
        zeta_values=np.array([0.0, 0.0, 0.0]),
        eta_values=np.array([0.0, 0.0, 0.0]),
        slope_reciprocal_values=np.array([0.4, 0.2156, 0.1]),
        used_range_filter=True,
        metadata={},
    )

    plot_lcurve_result(result)
    axis = plt.gcf().axes[0]
    annotations = [text for text in axis.texts if isinstance(text, Annotation)]

    assert any("Best eps = 7.609e-02" in item.get_text() for item in annotations)
    assert any("R = 0.2156" in item.get_text() for item in annotations)
    assert all(item.arrow_patch is not None for item in annotations)


def test_lcurve_default_alpha_search_uses_requested_range():
    cfg = LCurveConfig()

    assert cfg.alpha_min == 1e-3
    assert cfg.alpha_max == 1e4
    assert cfg.alpha_count == 300
    assert DEFAULT_EXPLORER_LCURVE_PARAMS["alpha_min"] == 1e-3
    assert DEFAULT_EXPLORER_LCURVE_PARAMS["alpha_max"] == 1e4
    assert DEFAULT_EXPLORER_LCURVE_PARAMS["alpha_count"] == 300


def test_interactive_lcurve_selection_helpers_do_not_require_precomputed_spectra():
    metrics = pd.DataFrame(
        {
            "alpha_regularization": [1e-3, 1e-2, 1e-1],
            "residual_norm": [20.0, 40.0, 120.0],
            "roughness_norm": [300.0, 140.0, 20.0],
            "slope_reciprocal": [0.4, 0.2156, 0.1],
            "is_best": [False, True, False],
        }
    )

    lcurve_fig = lcurve_metric_figure(metrics, selected_index=2)
    alpha_fig = alpha_path_figure(metrics, selected_index=2)
    selected = selected_alpha_from_plotly_selection({"selection": {"points": [{"point_index": 2}]}}, metrics)

    assert selected == 1e-1
    assert lcurve_fig.data[0].customdata[2][1] == "1.000000e-01"
    assert alpha_fig.data[0].y[2] == 1e-1
    assert all("spectrum" not in trace.name.lower() for trace in lcurve_fig.data)


def test_lcurve_explorer_shows_lcurve_spectrum_before_confirmed_inversion(tmp_path):
    lcurve_spectrum = tmp_path / "lcurve_spectrum.xlsx"
    confirmed_spectrum = tmp_path / "confirmed_spectrum.xlsx"

    source = _visible_spectrum_source(
        {"spectrum_xlsx": str(lcurve_spectrum)},
        confirmed=None,
        selected_alpha=0.1,
        confirmed_alpha=None,
    )
    confirmed_source = _visible_spectrum_source(
        {"spectrum_xlsx": str(lcurve_spectrum)},
        confirmed={"spectrum_xlsx": str(confirmed_spectrum)},
        selected_alpha=0.1,
        confirmed_alpha=0.2,
    )

    assert source == (lcurve_spectrum, 0.1, "L-curve selected")
    assert confirmed_source == (confirmed_spectrum, 0.2, "Confirmed fixed-alpha")


def test_lcurve_explorer_uses_compact_publication_plot_style():
    metrics = pd.DataFrame(
        {
            "alpha_regularization": [1e-3, 1e-2, 1e-1],
            "residual_norm": [20.0, 40.0, 120.0],
            "roughness_norm": [300.0, 140.0, 20.0],
            "slope_reciprocal": [0.4, 0.2156, 0.1],
            "is_best": [False, True, False],
        }
    )
    spectrum = pd.DataFrame({"t2_ms": [1.0, 10.0, 100.0], "amplitude": [0.2, 1.0, 0.1]})

    lcurve_fig = lcurve_metric_figure(metrics, selected_index=1)
    alpha_fig = alpha_path_figure(metrics, selected_index=1)
    spectrum_fig = _spectrum_figure(spectrum, 0.01)
    css = _page_css()

    assert ".block-container" in css
    assert "max-width: 1180px" in css
    assert lcurve_fig.layout.height == 360
    assert alpha_fig.layout.height == 300
    assert spectrum_fig.layout.height == 360
    assert lcurve_fig.layout.plot_bgcolor == "#f8fbff"
    assert lcurve_fig.layout.xaxis.gridcolor == "#dbe7f6"
    assert lcurve_fig.data[0].marker.opacity == 0.88
    assert spectrum_fig.data[0].fill == "tozeroy"


def test_lcurve_explorer_uses_high_contrast_colors():
    metrics = pd.DataFrame(
        {
            "alpha_regularization": [1e-3, 1e-2, 1e-1],
            "residual_norm": [20.0, 40.0, 120.0],
            "roughness_norm": [300.0, 140.0, 20.0],
            "slope_reciprocal": [0.4, 0.2156, 0.1],
            "is_best": [False, True, False],
        }
    )
    spectrum = pd.DataFrame({"t2_ms": [1.0, 10.0, 100.0], "amplitude": [0.2, 1.0, 0.1]})

    lcurve_fig = lcurve_metric_figure(metrics, selected_index=1)
    spectrum_fig = _spectrum_figure(spectrum, 0.01)
    css = _page_css()

    assert lcurve_fig.data[0].line.color == "#1d4ed8"
    assert lcurve_fig.data[0].marker.color == ("#38bdf8", "#f97316", "#38bdf8")
    assert lcurve_fig.layout.plot_bgcolor == "#f8fbff"
    assert spectrum_fig.data[0].line.color == "#0f766e"
    assert spectrum_fig.data[0].fillcolor == "rgba(15, 118, 110, 0.18)"
    assert "background: #f7faff" in css
    assert "border: 1px solid #c9d8ee" in css


def test_validate_workbook_handles_multi_signal_layout_without_named_headers(tmp_path):
    path = tmp_path / "multi_signal.xlsx"
    pd.DataFrame(
        [
            [0.1, 100.0, 80.0],
            [0.2, 92.0, 70.0],
            [0.3, 85.0, 62.0],
            [0.4, 77.0, 55.0],
        ]
    ).to_excel(path, index=False, header=False)

    result = validate_workbook(path)
    repaired = repair_workbook(path, tmp_path, result.summary["recommended_time_to_ms_scale"])
    frame = pd.read_excel(repaired.artifacts[0])

    assert result.status == "success"
    assert result.summary["time_column_excel_index"] == 1
    assert result.summary["signal_excel_columns"] == [2, 3]
    assert list(frame.columns) == ["time_ms", "col_2", "col_3"]


def test_validate_and_repair_three_column_csv_ignores_residual_noise_column(tmp_path):
    path = tmp_path / "three_column_decay_with_residual.csv"
    time_ms = np.arange(1, 121, dtype=float) * 0.6
    decay = 1.7 * np.exp(-time_ms / 28.0) + 0.05
    residual = np.where(np.arange(time_ms.size) % 2 == 0, 0.08, -0.07)
    pd.DataFrame(np.column_stack([time_ms, decay, residual])).to_csv(path, index=False, header=False)

    result = validate_workbook(path)
    repaired = repair_workbook(path, tmp_path, result.summary["recommended_time_to_ms_scale"])
    frame = pd.read_excel(repaired.artifacts[0])

    assert result.status == "success", result.error
    assert result.summary["time_column_excel_index"] == 1
    assert result.summary["signal_excel_columns"] == [2]
    assert result.summary["ignored_signal_like_excel_columns"] == [3]
    assert list(frame.columns) == ["time_ms", "col_2"]


def test_uploaded_t2_spectrum_is_not_repaired_or_inverted(tmp_path):
    path = tmp_path / "uploaded_t2_spectrum.xlsx"
    t2_ms = np.logspace(-1, 3, 80)
    amplitude = np.exp(-((np.log10(t2_ms) - 1.0) ** 2) / 0.18)
    pd.DataFrame({"t2_ms": t2_ms, "amplitude": amplitude}).to_excel(path, index=False)

    validation = validate_workbook(path)
    repaired = repair_workbook(path, tmp_path / "standardized")
    lcurve = run_lcurve(path, tmp_path / "lcurve", {"num_bins": 40, "alpha_count": 8})
    fixed = run_fixed_nnls(path, tmp_path / "nnls", {"regularization": 1.0, "num_bins": 40})
    gaussian = run_gaussian_peaks(path, tmp_path / "gaussian", {"peak_count": 2})

    assert validation.status == "success"
    assert validation.summary["data_kind"] == "spectrum"
    assert repaired.status == "failed"
    assert repaired.error == "spectrum_input_not_decay"
    assert lcurve.status == "failed"
    assert lcurve.error == "spectrum_input_not_decay"
    assert fixed.status == "failed"
    assert fixed.error == "spectrum_input_not_decay"
    assert gaussian.status == "success", gaussian.error


def test_repeated_gaussian_runs_are_grouped_by_peak_count(tmp_path):
    path = tmp_path / "uploaded_t2_spectrum.xlsx"
    t2_ms = np.logspace(-1, 3, 80)
    log_t2 = np.log10(t2_ms)
    amplitude = np.exp(-((log_t2 - 1.0) ** 2) / 0.18) + 0.25 * np.exp(-((log_t2 - 2.1) ** 2) / 0.12)
    pd.DataFrame({"t2_ms": t2_ms, "amplitude": amplitude}).to_excel(path, index=False)

    two_peak = run_gaussian_peaks(path, tmp_path / "gaussian", {"peak_count": 2})
    three_peak = run_gaussian_peaks(path, tmp_path / "gaussian", {"peak_count": 3})

    assert two_peak.status == "success", two_peak.error
    assert three_peak.status == "success", three_peak.error
    assert two_peak.summary["output_dir"].endswith("peaks_2")
    assert three_peak.summary["output_dir"].endswith("peaks_3")
    assert set(map(Path, two_peak.artifacts)).isdisjoint(set(map(Path, three_peak.artifacts)))
    assert any("peaks_2" in Path(path).parts and "__gaussian__" in Path(path).name and Path(path).suffix == ".png" for path in two_peak.artifacts)
    assert any("peaks_3" in Path(path).parts and "__gaussian__" in Path(path).name and Path(path).suffix == ".png" for path in three_peak.artifacts)

    interpretation = interpret_results([two_peak, three_peak], tmp_path / "interpretation")
    assert interpretation.status == "success", interpretation.error
    assert "2 峰拟合" in interpretation.message
    assert "3 峰拟合" in interpretation.message


def test_repeated_lcurve_runs_are_grouped_by_parameters(tmp_path):
    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path / "standardized", validation.summary["recommended_time_to_ms_scale"])
    repaired_workbook = Path(repaired.artifacts[0])

    first = run_lcurve(
        repaired_workbook,
        tmp_path / "lcurve",
        {"num_bins": 50, "alpha_count": 8, "t2_min_ms": 0.01, "t2_max_ms": 100000.0},
    )
    second = run_lcurve(
        repaired_workbook,
        tmp_path / "lcurve",
        {"num_bins": 80, "alpha_count": 10, "t2_min_ms": 0.1, "t2_max_ms": 10000.0},
    )

    assert first.status == "success", first.error
    assert second.status == "success", second.error
    assert first.summary["output_dir"] != second.summary["output_dir"]
    assert "bins_50" in first.summary["output_dir"]
    assert "bins_80" in second.summary["output_dir"]
    assert set(map(Path, first.artifacts)).isdisjoint(set(map(Path, second.artifacts)))
    assert any("paired_plots" in Path(path).parts and "__decay_t2__" in Path(path).name and Path(path).suffix == ".png" for path in first.artifacts)
    assert any("paired_plots" in Path(path).parts and "__decay_t2__" in Path(path).name and Path(path).suffix == ".png" for path in second.artifacts)

    interpretation = interpret_results([first, second], tmp_path / "interpretation")
    assert interpretation.status == "success", interpretation.error
    assert "不同反演参数结果对比" in interpretation.message
    assert len(interpretation.summary["inversion_runs"]) == 2


def test_repeated_lcurve_runs_with_same_parameters_do_not_reuse_old_figures(tmp_path):
    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path / "standardized", validation.summary["recommended_time_to_ms_scale"])
    repaired_workbook = Path(repaired.artifacts[0])
    params = {"num_bins": 40, "alpha_count": 8, "t2_min_ms": 0.01, "t2_max_ms": 100000.0}

    first = run_lcurve(repaired_workbook, tmp_path / "lcurve", params)
    second = run_lcurve(repaired_workbook, tmp_path / "lcurve", params)

    assert first.status == "success", first.error
    assert second.status == "success", second.error
    assert first.summary["output_dir"] == second.summary["output_dir"]
    first_lcurve_figures = {Path(path) for path in first.artifacts if "__lcurve__" in Path(path).name and Path(path).suffix == ".png"}
    second_lcurve_figures = {Path(path) for path in second.artifacts if "__lcurve__" in Path(path).name and Path(path).suffix == ".png"}
    assert first_lcurve_figures
    assert second_lcurve_figures
    assert first_lcurve_figures.isdisjoint(second_lcurve_figures)


def test_lcurve_exported_inversion_artifacts_include_selected_alpha_in_names(tmp_path):
    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path / "standardized", validation.summary["recommended_time_to_ms_scale"])

    result = run_lcurve(
        Path(repaired.artifacts[0]),
        tmp_path / "lcurve",
        {"num_bins": 40, "alpha_count": 8, "t2_min_ms": 0.01, "t2_max_ms": 100000.0},
    )

    assert result.status == "success", result.error
    inversion_artifacts = [
        Path(path)
        for path in result.artifacts
        if Path(path).suffix.lower() in {".xlsx", ".csv", ".png"}
    ]
    assert inversion_artifacts
    assert all("__alpha_" in path.stem for path in inversion_artifacts)


def test_lcurve_outputs_use_short_figure_folder_on_long_windows_paths(tmp_path):
    validation = validate_workbook(SIMULATION)
    long_root = tmp_path / ("long_path_segment_" * 4)
    repaired = repair_workbook(SIMULATION, long_root / "standardized", validation.summary["recommended_time_to_ms_scale"])
    repaired_workbook = Path(repaired.artifacts[0])

    result = run_lcurve(
        repaired_workbook,
        long_root / "lcurve",
        {"num_bins": 40, "alpha_count": 8, "t2_min_ms": 0.01, "t2_max_ms": 100000.0},
    )

    assert result.status == "success", result.error
    assert any("alpha_" in Path(path).stem and Path(path).suffix == ".png" for path in result.artifacts)


def test_repeated_fixed_nnls_runs_are_grouped_by_parameters(tmp_path):
    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path / "standardized", validation.summary["recommended_time_to_ms_scale"])
    repaired_workbook = Path(repaired.artifacts[0])

    weak = run_fixed_nnls(repaired_workbook, tmp_path / "nnls", {"regularization": 0.1, "num_bins": 50})
    strong = run_fixed_nnls(repaired_workbook, tmp_path / "nnls", {"regularization": 10.0, "num_bins": 50})

    assert weak.status == "success", weak.error
    assert strong.status == "success", strong.error
    assert weak.summary["output_dir"] != strong.summary["output_dir"]
    assert "reg_01" in weak.summary["output_dir"]
    assert "reg_10" in strong.summary["output_dir"]
    assert set(map(Path, weak.artifacts)).isdisjoint(set(map(Path, strong.artifacts)))
    assert any("paired_plots" in Path(path).parts and "__decay_t2__" in Path(path).name and Path(path).suffix == ".png" for path in weak.artifacts)
    assert any("paired_plots" in Path(path).parts and "__decay_t2__" in Path(path).name and Path(path).suffix == ".png" for path in strong.artifacts)


def test_fixed_nnls_exported_inversion_artifacts_include_regularization_in_names(tmp_path):
    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path / "standardized", validation.summary["recommended_time_to_ms_scale"])

    result = run_fixed_nnls(
        Path(repaired.artifacts[0]),
        tmp_path / "nnls",
        {"regularization": 0.25, "num_bins": 50},
    )

    assert result.status == "success", result.error
    inversion_artifacts = [
        Path(path)
        for path in result.artifacts
        if Path(path).suffix.lower() in {".xlsx", ".csv", ".png"}
    ]
    assert inversion_artifacts
    assert all("__alpha_0p25" in path.stem for path in inversion_artifacts)


def test_standalone_pair_plots_are_grouped_by_spectrum_parameter_folder(tmp_path):
    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path / "standardized", validation.summary["recommended_time_to_ms_scale"])
    repaired_workbook = Path(repaired.artifacts[0])
    first = run_lcurve(repaired_workbook, tmp_path / "lcurve", {"num_bins": 50, "alpha_count": 8})
    second = run_lcurve(repaired_workbook, tmp_path / "lcurve", {"num_bins": 80, "alpha_count": 10})

    first_plot = plot_decay_spectrum(repaired_workbook, Path(first.summary["spectrum_xlsx"]), tmp_path / "plots")
    second_plot = plot_decay_spectrum(repaired_workbook, Path(second.summary["spectrum_xlsx"]), tmp_path / "plots")

    assert first_plot.status == "success", first_plot.error
    assert second_plot.status == "success", second_plot.error
    assert first_plot.summary["output_dir"] != second_plot.summary["output_dir"]
    assert set(map(Path, first_plot.artifacts)).isdisjoint(set(map(Path, second_plot.artifacts)))


def test_validate_uses_curve_shape_when_decay_has_spectrum_like_headers(tmp_path):
    path = tmp_path / "misleading_decay_headers.xlsx"
    time_ms = np.linspace(0.1, 80.0, 120)
    signal = np.exp(-time_ms / 22.0) * 7000.0
    pd.DataFrame({"t2_ms": time_ms, "amplitude": signal}).to_excel(path, index=False)

    result = validate_workbook(path)

    assert result.status == "success"
    assert result.summary["data_kind"] == "decay"


def test_validate_uses_curve_shape_when_spectrum_has_generic_headers(tmp_path):
    path = tmp_path / "generic_spectrum_headers.xlsx"
    t2_ms = np.logspace(-2, 5, 200)
    log_t2 = np.log10(t2_ms)
    amplitude = np.exp(-((log_t2 - 1.2) ** 2) / 0.35) + 0.25 * np.exp(-((log_t2 - 3.0) ** 2) / 0.5)
    pd.DataFrame({"Time": t2_ms, "Peak": amplitude}).to_excel(path, index=False)

    result = validate_workbook(path)

    assert result.status == "success"
    assert result.summary["data_kind"] == "spectrum"


def test_inspect_schema_reports_shape_based_data_kind(tmp_path):
    path = tmp_path / "misleading_decay_headers.xlsx"
    time_ms = np.linspace(0.1, 80.0, 120)
    signal = np.exp(-time_ms / 22.0) * 7000.0
    pd.DataFrame({"t2_ms": time_ms, "amplitude": signal}).to_excel(path, index=False)

    result = inspect_workbook_schema(path)

    assert result.status == "success"
    assert result.summary["preliminary_data_kind"] == "decay"


def test_guidance_explains_regularization_and_defaults_to_lcurve_for_new_user():
    plan = infer_requested_plan("我不懂参数，只想做T2反演")
    guidance = build_parameter_guidance(plan)

    assert plan.workflow == "lcurve_inversion"
    assert plan.needs_gaussian is False
    assert "平滑因子" in guidance
    assert "L-curve" in guidance
    assert "默认" in guidance


def test_guidance_can_render_english_for_english_ui():
    plan = infer_requested_plan("I do not understand the parameters, please choose automatically")
    guidance = build_parameter_guidance(plan, language="English")

    assert "Smoothing/regularization factor" in guidance
    assert "Default recommendation" in guidance
    assert "平滑因子" not in guidance


def test_guidance_extracts_fixed_regularization_and_peak_count():
    plan = infer_requested_plan("我要固定平滑因子 1，然后分两个峰")
    guidance = build_parameter_guidance(plan)

    assert plan.workflow == "fixed_nnls"
    assert plan.regularization == 1.0
    assert plan.needs_gaussian is True
    assert plan.peak_count == 2
    assert "2 个峰" in guidance


def test_guidance_treats_only_peak_decomposition_as_gaussian_only():
    plan = infer_requested_plan("只做分峰，分三个峰")

    assert plan.workflow == "gaussian_only"
    assert plan.needs_gaussian is True
    assert plan.peak_count == 3


def test_lcurve_gaussian_and_report_tools_create_artifacts(tmp_path):
    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path, validation.summary["recommended_time_to_ms_scale"])
    repaired_workbook = Path(repaired.artifacts[0])

    lcurve = run_lcurve(
        repaired_workbook,
        tmp_path / "lcurve",
        {
            "num_bins": 60,
            "alpha_count": 12,
            "time_to_ms_scale": 1.0,
            "trim_from_peak": True,
        },
    )
    assert lcurve.status == "success"
    assert any("__lcurve_spectrum__" in Path(path).name and Path(path).suffix == ".xlsx" for path in lcurve.artifacts)
    assert any("__decay_t2__" in Path(path).name and Path(path).suffix == ".png" for path in lcurve.artifacts), lcurve.summary.get("paired_plot_warning")

    gaussian = run_gaussian_peaks(
        Path(lcurve.summary["spectrum_xlsx"]),
        tmp_path / "gaussian",
        {"peak_count": 2},
    )
    assert gaussian.status == "success", gaussian.error
    assert gaussian.summary["peak_count"] == 2
    assert any("__gaussian_summary__" in Path(path).name and Path(path).suffix == ".csv" for path in gaussian.artifacts)

    report = generate_report(
        tmp_path / "report",
        user_goal="我不懂参数，只想做T2反演并分两个峰",
        validation=validation,
        workflow_results=[lcurve, gaussian],
        parameter_notes=build_parameter_guidance(infer_requested_plan("我不懂参数，只想做T2反演并分两个峰")),
    )
    assert report.status == "success"
    report_text = Path(report.artifacts[0]).read_text(encoding="utf-8")
    assert "T2 反演智能体报告" in report_text
    assert "平滑因子" in report_text


def test_generate_report_can_render_english(tmp_path):
    report = generate_report(
        tmp_path / "report",
        user_goal="Run an English report",
        validation=validate_workbook(SIMULATION, language="English"),
        workflow_results=[],
        parameter_notes=build_parameter_guidance(infer_requested_plan("automatic T2 inversion"), language="English"),
        language="English",
    )

    assert report.status == "success"
    report_text = Path(report.artifacts[0]).read_text(encoding="utf-8")
    assert "T2 Inversion Agent Report" in report_text
    assert "User Goal" in report_text
    assert "T2 反演智能体报告" not in report_text


def test_gaussian_decomposition_does_not_require_removed_numpy_trapz(tmp_path, monkeypatch):
    if hasattr(np, "trapz"):
        monkeypatch.delattr(np, "trapz")

    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path, validation.summary["recommended_time_to_ms_scale"])
    lcurve = run_lcurve(
        Path(repaired.artifacts[0]),
        tmp_path / "lcurve",
        {"num_bins": 60, "alpha_count": 12, "time_to_ms_scale": 1.0},
    )

    gaussian = run_gaussian_peaks(
        Path(lcurve.summary["spectrum_xlsx"]),
        tmp_path / "gaussian",
        {"peak_count": 2},
    )

    assert gaussian.status == "success", gaussian.error
    assert any("__gaussian__" in Path(path).name and Path(path).suffix == ".png" for path in gaussian.artifacts)


def test_interpret_results_reads_lcurve_outputs_and_explains_main_peak(tmp_path):
    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path, validation.summary["recommended_time_to_ms_scale"])
    lcurve = run_lcurve(
        Path(repaired.artifacts[0]),
        tmp_path / "lcurve",
        {"num_bins": 60, "alpha_count": 12, "time_to_ms_scale": 1.0},
    )

    interpretation = interpret_results([lcurve], tmp_path / "interpretation")

    assert interpretation.status == "success"
    assert "最佳平滑因子" in interpretation.message
    assert "主峰" in interpretation.message
    assert Path(interpretation.artifacts[0]).exists()


def test_interpret_results_uses_workflow_summary_paths_when_artifacts_are_filtered(tmp_path):
    spectrum_path = tmp_path / "workflow_spectrum.xlsx"
    summary_path = tmp_path / "workflow_lcurve_summary.csv"
    pd.DataFrame(
        {
            "t2_ms": [1.0, 10.0, 100.0, 1000.0],
            "amplitude": [0.1, 0.3, 1.0, 0.2],
        }
    ).to_excel(spectrum_path, index=False)
    pd.DataFrame(
        {
            "signal_name": ["signal"],
            "best_regularization": [0.001],
            "best_residual_norm": [12.0],
            "best_roughness_norm": [34.0],
        }
    ).to_csv(summary_path, index=False)
    workflow_result = AgentToolResult(
        "success",
        "workflow",
        artifacts=[],
        summary={
            "stage": "full_workflow",
            "spectrum_xlsx": str(spectrum_path),
            "summary_csv": str(summary_path),
        },
    )

    interpretation = interpret_results([workflow_result], tmp_path / "interpretation")

    assert interpretation.status == "success"
    assert interpretation.error is None
    assert "最佳平滑因子" in interpretation.message
    assert "主峰" in interpretation.message
