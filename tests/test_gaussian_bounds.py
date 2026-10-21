import numpy as np

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
