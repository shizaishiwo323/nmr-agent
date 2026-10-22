import re
from pathlib import Path

import numpy as np

from t2_agent import literature as lit

ROOT = Path(__file__).resolve().parents[1]


def _two_peak_spectrum():
    t2 = np.logspace(-2, 5, 200)
    spectrum = np.exp(-((np.log10(t2) - 1.7) / 0.25) ** 2) + 0.6 * np.exp(-((np.log10(t2) - 2.55) / 0.15) ** 2)
    return t2, spectrum


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
    assert lit.in_text(["Bayer2010SoilNMR"]) == "(Bayer et al., 2010)"
    assert lit.in_text(["NotAKey"]) == ""


def test_class_fractions_add_up():
    t2, spectrum = _two_peak_spectrum()
    parts = lit.class_fractions(t2, spectrum, (10.0, 1000.0))
    assert abs(sum(parts) - 1.0) < 1e-12


def test_measured_rock_findings_drop_generic_caveats():
    t2, spectrum = _two_peak_spectrum()
    facts = lit.AnalysisFacts(workflow="measured", inversion_mode="lcurve", selection_rule="ratio", alpha=1.2, t2_ms=t2, spectrum=spectrum, main_peak_ms=50.0)
    facts.peak_positions_ms = lit.spectrum_peaks(t2, spectrum)
    facts.early_misfit_fraction = 0.024
    facts.gaussian_peaks = [{"position_ms": 3.0, "area_fraction": 0.01}]
    findings = lit.build_findings(facts, "English")
    scenarios = {finding.scenario for finding in findings}
    assert {"regularization_sensitive", "cpmg_sampling_trim", "gaussian_overfit_or_bad_residual", "short_t2_dominant"} <= scenarios
    assert "internal_gradient_shortening" not in scenarios
    text = " ".join(finding.text for finding in findings)
    assert "below the early echoes" in text and "underestimated" in text
    assert "hematite" not in text and "quartz" not in text
    lines, cited = lit.render_section(findings, "English")
    assert "## References" in lines and "Hansen1992LCurve" in cited


def test_soil_findings_give_water_states_and_two_populations():
    t2, spectrum = _two_peak_spectrum()
    facts = lit.AnalysisFacts(workflow="measured", inversion_mode="lcurve", alpha=1.0, t2_ms=t2, spectrum=spectrum, main_peak_ms=350.0)
    facts.sample_context = "NMR of a biomass-containing soil from Vienna"
    facts.peak_positions_ms = lit.spectrum_peaks(t2, spectrum)
    facts.gaussian_peaks = [
        {"position_ms": 50.0, "area_fraction": 0.72, "width_log10": 1.2},
        {"position_ms": 355.0, "area_fraction": 0.28, "width_log10": 0.6},
    ]
    facts.gaussian_r2 = 0.993
    facts.first_echo_ms, facts.echo_spacing_ms = 0.1005, 0.1005
    findings = lit.build_findings(facts, "English")
    scenarios = [finding.scenario for finding in findings]
    assert scenarios[:3] == ["soil_water_state_classes", "two_water_populations", "echo_spacing_lower_bound"]
    tight, loose, bulk_like = lit.class_fractions(t2, spectrum, (60.0, 300.0))
    text = findings[0].text
    assert f"{tight:.0%}" in text and f"{bulk_like:.0%}" in text and "(Bayer et al., 2010)" in text
    assert "hydrogel" in text  # organic context
    assert "intact plant cells" in findings[1].text and "R² = 0.99" in findings[1].text
    assert "lower bounds" in findings[2].text


def test_coupled_ideal_reports_exchange_and_merged_small_pore():
    t2 = np.logspace(-2, 5, 200)
    spectrum = np.exp(-((np.log10(t2) - np.log10(440.0)) / 0.08) ** 2)
    facts = lit.AnalysisFacts(workflow="ideal", inversion_mode="lcurve", alpha=1e-4, t2_ms=t2, spectrum=spectrum, main_peak_ms=440.0, bulk_t2_ms=3000.0)
    facts.peak_positions_ms = lit.spectrum_peaks(t2, spectrum)
    facts.ideal = {
        "config": {"coupled": True, "large_side_um": 20.0, "small_side_um": 8.0, "large_depth_um": 20.0, "small_depth_um": 8.0,
                   "diffusion_um2_per_ms": 2.0, "rho_solid_um_per_ms": 0.005, "bulk_t2_ms": 3000.0,
                   "throat_length_um": 5.0, "throat_width_um": 1.0, "large_water_saturation": 1.0, "small_water_saturation": 1.0},
        "estimated_t2_ms": {"large": 484.0, "small": 214.0},
        "water_configuration": {"large": "full", "small": "full"},
    }
    text = " ".join(finding.text for finding in lit.build_findings(facts, "English"))
    assert "fast-exchange limit of 430 ms" in text and "about 60 ms" in text
    assert "6.0% of the water in the small pore" in text and "17.9 μm" in text
    assert "(Zhou & Zhang, 2025)" in text and "(Zhou et al., 2026)" in text
    assert "refinement" not in text


def test_partial_saturation_capacity_check():
    t2 = np.logspace(-2, 5, 200)
    spectrum = np.exp(-((np.log10(t2) - np.log10(212.0)) / 0.08) ** 2)
    facts = lit.AnalysisFacts(workflow="ideal", inversion_mode="lcurve", alpha=1e-4, t2_ms=t2, spectrum=spectrum, main_peak_ms=212.0)
    facts.peak_positions_ms = lit.spectrum_peaks(t2, spectrum)
    facts.ideal = {
        "config": {"coupled": False, "large_side_um": 20.0, "small_side_um": 8.0, "large_depth_um": 20.0, "small_depth_um": 8.0,
                   "diffusion_um2_per_ms": 2.0, "rho_solid_um_per_ms": 0.005, "bulk_t2_ms": 3000.0,
                   "large_water_saturation": 0.4, "small_water_saturation": 1.0},
        "estimated_t2_ms": {"large": 214.0, "small": 214.0},
        "water_configuration": {"large": "bubble", "small": "full"},
    }
    findings = lit.build_findings(facts, "English")
    text = " ".join(finding.text for finding in findings)
    assert "same peak" in text and "nearly equal estimates" in text
    assert "44% of the saturated signal" in text and "cannot belong to the small pore alone" in text


def test_ct_findings_check_sv_and_unresolved_components():
    t2 = np.logspace(0, np.log10(101950.0), 150)
    spectrum = np.exp(-((np.log10(t2) - np.log10(1900.0)) / 0.16) ** 2)
    labels = np.full((20, 20), 2)
    labels[2:18, 2:10] = 1
    labels[2:18, 10:12] = 3
    facts = lit.AnalysisFacts(workflow="ct", inversion_mode="lcurve", selection_rule="curvature", alpha=1.0, t2_ms=t2, spectrum=spectrum,
                              main_peak_ms=1968.0, bulk_t2_ms=3000.0, rho_um_per_ms=0.005, diffusion_um2_per_ms=2.0)
    facts.peak_positions_ms = lit.spectrum_peaks(t2, spectrum)
    facts.gaussian_peaks = [{"position_ms": 1558.0, "area_fraction": 0.42, "width_log10": 0.23}, {"position_ms": 2278.0, "area_fraction": 0.58, "width_log10": 0.25}]
    facts.decay_end_fraction = 0.46
    facts.ct = {"water_saturation_2d": 0.775, "relaxing_boundary_um": 35915.0, "water_area_um2": 882944.0,
                "pixel_surface_to_volume_per_um": 0.0484, "wall_coverage": lit.wall_coverage_from_labels(labels)}
    scenarios = [finding.scenario for finding in lit.build_findings(facts, "English")]
    assert scenarios[:3] == ["sv_first_moment_check", "rho_calibration_conditioning", "saturation_wall_coverage"]
    assert "unresolved_gaussian_components" in scenarios and "area_above_bulk_t2" in scenarios
    assert lit.wall_coverage_from_labels(labels)["wetted_wall_fraction"] < 1.0
