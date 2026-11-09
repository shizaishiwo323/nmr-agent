"""Compatibility wrappers for legacy inversion API.

This module preserves historical function names used by existing notebooks
and scripts, while delegating implementation to the standardized `nmr_t2`
package.

New projects should import from `nmr_t2` directly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from nmr_t2 import NnlsConfig
from nmr_t2.io_utils import cell_to_float, load_decay_table_multi_column, parse_time_cell
from nmr_t2.nnls import build_exponential_kernel, invert_single_signal_nnls, solve_t2_nnls_matlab_compatible


def cell_to_num(value) -> float:
    """Legacy alias of `nmr_t2.io_utils.cell_to_float`."""

    return cell_to_float(value)


def load_spin_echo_data_multi_column(file_path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Legacy loader API.

    Returns
    -------
    time_values:
        Time values in original workbook units (no scaling).
    signal_matrix:
        Matrix with one column per valid signal.
    valid_col_ids:
        Excel 1-based column ids for valid signal columns.
    """

    time_values, signal_matrix, _, col_ids = load_decay_table_multi_column(
        Path(file_path),
        time_to_ms_scale=1.0,
        signal_name_prefix="col",
    )
    return time_values, signal_matrix, col_ids


def create_kernel(t: np.ndarray, t2_bins: np.ndarray) -> np.ndarray:
    """Legacy alias of the exponential kernel constructor."""

    return build_exponential_kernel(t, t2_bins)


def t2nnls_matlab_equivalent(
    d: np.ndarray,
    t: np.ndarray,
    noise: np.ndarray,
    t2: np.ndarray,
    eps: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Legacy API wrapper for MATLAB-compatible NNLS solver."""

    return solve_t2_nnls_matlab_compatible(
        data=d,
        time_ms=t,
        noise=noise,
        t2_bins_ms=t2,
        regularization=float(eps),
    )


def invert_single_column(
    t: np.ndarray,
    y: np.ndarray,
    num_bins: int = 200,
    reg_param: float = 0.01,
    t2_min: Optional[float] = None,
    t2_max: Optional[float] = None,
    noise: Optional[np.ndarray] = None,
):
    """Legacy single-column inversion API.

    Returns `(t2_bins, spectrum, y_fit)` to keep backward compatibility.
    """

    t_arr = np.asarray(t, dtype=float).ravel()
    positive_t = t_arr[np.isfinite(t_arr) & (t_arr > 0)]
    if positive_t.size == 0:
        return np.array([]), np.array([]), np.array([])

    min_t2 = float(t2_min) if t2_min is not None else float(np.min(positive_t))
    max_t2 = float(t2_max) if t2_max is not None else float(np.max(positive_t))

    config = NnlsConfig(
        num_bins=int(num_bins),
        regularization=float(reg_param),
        t2_min_ms=min_t2,
        t2_max_ms=max_t2,
        min_points_after_trim=2,
    )

    result = invert_single_signal_nnls(
        time_ms=t,
        amplitude=y,
        signal_name="legacy_signal",
        config=config,
        noise=noise,
    )
    return result.t2_bins_ms, result.spectrum, result.fit_amplitude


def invert_all_columns(
    t: np.ndarray,
    Y: np.ndarray,
    num_bins: int = 200,
    reg_param: float = 0.01,
    t2_min: Optional[float] = None,
    t2_max: Optional[float] = None,
):
    """Legacy all-column inversion API.

    Returns `(t2_bins_ref, combined_spectrum, y_fit_matrix)`.
    """

    matrix = np.asarray(Y, dtype=float)
    if matrix.ndim != 2:
        raise ValueError("Y must be a 2D array.")

    fit_matrix = np.full_like(matrix, np.nan, dtype=float)
    combined = None
    t2_bins_ref = None

    for column_idx in range(matrix.shape[1]):
        t2_bins, spectrum, fit = invert_single_column(
            t=t,
            y=matrix[:, column_idx],
            num_bins=num_bins,
            reg_param=reg_param,
            t2_min=t2_min,
            t2_max=t2_max,
        )

        if t2_bins.size == 0:
            continue

        fit_matrix[: fit.size, column_idx] = fit
        if combined is None:
            combined = spectrum.copy()
            t2_bins_ref = t2_bins.copy()
        else:
            combined += spectrum

    if combined is None or t2_bins_ref is None:
        raise RuntimeError("Inversion failed: no valid spectrum generated.")

    return t2_bins_ref, combined, fit_matrix
