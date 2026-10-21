"""Reference L-curve inversion matching the pixel-based image-slice calculation.

The default inversion route trims the decay tail, smooths, subsamples and weights the
residual by an estimated noise level, then selects alpha with the slope-reciprocal ratio.
For noise-free simulated decays these weights flatten the residual norm, so no corner can be
selected. This route instead fits the normalised decay directly,

    min_{p >= 0} ||A p - s||^2 + alpha^2 ||L p||^2,

with second differences in the interior and first differences at the two ends of L, and
selects alpha at the maximum curvature of the log-log L-curve. It reproduces the
inversion of the image-slice reference (advanced_tools/image_slice_simulation.py).
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from nmr_t2.io_utils import timestamped_name  # noqa: E402  (path set up by t2_agent.tools)
from scipy.optimize import nnls  # noqa: E402


def regularisation_operator(n: int) -> np.ndarray:
    reg = np.zeros((n, n))
    for i in range(1, n - 1):
        reg[i, i - 1], reg[i, i], reg[i, i + 1] = 1.0, -2.0, 1.0
    reg[0, 0], reg[0, 1] = -1.0, 1.0
    reg[-1, -2], reg[-1, -1] = 1.0, -1.0
    return reg


def lcurve_curvature(residual: np.ndarray, roughness: np.ndarray) -> np.ndarray:
    """Menger curvature of consecutive points on the log-log L-curve."""

    x = np.log10(np.maximum(residual, 1e-30))
    y = np.log10(np.maximum(roughness, 1e-30))
    curvature = np.zeros_like(x)
    for i in range(1, x.size - 1):
        p1, p2, p3 = (x[i - 1], y[i - 1]), (x[i], y[i]), (x[i + 1], y[i + 1])
        area2 = abs((p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0]))
        side = math.dist(p1, p3) * math.dist(p1, p2) * math.dist(p2, p3)
        curvature[i] = 2.0 * area2 / side if side > 0 else 0.0
    return curvature


def invert_reference_lcurve(time_ms: np.ndarray, signal: np.ndarray, cfg: dict[str, Any]) -> dict[str, Any]:
    t2_bins = np.logspace(np.log10(cfg["t2_min_ms"]), np.log10(cfg["t2_max_ms"]), int(cfg["num_bins"]))
    alphas = np.logspace(np.log10(cfg["alpha_min"]), np.log10(cfg["alpha_max"]), int(cfg["alpha_count"]))
    s0 = float(signal[0])
    norm = signal / s0
    kernel = np.exp(-np.outer(time_ms, 1.0 / t2_bins))
    reg = regularisation_operator(t2_bins.size)
    spectra, residual, roughness = [], [], []
    for alpha in alphas:
        p, _ = nnls(np.vstack([kernel, alpha * reg]), np.concatenate([norm, np.zeros(t2_bins.size)]))
        spectra.append(p)
        residual.append(float(np.linalg.norm(kernel @ p - norm)))
        roughness.append(float(np.linalg.norm(reg @ p)))
    residual, roughness = np.asarray(residual), np.asarray(roughness)
    curvature = lcurve_curvature(residual, roughness)
    best = int(np.argmax(curvature))
    spectrum = spectra[best] * s0
    return {
        "t2_bins_ms": t2_bins, "alphas": alphas, "spectrum": spectrum, "best": best,
        "residual": residual, "roughness": roughness, "curvature": curvature,
        "fit": (kernel @ spectra[best]) * s0,
    }


def run_reference_lcurve_workbook(input_workbook: Path, output_dir: Path, cfg: dict[str, Any],
                                  time_to_ms_scale: float = 1.0) -> dict[str, Path]:
    """Same output roles as nmr_t2.pipelines.run_lcurve_workbook."""

    table = pd.read_excel(input_workbook)
    time_ms = table.iloc[:, 0].to_numpy(dtype=float) * float(time_to_ms_scale)
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir = output_dir / "lcurve_figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(input_workbook).stem[:40]
    spectra, metrics, fits, rows = {}, {}, {}, []
    for k, column in enumerate(table.columns[1:]):
        name = f"col_{k + 2}"
        signal = table[column].to_numpy(dtype=float)
        keep = np.isfinite(time_ms) & np.isfinite(signal)
        t, s = time_ms[keep], signal[keep]
        r = invert_reference_lcurve(t, s, cfg)
        b, a = r["best"], r["alphas"]
        spectra[name] = pd.DataFrame({"t2_ms": r["t2_bins_ms"], "amplitude": r["spectrum"]})
        metrics[name] = pd.DataFrame({
            "alpha_regularization": a, "zeta": r["residual"] ** 2, "eta": r["roughness"] ** 2,
            "residual_norm": r["residual"], "roughness_norm": r["roughness"],
            "slope_reciprocal": a ** 2 * r["roughness"] ** 2 / np.maximum(r["residual"] ** 2, 1e-300),
            "curvature": r["curvature"], "is_best": np.arange(a.size) == b,
        })
        fits[name] = pd.DataFrame({"fit_time_ms": t, "decay_amplitude": s, "fit_amplitude": r["fit"],
                                   "residual": s - r["fit"]})
        fig_path = figure_dir / timestamped_name(f"{name}__lcurve_curvature", "png")
        fig, ax = plt.subplots(figsize=(5.0, 4.0))
        ax.loglog(r["residual"], r["roughness"], "o-", ms=3)
        ax.loglog(r["residual"][b], r["roughness"][b], "r*", ms=12, label=f"max curvature: alpha={a[b]:.3g}")
        ax.set(xlabel="residual norm ||Ap - s||", ylabel="roughness norm ||Lp||", title=f"L-curve: {name}")
        ax.legend()
        fig.tight_layout()
        fig.savefig(fig_path, dpi=200)
        plt.close(fig)
        rows.append({
            "signal_name": name, "best_regularization": float(a[b]), "best_index": b,
            "best_residual_norm": float(r["residual"][b]), "best_roughness_norm": float(r["roughness"][b]),
            "best_slope_reciprocal": float(metrics[name]["slope_reciprocal"].iloc[b]),
            "selection": "max_curvature", "raw_points": int(t.size), "trimmed_points": int(t.size),
            "lcurve_figure": str(fig_path),
        })

    paths = {
        "spectrum_xlsx": output_dir / timestamped_name(f"{stem}__lcurve_spectrum", "xlsx"),
        "metrics_xlsx": output_dir / timestamped_name(f"{stem}__lcurve_metrics", "xlsx"),
        "fit_xlsx": output_dir / timestamped_name(f"{stem}__lcurve_fit", "xlsx"),
        "summary_csv": output_dir / timestamped_name(f"{stem}__lcurve_summary", "csv"),
        "summary_xlsx": output_dir / timestamped_name(f"{stem}__lcurve_summary", "xlsx"),
    }
    for key, sheets in (("spectrum_xlsx", spectra), ("metrics_xlsx", metrics), ("fit_xlsx", fits)):
        with pd.ExcelWriter(paths[key]) as writer:
            for name, frame in sheets.items():
                frame.to_excel(writer, sheet_name=name, index=False)
    summary = pd.DataFrame(rows)
    summary.to_csv(paths["summary_csv"], index=False, encoding="utf-8-sig")
    summary.to_excel(paths["summary_xlsx"], index=False)
    paths["figure_dir"] = figure_dir
    return paths
