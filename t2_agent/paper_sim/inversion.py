"""Regularized nonnegative inversions used in the manuscript."""

from __future__ import annotations

import math

import numpy as np
from scipy.optimize import nnls


def invert_t2_controlled(times_ms: np.ndarray, signal: np.ndarray, axis_ms: np.ndarray, alpha: float = 0.08) -> np.ndarray:
    """Controlled cases: fixed alpha, interior second differences (Table 1)."""

    kernel = np.exp(-np.asarray(times_ms)[:, None] / np.asarray(axis_ms)[None, :])
    smooth = np.diff(np.eye(len(axis_ms)), 2, axis=0)
    spectrum = nnls(np.vstack([kernel, alpha * smooth]), np.r_[np.asarray(signal, float), np.zeros(smooth.shape[0])], maxiter=30000)[0]
    return spectrum


def _endpoint_regularizer(n: int) -> np.ndarray:
    reg = np.zeros((n, n))
    for i in range(1, n - 1):
        reg[i, i - 1 : i + 2] = (1.0, -2.0, 1.0)
    reg[0, :2] = (-1.0, 1.0)
    reg[-1, -2:] = (1.0, -1.0)
    return reg


def invert_t2_fixed_slice(times_ms, signal, axis_ms, alpha: float) -> np.ndarray:
    """Slice inversion with a given alpha (coefficients scaled by s(0))."""

    signal = np.asarray(signal, float)
    if np.max(signal) <= 1e-12:
        return np.zeros_like(axis_ms)
    kernel = np.exp(-np.outer(times_ms, 1.0 / np.asarray(axis_ms)))
    reg = _endpoint_regularizer(len(axis_ms))
    spec, _ = nnls(np.vstack([kernel, alpha * reg]), np.concatenate([signal / signal[0], np.zeros(len(axis_ms))]))
    return spec * signal[0]


def invert_t2_lcurve_slice(times_ms, signal, axis_ms, alphas: np.ndarray | None = None):
    """Slice inversion with alpha at the maximum curvature of the L-curve (Hansen, 1992)."""

    signal = np.asarray(signal, float)
    alphas = np.logspace(-5, 2, 36) if alphas is None else np.asarray(alphas, float)
    norm = signal / signal[0]
    kernel = np.exp(-np.outer(times_ms, 1.0 / np.asarray(axis_ms)))
    reg = _endpoint_regularizer(len(axis_ms))
    spectra, residuals, roughness = [], [], []
    for alpha in alphas:
        spec, _ = nnls(np.vstack([kernel, alpha * reg]), np.concatenate([norm, np.zeros(len(axis_ms))]))
        spectra.append(spec)
        residuals.append(float(np.linalg.norm(kernel @ spec - norm)))
        roughness.append(float(np.linalg.norm(reg @ spec)))
    x = np.log10(np.maximum(residuals, 1e-30))
    y = np.log10(np.maximum(roughness, 1e-30))
    curvature = np.zeros_like(alphas)
    for i in range(1, len(alphas) - 1):
        x1, y1, x2, y2, x3, y3 = x[i - 1], y[i - 1], x[i], y[i], x[i + 1], y[i + 1]
        area2 = abs((x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1))
        side = math.dist((x1, y1), (x3, y3)) * math.dist((x1, y1), (x2, y2)) * math.dist((x2, y2), (x3, y3))
        curvature[i] = 2.0 * area2 / side if side > 0 else 0.0
    best = int(np.argmax(curvature))
    metrics = {"alpha": alphas, "residual_norm": np.asarray(residuals), "roughness_norm": np.asarray(roughness),
               "curvature": curvature, "best_index": best}
    return spectra[best] * signal[0], float(alphas[best]), metrics


def second_difference(size: int) -> np.ndarray:
    return _endpoint_regularizer(size) if size >= 2 else np.zeros((size, size))


def _invert_separable(signal, k_row, k_col, alpha, normalization):
    normalized = np.asarray(signal, float) / normalization
    n1, n2 = k_row.shape[1], k_col.shape[1]
    design = np.kron(k_col, k_row)
    reg = np.vstack((np.kron(np.eye(n2), second_difference(n1)), np.kron(second_difference(n2), np.eye(n1))))
    vector, _ = nnls(np.vstack((design, alpha * reg)), np.concatenate((normalized.ravel(order="F"), np.zeros(reg.shape[0]))), maxiter=10 * n1 * n2)
    distribution = vector.reshape((n1, n2), order="F")
    reconstructed = k_row @ distribution @ k_col.T
    return distribution, float(np.linalg.norm(reconstructed - normalized) / np.linalg.norm(normalized))


def invert_dt2(signal, b_axis, te_axis_ms, d_axis, t2_axis_ms, alpha: float = 0.025):
    """D-T2 map f(D, T2) from S(b, TE)."""

    signal = np.asarray(signal, float)
    if signal[0, 0] <= 0:
        raise ValueError("D-T2 normalization signal must be positive")
    k_d = np.exp(-np.outer(b_axis, d_axis))
    k_t = np.exp(-np.outer(te_axis_ms, 1.0 / np.asarray(t2_axis_ms)))
    distribution, misfit = _invert_separable(signal, k_d, k_t, alpha, float(signal[0, 0]))
    peak = np.unravel_index(np.argmax(distribution), distribution.shape)
    return distribution, {"alpha": alpha, "data_relative_l2": misfit, "peak_D_um2_per_ms": float(d_axis[peak[0]]),
                          "peak_T2_ms": float(t2_axis_ms[peak[1]])}


def invert_t1t2(signal, recovery_ms, detection_ms, t1_axis_ms, t2_axis_ms, alpha: float = 0.025):
    """T1-T2 map f(T1, T2) from S(TR, TE) with the saturation-recovery kernel."""

    signal = np.asarray(signal, float)
    k1 = 1.0 - np.exp(-np.outer(recovery_ms, 1.0 / np.asarray(t1_axis_ms)))
    k2 = np.exp(-np.outer(detection_ms, 1.0 / np.asarray(t2_axis_ms)))
    distribution, misfit = _invert_separable(signal, k1, k2, alpha, float(np.max(signal)))
    peak = np.unravel_index(np.argmax(distribution), distribution.shape)
    return distribution, {"alpha": alpha, "data_relative_l2": misfit, "peak_T1_ms": float(t1_axis_ms[peak[0]]),
                          "peak_T2_ms": float(t2_axis_ms[peak[1]])}


def peak_position(axis: np.ndarray, spectrum: np.ndarray) -> float:
    return float(np.asarray(axis)[int(np.argmax(spectrum))])
