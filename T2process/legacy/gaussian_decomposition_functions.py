"""Compatibility wrappers for legacy Gaussian decomposition API.

This module keeps historical function names while redirecting implementation
into the standardized `nmr_t2.gaussian` module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from nmr_t2 import GaussianConfig, decompose_spectrum_as_gaussians
from nmr_t2.gaussian import gaussian_component


@dataclass
class GaussianFitResult:
    """Legacy result structure preserved for backward compatibility."""

    peak_num: int
    parameter: np.ndarray
    objectivef: float
    model: np.ndarray
    peak_matrix: np.ndarray
    peak_table: pd.DataFrame
    trial_error: np.ndarray


def gaussian(x: np.ndarray, pos: float, wid: float) -> np.ndarray:
    """Legacy alias for one Gaussian component in log-domain."""

    return gaussian_component(np.asarray(x, dtype=float), float(pos), float(wid))


def fitgauss_residual(lambda_vec: np.ndarray, t2_log: np.ndarray, amp: np.ndarray, peak_num: int) -> Tuple[np.ndarray, np.ndarray, float]:
    """Legacy residual helper used by old notebooks.

    The behavior mirrors the previous implementation: nonlinear parameters are
    provided in `lambda_vec`, while linear heights are solved by least squares.
    """

    t2_log_arr = np.asarray(t2_log, dtype=float).ravel()
    amp_arr = np.asarray(amp, dtype=float).ravel()
    parameter = np.asarray(lambda_vec, dtype=float).ravel()

    basis = np.zeros((t2_log_arr.size, int(peak_num)), dtype=float)
    for idx in range(int(peak_num)):
        basis[:, idx] = gaussian(t2_log_arr, parameter[2 * idx], parameter[2 * idx + 1])

    height, *_ = np.linalg.lstsq(basis, amp_arr, rcond=None)
    height = np.abs(height)
    model = basis @ height
    residual = model - amp_arr
    norm_error = float(np.linalg.norm(residual))
    return residual, height, norm_error


def auto_start_guess(t2_log: np.ndarray, peak_num: int) -> np.ndarray:
    """Legacy auto-initialization helper."""

    t2_log_arr = np.asarray(t2_log, dtype=float).ravel()
    min_t = float(np.min(t2_log_arr))
    max_t = float(np.max(t2_log_arr))
    span = max_t - min_t

    guess = np.zeros(2 * int(peak_num), dtype=float)
    for idx in range(int(peak_num)):
        k_factor = 0.9 + int(peak_num) - (idx + 1)
        center = min_t + span / k_factor
        width = span / int(peak_num)
        guess[2 * idx : 2 * idx + 2] = [center, width]
    return guess


def gaussian_decompose_spectrum(
    t2_bins: np.ndarray,
    spectrum: np.ndarray,
    peak_num: int,
    manual_start: Optional[List[float]] = None,
) -> GaussianFitResult:
    """Legacy decomposition API wrapper.

    Returns a `GaussianFitResult` object with the legacy field names.
    """

    config = GaussianConfig(peak_count=int(peak_num))
    result = decompose_spectrum_as_gaussians(
        t2_bins_ms=t2_bins,
        spectrum=spectrum,
        signal_name="legacy_signal",
        config=config,
        manual_initial_guess=manual_start,
    )

    return GaussianFitResult(
        peak_num=int(result.peak_count),
        parameter=result.parameter,
        objectivef=float(result.objective_value),
        model=result.fitted_spectrum,
        peak_matrix=result.component_matrix,
        peak_table=result.peak_table,
        trial_error=result.trial_errors,
    )
