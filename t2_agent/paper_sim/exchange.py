"""Effective two-compartment exchange model of the dual-pore case.

Each pore is a well-mixed compartment. In every time step the magnetization of
each pore first relaxes as in the isolated pore (using its FEM signal) and is
then redistributed at the rate k_ex = D_eff / l_c^2, weighted by the water
volume fractions. The step conserves total magnetization and leaves equal
magnetization densities unchanged.
"""

from __future__ import annotations

import numpy as np


def apply_exchange(large: np.ndarray, small: np.ndarray, times_ms: np.ndarray, k_ex_per_ms: float) -> tuple[np.ndarray, np.ndarray]:
    """Exchange-coupled compartment signals from the isolated-pore signals.

    ``large`` and ``small`` are the volume-weighted signals of the two pores
    (their initial values are the water-volume fractions).
    """

    large = np.asarray(large, dtype=float)
    small = np.asarray(small, dtype=float)
    if k_ex_per_ms <= 0 or large[0] <= 1e-12 or small[0] <= 1e-12:
        return large.copy(), small.copy()
    dt = float(np.median(np.diff(times_ms)))
    out_l = np.zeros_like(large)
    out_s = np.zeros_like(small)
    out_l[0], out_s[0] = large[0], small[0]
    v_l0, v_s0 = max(large[0], 1e-12), max(small[0], 1e-12)
    v_tot = v_l0 + v_s0
    k_l_to_s = k_ex_per_ms * v_s0 / v_tot
    k_s_to_l = k_ex_per_ms * v_l0 / v_tot
    for i in range(len(times_ms) - 1):
        m_l = out_l[i] * large[i + 1] / max(large[i], 1e-12)
        m_s = out_s[i] * small[i + 1] / max(small[i], 1e-12)
        flux_l_to_s = dt * k_l_to_s * m_l
        flux_s_to_l = dt * k_s_to_l * m_s
        out_l[i + 1] = max(m_l - flux_l_to_s + flux_s_to_l, 0.0)
        out_s[i + 1] = max(m_s - flux_s_to_l + flux_l_to_s, 0.0)
    return out_l, out_s


def fast_exchange_rate(rates_per_ms: tuple[float, float], weights: tuple[float, float]) -> float:
    """Volume-weighted mean relaxation rate (fast-exchange limit)."""

    return float(weights[0] * rates_per_ms[0] + weights[1] * rates_per_ms[1])
