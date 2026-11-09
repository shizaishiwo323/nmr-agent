from pathlib import Path

from t2_agent.models import AgentToolResult
from t2_agent.tools import interpret_results  # puts T2process on sys.path

from nmr_t2.pipelines import run_lcurve_workbook  # noqa: E402
from nmr_t2.report_figure import load_inversion_report_data, plot_inversion_report  # noqa: E402

DECAY_XLSX = Path(__file__).resolve().parents[1] / "testData" / "ExperimentalDecay.xlsx"


def _lcurve_outputs(tmp_path):
    return run_lcurve_workbook(DECAY_XLSX, tmp_path / "run")


def test_plot_inversion_report_writes_png(tmp_path):
    outputs = _lcurve_outputs(tmp_path)
    figure = plot_inversion_report(
        outputs["spectrum_xlsx"],
        outputs["metrics_xlsx"],
        outputs["trimmed_xlsx"],
        outputs["fit_xlsx"],
        tmp_path / "report.png",
        dpi=100,
    )
    assert figure.exists() and figure.stat().st_size > 0
    data = load_inversion_report_data(
        outputs["spectrum_xlsx"], outputs["metrics_xlsx"], outputs["trimmed_xlsx"], outputs["fit_xlsx"]
    )
    assert data.best_alpha > 0
    assert data.time_ms.size == data.fit_amplitude.size


def test_interpret_results_adds_overview_figure(tmp_path):
    outputs = _lcurve_outputs(tmp_path)
    summary = {key: str(value) for key, value in outputs.items()}
    result = AgentToolResult("success", "ok", artifacts=[str(v) for k, v in outputs.items() if k != "figure_dir"], summary=summary)
    interpretation = interpret_results([result], tmp_path / "interpretation", language="English")
    assert interpretation.status == "success"
    assert interpretation.summary["inversion_report_figure"].endswith(".png")
    assert any(path.endswith(".png") for path in interpretation.artifacts)
    report_text = Path(interpretation.artifacts[0]).read_text(encoding="utf-8")
    assert "Inversion Overview Figure" in report_text
