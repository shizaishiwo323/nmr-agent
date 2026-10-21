"""Publication-style multi-panel figure for a single T2 inversion result.

The figure answers one question: does the selected regularisation reproduce the
measured echo decay, and what T2 spectrum does it return? Four panels share one
palette and read as two columns.

- Left column, time domain: measured decay with the fitted decay, and the
  residual below it on the same time axis.
- Right column, T2 domain: the recovered spectrum, and the L-curve with the
  selected regularisation factor.

Text inside the image is limited to the legends, axis labels, tick labels and
the colour-bar label. Caption-level information (data file, settings, selected
factor) belongs in the report text, not in the image.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

PALETTE = {
    "data": "#8C96A3",
    "main": "#1B4F8C",
    "accent": "#D1601A",
    "axis": "#333333",
}

FIGURE_SIZE_MM = (183.0, 112.0)
FONT_CANDIDATES = ("Arial", "Helvetica", "Liberation Sans", "DejaVu Sans")
_FONT_CACHE: list[str] = []


def publication_font() -> str:
    """First installed sans-serif font; avoids per-glyph lookup warnings on Linux hosts without Arial."""

    if not _FONT_CACHE:
        from .plotting import pick_font_family

        _FONT_CACHE.append(pick_font_family(FONT_CANDIDATES))
    return _FONT_CACHE[0]


def publication_font_family() -> list[str]:
    """Preferred font plus DejaVu Sans, which supplies glyphs such as the subscript in T₂."""

    font = publication_font()
    return [font] if font == "DejaVu Sans" else [font, "DejaVu Sans"]
_MM_PER_INCH = 25.4


@dataclass
class InversionReportData:
    """Arrays needed to draw one inversion report figure."""

    signal_name: str
    time_ms: np.ndarray
    amplitude: np.ndarray
    fit_amplitude: np.ndarray
    sampled_time_ms: np.ndarray
    sampled_residual: np.ndarray
    t2_ms: np.ndarray
    spectrum: np.ndarray
    alpha: np.ndarray
    residual_norm: np.ndarray
    roughness_norm: np.ndarray
    best_index: int

    @property
    def best_alpha(self) -> float:
        return float(self.alpha[self.best_index])

    @property
    def residual(self) -> np.ndarray:
        return self.amplitude - self.fit_amplitude


def _read_sheet(path: Path, signal_name: Optional[str]) -> tuple[str, pd.DataFrame]:
    sheets = pd.read_excel(path, sheet_name=None)
    if signal_name is not None and signal_name in sheets:
        return signal_name, sheets[signal_name]
    name = next(iter(sheets))
    return name, sheets[name]


def load_inversion_report_data(
    spectrum_xlsx: Path,
    metrics_xlsx: Path,
    trimmed_xlsx: Path,
    fit_xlsx: Path,
    signal_name: Optional[str] = None,
) -> InversionReportData:
    """Read the workbooks written by ``run_lcurve_workbook`` for one signal."""

    name, spectrum = _read_sheet(Path(spectrum_xlsx), signal_name)
    _, metrics = _read_sheet(Path(metrics_xlsx), name)
    _, trimmed = _read_sheet(Path(trimmed_xlsx), name)
    _, fit = _read_sheet(Path(fit_xlsx), name)

    used = trimmed["trimmed_time_ms"].notna() & trimmed["trimmed_fit_amplitude"].notna()
    best = np.flatnonzero(metrics["is_best"].to_numpy(dtype=bool))
    if best.size != 1:
        raise ValueError("The metrics sheet must mark exactly one selected regularisation factor.")

    return InversionReportData(
        signal_name=name,
        time_ms=trimmed.loc[used, "trimmed_time_ms"].to_numpy(dtype=float),
        amplitude=trimmed.loc[used, "trimmed_amplitude"].to_numpy(dtype=float),
        fit_amplitude=trimmed.loc[used, "trimmed_fit_amplitude"].to_numpy(dtype=float),
        sampled_time_ms=fit["fit_time_ms"].to_numpy(dtype=float),
        sampled_residual=fit["residual"].to_numpy(dtype=float),
        t2_ms=spectrum["t2_ms"].to_numpy(dtype=float),
        spectrum=spectrum["amplitude"].to_numpy(dtype=float),
        alpha=metrics["alpha_regularization"].to_numpy(dtype=float),
        residual_norm=metrics["residual_norm"].to_numpy(dtype=float),
        roughness_norm=metrics["roughness_norm"].to_numpy(dtype=float),
        best_index=int(best[0]),
    )


def _style_axis(ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.8)
        ax.spines[side].set_color(PALETTE["axis"])
    ax.tick_params(axis="both", which="both", width=0.6, length=2.5, colors=PALETTE["axis"], pad=2)
    ax.tick_params(axis="both", which="minor", length=1.5)


def _log_ticks(ax, axis: str) -> None:
    target = ax.xaxis if axis == "x" else ax.yaxis
    target.set_major_locator(LogLocator(base=10, numticks=12))
    target.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=12))
    target.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    target.set_minor_formatter(NullFormatter())


def _legend(ax, loc: str) -> None:
    ax.legend(loc=loc, frameon=False, handlelength=1.6, handletextpad=0.5, borderaxespad=0.2, labelspacing=0.35)


def build_inversion_report_figure(data: InversionReportData) -> Figure:
    """Draw the four-panel figure and return it without saving."""

    rc = {
        "font.family": publication_font_family(),
        "font.size": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.5,
        "axes.labelcolor": PALETTE["axis"],
        "pdf.fonttype": 42,
    }
    with mpl.rc_context(rc):
        fig = Figure(figsize=(FIGURE_SIZE_MM[0] / _MM_PER_INCH, FIGURE_SIZE_MM[1] / _MM_PER_INCH), facecolor="white")
        grid = GridSpec(
            2,
            2,
            figure=fig,
            width_ratios=[1.0, 1.0],
            height_ratios=[1.35, 1.0],
            left=0.075,
            right=0.985,
            top=0.975,
            bottom=0.105,
            wspace=0.22,
            hspace=0.34,
        )
        ax_decay = fig.add_subplot(grid[0, 0])
        ax_spec = fig.add_subplot(grid[0, 1])
        ax_res = fig.add_subplot(grid[1, 0])
        ax_lc = fig.add_subplot(grid[1, 1])
        for ax in (ax_decay, ax_spec, ax_res, ax_lc):
            _style_axis(ax)

        t_min, t_max = float(data.time_ms.min()), float(data.time_ms.max())

        # Measured decay and fit
        ax_decay.scatter(
            data.time_ms, data.amplitude, s=1.6, color=PALETTE["data"], linewidths=0, rasterized=True,
            label="Measured decay", zorder=2,
        )
        ax_decay.plot(data.time_ms, data.fit_amplitude, color=PALETTE["main"], linewidth=1.2, label="Fitted decay", zorder=3)
        ax_decay.set_xscale("log")
        ax_decay.set_xlim(t_min, t_max)
        ax_decay.set_ylim(0, float(max(data.amplitude.max(), data.fit_amplitude.max())) * 1.04)
        ax_decay.set_xlabel("Echo time (ms)")
        ax_decay.set_ylabel("Signal amplitude (a.u.)")
        _log_ticks(ax_decay, "x")
        _legend(ax_decay, "upper right")

        # Residual: full resolution and the log-sampled points used by the inversion
        ax_res.scatter(
            data.time_ms, data.residual, s=1.6, color=PALETTE["data"], linewidths=0, rasterized=True,
            label="Residual, full resolution", zorder=2,
        )
        ax_res.scatter(
            data.sampled_time_ms, data.sampled_residual, s=4.5, color=PALETTE["main"], linewidths=0,
            label="Residual, inversion sampling", zorder=3,
        )
        ax_res.axhline(0.0, color=PALETTE["axis"], linewidth=0.6, zorder=1)
        ax_res.set_xscale("log")
        ax_res.set_xlim(t_min, t_max)
        ax_res.set_xlabel("Echo time (ms)")
        ax_res.set_ylabel("Residual (a.u.)")
        _log_ticks(ax_res, "x")
        _legend(ax_res, "upper right")

        # T2 spectrum
        positive = data.t2_ms > 0
        ax_spec.fill_between(data.t2_ms[positive], 0, data.spectrum[positive], color=PALETTE["main"], alpha=0.22, linewidth=0)
        ax_spec.plot(data.t2_ms[positive], data.spectrum[positive], color=PALETTE["main"], linewidth=1.3, label="T₂ spectrum")
        ax_spec.set_xscale("log")
        ax_spec.set_xlim(float(data.t2_ms[positive].min()), float(data.t2_ms[positive].max()))
        ax_spec.set_ylim(0, float(data.spectrum.max()) * 1.08)
        ax_spec.set_xlabel("T₂ (ms)")
        ax_spec.set_ylabel("Amplitude (a.u.)")
        _log_ticks(ax_spec, "x")
        _legend(ax_spec, "upper left")

        # L-curve coloured by regularisation factor
        log_alpha = np.log10(data.alpha)
        ax_lc.plot(data.residual_norm, data.roughness_norm, color=PALETTE["data"], linewidth=0.8, zorder=1)
        points = ax_lc.scatter(
            data.residual_norm, data.roughness_norm, c=log_alpha, cmap="cividis", s=7, linewidths=0, zorder=2,
        )
        best = data.best_index
        ax_lc.scatter(
            [data.residual_norm[best]], [data.roughness_norm[best]], marker="*", s=70, color=PALETTE["accent"],
            edgecolors="white", linewidths=0.5, zorder=4, label=f"Selected, α = {data.best_alpha:.3g}",
        )
        ax_lc.set_xscale("log")
        ax_lc.set_yscale("log")
        ax_lc.set_xlabel("Residual norm")
        ax_lc.set_ylabel("Roughness norm")
        _log_ticks(ax_lc, "x")
        _log_ticks(ax_lc, "y")
        _legend(ax_lc, "upper right")

        cax = ax_lc.inset_axes([0.46, 0.50, 0.34, 0.045])
        cbar = fig.colorbar(points, cax=cax, orientation="horizontal")
        cbar.set_label("log₁₀ α", labelpad=1.5)
        cbar.ax.tick_params(width=0.5, length=1.8, labelsize=6, pad=1.5)
        cbar.outline.set_linewidth(0.5)

    fig._t2_report_axes = {"decay": ax_decay, "spectrum": ax_spec, "residual": ax_res, "lcurve": ax_lc, "colorbar": cax}
    return fig


def plot_inversion_report(
    spectrum_xlsx: Path,
    metrics_xlsx: Path,
    trimmed_xlsx: Path,
    fit_xlsx: Path,
    output_path: Path,
    signal_name: Optional[str] = None,
    dpi: int = 600,
) -> Path:
    """Write the report figure as a PNG and return its path."""

    data = load_inversion_report_data(spectrum_xlsx, metrics_xlsx, trimmed_xlsx, fit_xlsx, signal_name)
    fig = build_inversion_report_figure(data)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    return output_path
