import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "T2process"))

from nmr_t2.nnls import solve_t2_nnls_matlab_compatible  # noqa: E402


def test_smoothing_keeps_echo_times_aligned():
    # Two equal components; a time shift of the smoothed decay would shrink the 2 ms one by exp(-shift/2).
    time_ms = np.arange(1, 15001) * 0.1
    data = 5000.0 * np.exp(-time_ms / 2.0) + 5000.0 * np.exp(-time_ms / 100.0)
    noise = np.random.default_rng(0).normal(0.0, 1.0, time_ms.size)
    t2 = np.logspace(-1, 4, 120)
    model, synthetic, _ = solve_t2_nnls_matlab_compatible(data, time_ms, noise, t2, regularization=0.1)
    spectrum = model[:-1]
    short = spectrum[t2 < 10].sum() / spectrum.sum()
    assert abs(short - 0.5) < 0.02
    # The fitted first point matches the data at its own time stamp.
    first_time, first_fit = synthetic[0, 0], synthetic[0, 1]
    expected = 5000.0 * np.exp(-first_time / 2.0) + 5000.0 * np.exp(-first_time / 100.0)
    assert abs(first_fit - expected) / expected < 0.01
