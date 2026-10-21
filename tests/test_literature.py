import re
from pathlib import Path

import numpy as np

from t2_agent import literature as lit

ROOT = Path(__file__).resolve().parents[1]


def test_every_key_used_by_the_templates_has_a_verified_reference():
    source = (ROOT / "t2_agent" / "literature.py").read_text(encoding="utf-8")
    keys = set(re.findall(r'"([A-Z][A-Za-z]+\d{4}[A-Za-z0-9]*)"', source))
    refs = lit.load_references()
    missing = sorted(key for key in keys if key not in refs)
    assert not missing, missing
    for key in keys:
        assert refs[key]["reference_agu"].count("(") >= 1 and refs[key]["in_text"]


def test_in_text_follows_agu_author_rules():
    assert lit.in_text(["Hansen1992LCurve"]) == "(Hansen, 1992)"
    assert lit.in_text(["KleinbergHorsfield1990TransverseRelaxation"]) == "(Kleinberg & Horsfield, 1990)"
    assert lit.in_text(["Kleinberg1994RelaxationMechanism"]) == "(Kleinberg et al., 1994)"
    assert lit.in_text(["NotAKey"]) == ""


def test_findings_follow_the_numbers():
    t2 = np.logspace(-2, 5, 200)
    spectrum = np.exp(-((np.log10(t2) - 2.0) / 0.2) ** 2) + 0.5 * np.exp(-((np.log10(t2) - 0.5) / 0.2) ** 2)
    facts = lit.AnalysisFacts(workflow="measured", inversion_mode="lcurve", selection_rule="ratio", alpha=1.2, t2_ms=t2, spectrum=spectrum, main_peak_ms=100.0)
    facts.peak_positions_ms = lit.spectrum_peaks(t2, spectrum)
    facts.early_misfit_fraction = 0.024
    facts.gaussian_peaks = [{"position_ms": 3.0, "area_fraction": 0.01}]
    findings = lit.build_findings(facts, "中文")
    scenarios = {finding.scenario for finding in findings}
    assert {"regularization_sensitive", "cpmg_sampling_trim", "multimodal_spectrum", "gaussian_overfit_or_bad_residual", "internal_gradient_shortening"} <= scenarios
    lines, cited = lit.render_section(findings, "中文")
    assert "## 参考文献" in lines and "Hansen1992LCurve" in cited
    assert any("+2.4%" in line for line in lines)


def test_ideal_findings_report_regime_coupling_and_saturation():
    facts = lit.AnalysisFacts(workflow="ideal", inversion_mode="lcurve", alpha=1e-4, t2_ms=np.logspace(-2, 5, 50), spectrum=np.ones(50))
    facts.ideal = {
        "config": {"coupled": True, "large_side_um": 20.0, "diffusion_um2_per_ms": 2.0, "rho_solid_um_per_ms": 0.005, "throat_length_um": 5.0, "throat_width_um": 1.0, "large_water_saturation": 0.7, "small_water_saturation": 1.0},
        "estimated_t2_ms": {"large": 300.0, "small": 214.0},
        "water_configuration": {"large": "bubble", "small": "full"},
    }
    text = " ".join(finding.text for finding in lit.build_findings(facts, "English"))
    assert "fast-diffusion regime" in text and "throat" in text and "central gas bubble" in text
    assert "(Mohnke et al., 2015)" in text
