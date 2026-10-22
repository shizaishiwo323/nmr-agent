"""Five-panel report figure for simulated NMR runs (segmented CT slice or ideal geometry).

The figure answers one question: what water domain was simulated, and which T2
spectrum does its decay give? Panels, left to right and top to bottom:

1. three-phase map (solid, water, gas);
2. water-filled domain used by the forward model;
3. local pore-size distribution of the pore space and of the water domain;
4. simulated echo envelope with the spectral reconstruction;
5. peak-normalized T2 spectrum (with Gaussian components, or the fast-diffusion
   estimates of the ideal pores).

Text in the image is limited to legends and axis labels; panel letters and
titles belong in the caption.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

OUTSIDE, WATER, SOLID, AIR = 0, 1, 2, 3
COLORS = {
    "solid": "#9AA3AE",
    "water": "#3F7FB5",
    "air": "#EAD7A4",
    "outside": "#FFFFFF",
    "line": "#1F3B57",
    "accent": "#C8642A",
    "mesh_fill": "#CFE1F1",
    "mesh_edge": "#2E6699",
    "neutral": "#6E7781",
    "axis": "#333333",
}
FIGURE_SIZE_MM = (183.0, 128.0)
_MM_PER_INCH = 25.4


@dataclass
class SimulationFigureData:
    phase_map: np.ndarray  # OUTSIDE / WATER / SOLID / AIR codes, row 0 at the top
    pixel_um: float
    time_ms: np.ndarray
    signal: np.ndarray  # normalized to the first echo
    recon_time_ms: np.ndarray | None
    recon_signal: np.ndarray | None
    t2_ms: np.ndarray
    spectrum: np.ndarray
    alpha: float | None = None
    inversion_label: str = "L-curve"
    gaussian_components: list[np.ndarray] = field(default_factory=list)
    gaussian_positions_ms: list[float] = field(default_factory=list)
    estimates_ms: dict[str, float] = field(default_factory=dict)
    pore_diameter_um: np.ndarray | None = None
    water_diameter_um: np.ndarray | None = None
    mesh_points_um: np.ndarray | None = None  # node coordinates in the phase-map frame (origin bottom left)
    mesh_triangles: np.ndarray | None = None


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def local_diameter_px(mask: np.ndarray, max_radii: int = 80) -> np.ndarray:
    """Local thickness: diameter of the largest inscribed disk covering each pixel (0 outside)."""

    from scipy.ndimage import distance_transform_edt

    mask = np.asarray(mask, dtype=bool)
    thickness = np.zeros(mask.shape, dtype=float)
    if not mask.any():
        return thickness
    distance = distance_transform_edt(mask)
    r_max = float(distance.max())
    radii = np.arange(1.0, math.floor(r_max) + 1.0) if r_max < max_radii else np.linspace(1.0, r_max, max_radii)
    if radii.size == 0:
        thickness[mask] = 2.0 * distance[mask]
        return thickness
    for radius in radii:  # ascending, so each pixel keeps the largest covering disk
        centres = distance >= radius
        if not centres.any():
            break
        covered = distance_transform_edt(~centres) <= radius
        thickness[covered & mask] = 2.0 * radius
    unassigned = mask & (thickness == 0)
    thickness[unassigned] = 2.0 * np.maximum(distance[unassigned], 0.5)
    return thickness


def rasterize_ideal_geometry(config: Any, pixel_um: float | None = None) -> tuple[np.ndarray, float]:
    """Phase map of the ideal triangle pair on a fine grid (solid around the pores)."""

    from matplotlib.path import Path as MplPath

    from . import ideal_workflow as iw

    shift = config.throat_length_um / 2.0 if config.coupled else 0.0
    gap = 0.0 if config.coupled else max(2.0, 0.15 * config.large_side_um)
    pores = [
        (config.large_side_um, config.large_water_saturation, False, shift + gap / 2.0),
        (config.small_side_um, config.small_water_saturation, True, -shift - gap / 2.0),
    ]
    top = shift + gap / 2.0 + config.large_side_um * math.sqrt(3.0) / 2.0
    bottom = -shift - gap / 2.0 - config.small_side_um * math.sqrt(3.0) / 2.0
    margin = 0.08 * config.large_side_um
    x0, x1 = -config.large_side_um / 2.0 - margin, config.large_side_um / 2.0 + margin
    y0, y1 = bottom - margin, top + margin
    pixel = pixel_um or max((x1 - x0), (y1 - y0)) / 600.0
    xs = np.arange(x0 + pixel / 2.0, x1, pixel)
    ys = np.arange(y1 - pixel / 2.0, y0, -pixel)  # row 0 at the top
    grid_x, grid_y = np.meshgrid(xs, ys)
    points = np.column_stack([grid_x.ravel(), grid_y.ravel()])
    phase = np.full(grid_x.shape, SOLID, dtype=np.uint8)

    def inside(polygon) -> np.ndarray:
        return MplPath(np.asarray(polygon)).contains_points(points).reshape(grid_x.shape)

    for side, saturation, inverted, y_shift in pores:
        outline = iw._triangle_vertices(side, inverted, y_shift)
        water_polys, gas_polys = iw._water_patches(side, saturation, inverted, y_shift)
        pore = inside(outline)
        kind = iw.water_configuration(saturation)
        if kind == "full":
            phase[pore] = WATER
        elif kind == "bubble":
            phase[pore] = WATER
            for gas in gas_polys:
                phase[inside(gas)] = AIR
        else:
            phase[pore] = AIR
            for water in water_polys:
                phase[inside(water) & pore] = WATER
    if config.coupled:
        half_w, half_l = config.throat_width_um / 2.0, config.throat_length_um / 2.0
        throat = (np.abs(grid_x) <= half_w) & (np.abs(grid_y) <= half_l)
        phase[throat & (phase == SOLID)] = WATER
    return phase, float(pixel)


def ideal_frame_origin(config: Any, phase_shape: tuple[int, int], pixel_um: float) -> tuple[float, float]:
    """Native (x, y) of the bottom-left corner of the rasterized ideal phase map."""

    shift = config.throat_length_um / 2.0 if config.coupled else 0.0
    gap = 0.0 if config.coupled else max(2.0, 0.15 * config.large_side_um)
    top = shift + gap / 2.0 + config.large_side_um * math.sqrt(3.0) / 2.0
    margin = 0.08 * config.large_side_um
    x0 = -config.large_side_um / 2.0 - margin
    y_top = top + margin
    return x0, y_top - phase_shape[0] * pixel_um


def _mesh_arrays(mesh) -> tuple[np.ndarray, np.ndarray]:
    points = np.asarray([[node.pos().x(), node.pos().y()] for node in mesh.nodes()], dtype=float)
    triangles = np.asarray([[node.id() for node in cell.nodes()] for cell in mesh.cells() if cell.nodeCount() == 3], dtype=np.int64)
    return points, triangles


def load_mesh_arrays(bms_path: Path) -> tuple[np.ndarray, np.ndarray]:
    import pygimli as pg

    return _mesh_arrays(pg.load(str(bms_path)))


def ideal_mesh_arrays(config: Any) -> tuple[np.ndarray, np.ndarray]:
    """Re-create the ideal-geometry mesh with the simulation's own mesher and settings.

    The coupled run saves one mesh; the uncoupled run meshes the two pores
    separately, so both are rebuilt here and placed with the figure's gap.
    """

    from . import simulation_2d as sim

    mt = sim.mt
    if mt is None:
        raise RuntimeError("pyGIMLi meshtools are not available")
    large_air = (1.0 - config.large_water_saturation) * math.sqrt(3.0) / 4.0 * config.large_side_um**2
    small_air = (1.0 - config.small_water_saturation) * math.sqrt(3.0) / 4.0 * config.small_side_um**2
    area = max(float(config.ideal_mesh_area_um2), 1e-6)
    if config.coupled:
        half_l = config.throat_length_um / 2.0
        large = sim.create_ideal_triangle_pore_geometry(config.large_side_um, large_air, is_inverted=False, y_shift_um=half_l)
        small = sim.create_ideal_triangle_pore_geometry(config.small_side_um, small_air, is_inverted=True, y_shift_um=-half_l)
        throat = mt.createRectangle(start=[-config.throat_width_um / 2.0, -half_l], end=[config.throat_width_um / 2.0, half_l])
        return _mesh_arrays(mt.createMesh(large + throat + small, area=area, quality=34.0))
    gap = max(2.0, 0.15 * config.large_side_um)
    pieces = []
    for side, air, inverted, offset in ((config.large_side_um, large_air, False, gap / 2.0), (config.small_side_um, small_air, True, -gap / 2.0)):
        geometry = sim.create_ideal_triangle_pore_geometry(side, air, is_inverted=inverted, y_shift_um=offset)
        if geometry is not None:
            pieces.append(_mesh_arrays(mt.createMesh(geometry, area=area, quality=34.0)))
    points = np.vstack([piece[0] for piece in pieces])
    offsets = np.cumsum([0] + [piece[0].shape[0] for piece in pieces[:-1]])
    triangles = np.vstack([piece[1] + offset for piece, offset in zip(pieces, offsets)])
    return points, triangles


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def _first_sheet(path: Path) -> pd.DataFrame:
    return next(iter(pd.read_excel(path, sheet_name=None).values()))


def _decay_columns(table: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    time_col = "time_ms" if "time_ms" in table.columns else table.columns[0]
    value_col = [col for col in table.columns if col != time_col][0]
    return table[time_col].to_numpy(float), table[value_col].to_numpy(float)


def load_inversion_series(
    decay_xlsx: Path,
    spectrum_xlsx: Path,
    fit_xlsx: Path | None = None,
    summary_csv: Path | None = None,
    gaussian_fit_xlsx: Path | None = None,
) -> dict[str, Any]:
    time_ms, raw = _decay_columns(_first_sheet(Path(decay_xlsx)))
    scale = raw[0] if raw.size and raw[0] != 0 else 1.0
    series: dict[str, Any] = {"time_ms": time_ms, "signal": raw / scale, "recon_time_ms": None, "recon_signal": None}
    if fit_xlsx and Path(fit_xlsx).exists():
        fit = _first_sheet(Path(fit_xlsx))
        if {"fit_time_ms", "fit_amplitude"} <= set(fit.columns):
            fit_time = fit["fit_time_ms"].to_numpy(float)
            fit_amp = fit["fit_amplitude"].to_numpy(float)
            # The fit is on the inversion's own scale; match it to the decay at the first sampled echo.
            reference = np.interp(fit_time[0], time_ms, raw) / scale
            fit_scale = fit_amp[0] / reference if reference else 1.0
            series["recon_time_ms"] = fit_time
            series["recon_signal"] = fit_amp / fit_scale if fit_scale else fit_amp
    spectrum = _first_sheet(Path(spectrum_xlsx))
    t2 = spectrum["t2_ms"].to_numpy(float)
    amp = spectrum["amplitude"].to_numpy(float)
    peak = float(np.nanmax(amp)) if amp.size and np.nanmax(amp) > 0 else 1.0
    series.update({"t2_ms": t2, "spectrum": amp / peak})
    if summary_csv and Path(summary_csv).exists():
        row = pd.read_csv(summary_csv).iloc[0]
        value = row.get("best_regularization", row.get("regularization"))
        series["alpha"] = float(value) if value is not None and np.isfinite(value) else None
    components: list[np.ndarray] = []
    if gaussian_fit_xlsx and Path(gaussian_fit_xlsx).exists():
        fit = _first_sheet(Path(gaussian_fit_xlsx))
        component_cols = [col for col in fit.columns if str(col).startswith("component_")]
        if component_cols and "t2_ms" in fit.columns:
            grid = fit["t2_ms"].to_numpy(float)
            for col in component_cols:
                values = np.interp(np.log10(t2), np.log10(grid), fit[col].to_numpy(float), left=0.0, right=0.0)
                components.append(values / peak)
    series["gaussian_components"] = components
    return series


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------


def spectrum_window(
    t2_ms: np.ndarray,
    spectrum: np.ndarray,
    extra_ms: list[float] | None = None,
    left_decades: int = 4,
) -> tuple[float, float]:
    """Decade-snapped T2 range around the non-zero spectrum and any marked estimates.

    Several empty decades are kept on the short-T2 side so the spectrum sits in
    the right part of the panel and the legend has a free upper-left corner.
    """

    positive = t2_ms > 0
    grid_lo, grid_hi = float(t2_ms[positive].min()), float(t2_ms[positive].max())
    support = t2_ms[positive & (spectrum > 1e-3 * np.nanmax(spectrum))]
    values = list(support) + [value for value in (extra_ms or []) if value and value > 0]
    if not values:
        return grid_lo, grid_hi
    lo = 10 ** (math.floor(math.log10(min(values))) - left_decades)
    hi = 10 ** (math.ceil(math.log10(max(values))) + 1)
    return max(grid_lo, lo), min(grid_hi, hi)


def legend_corner(t2_ms: np.ndarray, spectrum: np.ndarray, window: tuple[float, float]) -> str:
    """Upper corner on the opposite side of the main peak (log position in the window)."""

    peak = float(t2_ms[int(np.nanargmax(spectrum))])
    fraction = (math.log10(peak) - math.log10(window[0])) / max(math.log10(window[1]) - math.log10(window[0]), 1e-9)
    return "upper left" if fraction >= 0.5 else "upper right"


def _style(ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.8)
        ax.spines[side].set_color(COLORS["axis"])
    ax.tick_params(axis="both", which="both", width=0.6, length=2.5, colors=COLORS["axis"], pad=2)
    ax.tick_params(axis="both", which="minor", length=1.5)


def _legend(ax, loc: str, **kwargs) -> None:
    ax.legend(loc=loc, frameon=False, handlelength=1.4, handletextpad=0.5, borderaxespad=0.3, labelspacing=0.3, **kwargs)


def _phase_rgb(phase: np.ndarray, water_only: bool = False) -> np.ndarray:
    from matplotlib.colors import to_rgb

    rgb = np.ones(phase.shape + (3,), dtype=float)
    if water_only:
        rgb[phase == WATER] = to_rgb(COLORS["water"])
        return rgb
    for code, key in ((SOLID, "solid"), (WATER, "water"), (AIR, "air"), (OUTSIDE, "outside")):
        rgb[phase == code] = to_rgb(COLORS[key])
    return rgb


def build_simulation_figure(data: SimulationFigureData):
    import matplotlib as mpl
    from matplotlib.figure import Figure
    from matplotlib.gridspec import GridSpec
    from matplotlib.patches import Patch
    from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

    from nmr_t2.report_figure import publication_font_family

    rc = {
        "font.family": publication_font_family(),
        "font.size": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.5,
        "axes.labelcolor": COLORS["axis"],
        "pdf.fonttype": 42,
    }
    rows, cols = data.phase_map.shape
    extent_um = (cols * data.pixel_um, rows * data.pixel_um)
    use_mm = max(extent_um) >= 1000.0
    unit = 1000.0 if use_mm else 1.0
    unit_label = "mm" if use_mm else "μm"
    extent = (0.0, extent_um[0] / unit, 0.0, extent_um[1] / unit)

    with mpl.rc_context(rc):
        fig = Figure(figsize=(FIGURE_SIZE_MM[0] / _MM_PER_INCH, FIGURE_SIZE_MM[1] / _MM_PER_INCH), facecolor="white")
        grid = GridSpec(2, 6, figure=fig, height_ratios=[1.0, 0.95], left=0.07, right=0.985, top=0.955, bottom=0.085, wspace=1.15, hspace=0.48)
        ax_phase = fig.add_subplot(grid[0, 0:2])
        ax_water = fig.add_subplot(grid[0, 2:4])
        ax_size = fig.add_subplot(grid[0, 4:6])
        ax_decay = fig.add_subplot(grid[1, 0:3])
        ax_spec = fig.add_subplot(grid[1, 3:6])
        for ax in (ax_phase, ax_water, ax_size, ax_decay, ax_spec):
            _style(ax)

        # 1. Three-phase map
        ax_phase.imshow(_phase_rgb(data.phase_map), extent=extent, origin="upper", interpolation="nearest")
        present = {code for code in np.unique(data.phase_map)}
        handles = [Patch(facecolor=COLORS["solid"], label="Solid"), Patch(facecolor=COLORS["water"], label="Water")]
        if AIR in present:
            handles.append(Patch(facecolor=COLORS["air"], label="Gas"))
        ax_phase.legend(handles=handles, loc="lower left", frameon=True, framealpha=0.9, edgecolor="none", handlelength=1.0, borderpad=0.3, labelspacing=0.25)
        ax_phase.set_xlabel(f"Width ({unit_label})")
        ax_phase.set_ylabel(f"Height ({unit_label})")
        ax_phase.set_aspect("equal", adjustable="datalim")

        # 2. Water-filled domain as meshed for the forward model
        if data.mesh_points_um is not None and data.mesh_triangles is not None and len(data.mesh_triangles):
            from matplotlib.tri import Triangulation

            mesh = Triangulation(data.mesh_points_um[:, 0] / unit, data.mesh_points_um[:, 1] / unit, data.mesh_triangles)
            ax_water.tripcolor(mesh, np.zeros(len(data.mesh_triangles)), cmap=mpl.colors.ListedColormap([COLORS["mesh_fill"]]), shading="flat", edgecolors="none", rasterized=True)
            width = 0.25 if len(data.mesh_triangles) < 15000 else 0.12
            ax_water.triplot(mesh, color=COLORS["mesh_edge"], linewidth=width, rasterized=True)
            # Same view as panel (a) through the data limits, so the equal aspect needs no fixed limits.
            ax_water.update_datalim([(extent[0], extent[2]), (extent[1], extent[3])])
            ax_water.margins(0.0)
            ax_water.autoscale_view()
        else:
            ax_water.imshow(_phase_rgb(data.phase_map, water_only=True), extent=extent, origin="upper", interpolation="nearest")
        ax_water.set_xlabel(f"Width ({unit_label})")
        ax_water.set_aspect("equal", adjustable="datalim")

        # 3. Local pore-size distribution (area weighted)
        pores = data.pore_diameter_um if data.pore_diameter_um is not None else np.array([])
        water = data.water_diameter_um if data.water_diameter_um is not None else np.array([])
        if pores.size:
            upper = float(np.percentile(pores, 99.5))
            bins = np.linspace(0.0, max(upper, 1e-6) * 1.02, 13)
            weights = np.full(pores.size, 100.0 / pores.size)
            ax_size.hist(pores, bins=bins, weights=weights, color=COLORS["water"] if not water.size or water.size == pores.size else COLORS["solid"], edgecolor="white", linewidth=0.6, label="Pore space")
            if water.size and water.size != pores.size:
                ax_size.hist(water, bins=bins, weights=np.full(water.size, 100.0 / pores.size), histtype="step", color=COLORS["water"], linewidth=1.2, label="Water-filled")
            ax_size.set_xlim(0.0, bins[-1])
            ax_size.set_ylim(0.0, ax_size.get_ylim()[1] * 1.32)  # headroom keeps the legend off the bars
            _legend(ax_size, "upper right")
        ax_size.set_xlabel("Local pore diameter (μm)")
        ax_size.set_ylabel("Pore area fraction (%)")

        # 4. Echo envelope and reconstruction
        ax_decay.plot(data.time_ms, data.signal, color=COLORS["line"], linewidth=1.2, label="Simulated echo envelope", zorder=2)
        if data.recon_time_ms is not None and data.recon_signal is not None and data.recon_time_ms.size:
            picks = np.unique(np.linspace(0, data.recon_time_ms.size - 1, 18).round().astype(int))
            ax_decay.plot(data.recon_time_ms[picks], data.recon_signal[picks], linestyle="none", marker="o", markersize=3.6, markerfacecolor="white", markeredgecolor=COLORS["accent"], markeredgewidth=0.9, label="Spectral reconstruction", zorder=3)
        ax_decay.set_xlim(0.0, float(data.time_ms.max()))
        ax_decay.set_ylim(0.0, 1.05)
        ax_decay.set_xlabel("Echo time (ms)")
        ax_decay.set_ylabel("Normalized signal")
        _legend(ax_decay, "upper right")

        # 5. T2 spectrum
        label = data.inversion_label + (f", α = {data.alpha:.3g}" if data.alpha is not None else "")
        window = spectrum_window(data.t2_ms, data.spectrum, list(data.estimates_ms.values()))
        # Draw only the visible window: clipped-away segments along y = 0 would
        # otherwise run under the neighbouring tick labels in vector output.
        shown = (data.t2_ms >= window[0]) & (data.t2_ms <= window[1])
        ax_spec.plot(data.t2_ms[shown], data.spectrum[shown], color=COLORS["line"], linewidth=1.3, label=label, zorder=3)
        styles = ["--", ":", "-."]
        for idx, component in enumerate(data.gaussian_components):
            position = data.gaussian_positions_ms[idx] if idx < len(data.gaussian_positions_ms) else None
            name = f"Gaussian {idx + 1}" + (f" ({position:.0f} ms)" if position and position >= 10 else f" ({position:.3g} ms)" if position else "")
            ax_spec.plot(data.t2_ms[shown], component[shown], color=COLORS["accent"], linewidth=0.9, linestyle=styles[idx % 3], label=name, zorder=2)
        for name, value in data.estimates_ms.items():
            # Estimate markers stop below the legend band.
            ax_spec.axvline(value, ymax=0.6, color=COLORS["neutral"], linewidth=0.8, linestyle="--" if name.startswith("Large") else ":", label=f"{name} ({value:.0f} ms)", zorder=1)
        ax_spec.set_xscale("log")
        ax_spec.set_xlim(*window)
        ax_spec.set_ylim(0.0, 1.12)
        ax_spec.xaxis.set_major_locator(LogLocator(base=10, numticks=12))
        ax_spec.xaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=12))
        ax_spec.xaxis.set_minor_formatter(NullFormatter())
        ax_spec.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
        ax_spec.set_xlabel("T₂ (ms)")
        ax_spec.set_ylabel("Peak-normalized amplitude")
        _legend(ax_spec, legend_corner(data.t2_ms, data.spectrum, window))

        for letter, ax in zip("abcde", (ax_phase, ax_water, ax_size, ax_decay, ax_spec)):
            add_panel_label(fig, ax, letter)

    fig._simulation_axes = {"phase": ax_phase, "water": ax_water, "size": ax_size, "decay": ax_decay, "spectrum": ax_spec}
    return fig


def add_panel_label(fig, ax, letter: str) -> None:
    """Bold "(a)" just above the top-left corner, at a fixed point offset for every panel."""

    from matplotlib.transforms import offset_copy

    transform = offset_copy(ax.transAxes, fig=fig, x=-2.0, y=5.0, units="points")
    ax.text(0.0, 1.0, f"({letter})", transform=transform, ha="left", va="bottom", fontsize=8, fontweight="bold", color=COLORS["axis"])


def _with_distributions(data: SimulationFigureData) -> SimulationFigureData:
    pore_mask = (data.phase_map == WATER) | (data.phase_map == AIR)
    water_mask = data.phase_map == WATER
    pore_d = local_diameter_px(pore_mask)
    water_d = local_diameter_px(water_mask)
    data.pore_diameter_um = pore_d[pore_mask] * data.pixel_um
    data.water_diameter_um = water_d[water_mask] * data.pixel_um
    return data


def ct_figure_data(labels_npy: Path, pixel_um: float, series: dict[str, Any], mesh_bms: Path | None = None) -> SimulationFigureData:
    phase = np.load(labels_npy)
    data = SimulationFigureData(phase_map=phase, pixel_um=float(pixel_um), **_series_kwargs(series))
    if mesh_bms is not None and Path(mesh_bms).exists():
        # The CT mesh is already in micrometres with its origin at the bottom-left of the cropped slice.
        points, triangles = load_mesh_arrays(Path(mesh_bms))
        data.mesh_points_um, data.mesh_triangles = points, water_triangles(points, triangles, phase, float(pixel_um))
    return _with_distributions(data)


def water_triangles(points: np.ndarray, triangles: np.ndarray, phase: np.ndarray, pixel_um: float) -> np.ndarray:
    """Keep the triangles whose centroid lies on a water pixel, as the solver does.

    Older runs saved the raw PLC mesh, which also covers solid and gas islands.
    """

    if triangles.size == 0:
        return triangles
    centroid = points[triangles].mean(axis=1)
    rows = np.clip(np.floor(phase.shape[0] - centroid[:, 1] / pixel_um).astype(int), 0, phase.shape[0] - 1)
    cols = np.clip(np.floor(centroid[:, 0] / pixel_um).astype(int), 0, phase.shape[1] - 1)
    return triangles[phase[rows, cols] == WATER]


def ideal_figure_data(config_mapping: dict[str, Any], series: dict[str, Any], estimates: dict[str, float]) -> SimulationFigureData:
    from .ideal_workflow import IdealRunConfig

    config = IdealRunConfig.from_mapping(config_mapping)
    phase, pixel = rasterize_ideal_geometry(config)
    data = SimulationFigureData(phase_map=phase, pixel_um=pixel, **_series_kwargs(series))
    data.estimates_ms = {"Large-pore estimate": float(estimates["large"]), "Small-pore estimate": float(estimates["small"])} if estimates else {}
    try:
        points, triangles = ideal_mesh_arrays(config)
        origin_x, origin_y = ideal_frame_origin(config, phase.shape, pixel)
        data.mesh_points_um = points - np.array([origin_x, origin_y])
        data.mesh_triangles = triangles
    except Exception:  # without pyGIMLi the panel falls back to the water mask
        data.mesh_points_um = data.mesh_triangles = None
    return _with_distributions(data)


def _series_kwargs(series: dict[str, Any]) -> dict[str, Any]:
    keys = ("time_ms", "signal", "recon_time_ms", "recon_signal", "t2_ms", "spectrum", "alpha", "inversion_label", "gaussian_components", "gaussian_positions_ms")
    return {key: series[key] for key in keys if key in series}


def save_simulation_figure(data: SimulationFigureData, output_path: Path, dpi: int = 600) -> Path:
    fig = build_simulation_figure(data)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    return output_path
