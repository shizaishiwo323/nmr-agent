import numpy as np
import pytest

import t2_agent.tools  # noqa: F401  (puts T2process on sys.path)
from nmr_t2.config import GaussianConfig
from nmr_t2.gaussian import decompose_spectrum_as_gaussians


def test_gaussian_centres_stay_inside_the_t2_grid():
    # Two peaks near the upper part of the grid: the automatic guess puts the
    # second centre beyond the grid, which used to trigger an unbounded fallback.
    t2 = np.logspace(-2, 5, 200)
    log_t2 = np.log10(t2)
    spectrum = np.exp(-((log_t2 - np.log10(200.0)) / 0.1) ** 2) * 0.05 + np.exp(-((log_t2 - np.log10(500.0)) / 0.15) ** 2)

    for peak_count in (2, 3):
        result = decompose_spectrum_as_gaussians(t2, spectrum, signal_name="s", config=GaussianConfig(peak_count=peak_count))
        positions = result.peak_table["position_ms"].to_numpy()
        assert np.all(positions >= t2.min()) and np.all(positions <= t2.max())


def test_negligible_gaussian_components_are_dropped():
    t2 = np.logspace(-2, 5, 200)
    spectrum = np.exp(-((np.log10(t2) - np.log10(300.0)) / 0.15) ** 2)  # one peak only
    result = decompose_spectrum_as_gaussians(t2, spectrum, signal_name="s", config=GaussianConfig(peak_count=2))
    assert result.requested_peak_count == 2
    assert (result.peak_table["area_fraction"] >= 0.01).all()
    assert result.peak_table["area_fraction"].sum() == pytest.approx(1.0, abs=1e-6)
    assert result.component_matrix.shape[0] == len(result.peak_table)
    if result.dropped_components is not None and len(result.dropped_components):
        assert (result.dropped_components["area_fraction"] < 0.01).all()
