import numpy as np
import pandas as pd

from t2_agent.reference_inversion import invert_reference_lcurve, lcurve_curvature, regularisation_operator
from t2_agent.tools import run_lcurve


def test_regularisation_operator_matches_reference_stencil():
    reg = regularisation_operator(5)
    assert reg[0].tolist() == [-1, 1, 0, 0, 0]
    assert reg[2].tolist() == [0, 1, -2, 1, 0]
    assert reg[-1].tolist() == [0, 0, 0, 1, -1]


def test_curvature_is_zero_on_a_straight_lcurve():
    k = lcurve_curvature(np.logspace(0, 2, 10), np.logspace(2, 0, 10))
    assert np.allclose(k, 0.0)


def test_reference_inversion_recovers_noise_free_peak():
    t = np.arange(0.0, 1500.0, 5.0)
    s = np.exp(-t / 400.0)
    cfg = {"t2_min_ms": 1.0, "t2_max_ms": 1e5, "num_bins": 150, "alpha_min": 1e-5, "alpha_max": 1e2, "alpha_count": 36}
    r = invert_reference_lcurve(t, s, cfg)
    peak = r["t2_bins_ms"][np.argmax(r["spectrum"])]
    assert 300.0 < peak < 530.0
    assert 0 < r["best"] < cfg["alpha_count"] - 1


def test_run_lcurve_curvature_criterion_writes_standard_outputs(tmp_path):
    t = np.arange(5.0, 1500.0, 5.0)
    wb = tmp_path / "decay.xlsx"
    pd.DataFrame({"time_ms": t, "signal": np.exp(-t / 400.0)}).to_excel(wb, index=False)
    result = run_lcurve(wb, tmp_path / "out", {"criterion": "curvature", "num_bins": 80, "t2_min_ms": 1.0,
                                                "t2_max_ms": 1e5, "alpha_min": 1e-5, "alpha_max": 1e2,
                                                "alpha_count": 36}, language="English")
    assert result.status == "success", result.error
    assert "maximum curvature" in result.message
    summary = pd.read_csv(result.summary["summary_csv"])
    assert summary.loc[0, "selection"] == "max_curvature"
    spectrum = pd.read_excel(result.summary["spectrum_xlsx"])
    assert list(spectrum.columns) == ["t2_ms", "amplitude"]
    assert result.summary["parameters"]["criterion"] == "curvature"
