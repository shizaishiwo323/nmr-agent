"""Manuscript-style figures for the controlled cases and the CT slice.

Layouts, colours, fonts and line weights follow the published figures of the
manuscript (Figs. 4-7 and 9): Arial, 7.2-inch width, panel labels "(a)",
blue/green/orange/red case colours, and translucent filled contours with a
50% outline for overlaid 2D maps. Every function writes PNG (600 dpi) and PDF
and returns the PNG path.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import math

import numpy as np

NAVY = "#27455C"
TEXT = "#242A30"
GREY = "#62727E"
BLUE = "#4789A8"
PALE = "#BAD4E0"
ORANGE = "#BD713E"
AIR = "#F5F7F8"
CASE_BLUE = "#168BEB"
CASE_GREEN = "#22AD63"
CASE_ORANGE = "#DD9024"
CASE_RED = "#EC4B4B"
CASE_PURPLE = "#9863A7"
OVERLAY_LEVELS = [0.05, 0.15, 0.30, 0.50, 0.70, 0.85, 1.00001]


def case_colors(n: int) -> list[str]:
    if n == 3:
        return [CASE_BLUE, CASE_GREEN, CASE_RED]
    base = [CASE_BLUE, CASE_GREEN, CASE_ORANGE, CASE_RED, CASE_PURPLE]
    return [base[i % len(base)] for i in range(n)]


def _font_family() -> list[str]:
    from matplotlib import font_manager

    available = {font.name for font in font_manager.fontManager.ttflist}
    return [name for name in ("Arial", "Liberation Sans", "DejaVu Sans") if name in available] or ["DejaVu Sans"]


@contextmanager
def paper_style():
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    families = _font_family()
    params = {
        "font.family": "sans-serif",
        "font.sans-serif": families,
        "font.size": 8,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "axes.linewidth": 0.7,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "text.color": TEXT,
        "axes.titleweight": "normal",
    }
    if families[0] == "Arial":
        params.update({"mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic", "mathtext.bf": "Arial:bold"})
    else:
        params["mathtext.fontset"] = "dejavusans"
    with plt.rc_context(params):
        yield plt


def _save(fig, output_dir: Path, name: str) -> Path:
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)
    png = output_dir / f"{name}.png"
    fig.savefig(output_dir / f"{name}.pdf", facecolor="white", bbox_inches="tight", pad_inches=0.08)
    fig.savefig(png, facecolor="white", dpi=600, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    return png


def _label(ax, letter: str, bold: bool = False) -> None:
    ax.text(0, 1.045, f"({letter})", transform=ax.transAxes, ha="left", va="bottom", fontsize=9, clip_on=False,
            weight="bold" if bold else "normal")


def _tidy(ax) -> None:
    ax.grid(False)
    ax.tick_params(which="both", direction="out", length=2.5, pad=2)
    ax.set_facecolor("white")


def _title(ax, text: str) -> None:
    ax.set_title(text, pad=14, fontsize=9)


# ---------------------------------------------------------------------------
# Shared 2 x 2 overlay layout of Figs. 4, 6 and 7
# ---------------------------------------------------------------------------

def _overlay_axes(plt, two_d_rows: int):
    rows = 1 + math.ceil(two_d_rows / 2)
    fig, axs = plt.subplots(rows, 2, figsize=(7.2, 2.62 * rows))
    axs = np.atleast_2d(axs)
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.10 if rows > 1 else 0.16, top=0.88 if rows > 1 else 0.78, hspace=0.52, wspace=0.30)
    flat = list(axs.flat)
    for ax in flat[2 + two_d_rows:]:
        ax.axis("off")
    return fig, flat


def _overlay_maps(ax, maps: list[tuple[np.ndarray, np.ndarray, np.ndarray]], colors: list[str], xlim, ylabel: str, title: str):
    from matplotlib.colors import LinearSegmentedColormap

    for (x, y, z), color in zip(maps, colors):
        if z.max() <= 0:
            continue
        cm = LinearSegmentedColormap.from_list("overlay" + color, ["#FFFFFF", color])
        ax.contourf(x, y, z / z.max(), levels=OVERLAY_LEVELS, cmap=cm, alpha=0.34, vmin=0, vmax=1, zorder=1)
    for (x, y, z), color in zip(maps, colors):
        if z.max() <= 0:
            continue
        ax.contour(x, y, z / z.max(), levels=[0.5], colors=[color], linewidths=0.8, alpha=0.95, zorder=5)
    y_all = maps[0][1]
    ax.set(xscale="log", yscale="log", xlim=xlim, ylim=(y_all.min(), y_all.max()), xlabel=r"$T_2$ (ms)", ylabel=ylabel)
    _title(ax, title)


def _two_d_panels(flat, result: dict, keys: list[str], colors: list[str], xlim) -> int:
    used = 0
    for kind, ylabel, title in (("dt2", r"$D$ ($\mu$m$^2$ ms$^{-1}$)", r"$D$–$T_2$ comparison"), ("t1t2", r"$T_1$ (ms)", r"$T_1$–$T_2$ comparison")):
        if not result.get(kind):
            continue
        maps = [(np.asarray(result[kind][k]["t2_axis_ms"]), np.asarray(result[kind][k]["y_axis"]), np.maximum(np.asarray(result[kind][k]["map"]), 0.0)) for k in keys]
        _overlay_maps(flat[2 + used], maps, colors, xlim, ylabel, title)
        used += 1
    return used


def _finish_overlay(flat, n_used: int, log_ticks: list[float] | None = None) -> None:
    import matplotlib

    for j, ax in enumerate(flat[: 2 + n_used]):
        _label(ax, chr(97 + j))
        if j > 0:
            _tidy(ax)
            if log_ticks:
                ax.set_xticks(log_ticks)
                ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
                ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())


def _dimension(ax, start, end, text, offset, color=GREY, fontsize=7.2):
    start, end, offset = np.asarray(start, float), np.asarray(end, float), np.asarray(offset, float)
    a, b = start + offset, end + offset
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="<->", lw=0.6, color=color, shrinkA=0, shrinkB=0))
    for point, base in ((a, start), (b, end)):
        ax.plot([base[0], point[0]], [base[1], point[1]], color=color, lw=0.45)
    mid = (a + b) / 2
    ax.text(mid[0], mid[1], text, fontsize=fontsize, style="italic", ha="center", va="center", color=TEXT,
            bbox=dict(fc="white", ec="none", pad=0.4))


# ---------------------------------------------------------------------------
# Fig. 4: equal-area pore shapes
# ---------------------------------------------------------------------------

def figure_shapes(result: dict, output_dir: Path, name: str = "Equal area geometry") -> Path:
    from matplotlib.patches import Circle, Polygon

    keys = list(result["cases"].keys())
    colors = case_colors(len(keys))
    area = float(result["area_um2"])
    x = np.asarray(result["t2_axis_ms"])
    n_2d = sum(1 for kind in ("dt2", "t1t2") if result.get(kind))
    names = {"circle": "Circle", "equilateral_triangle": "Equilateral\ntriangle", "right_triangle_30_60_90": "Right\ntriangle"}
    short = {"circle": "Circle", "equilateral_triangle": "Equilateral", "right_triangle_30_60_90": "Right"}
    with paper_style() as plt:
        fig, flat = _overlay_axes(plt, n_2d)
        ax = flat[0]
        scale = math.sqrt(area)
        spacing = 1.85 * scale
        ax.set(xlim=(-0.9 * scale, 2 * spacing + 0.9 * scale), ylim=(-1.45 * scale, 1.55 * scale), aspect="equal")
        ax.axis("off")
        _title(ax, "Equal-area pore geometries")
        for j, (key, color) in enumerate(zip(keys, colors)):
            cx = j * spacing
            case = result["cases"][key]
            dims = case["dimensions"]
            if key == "circle":
                radius = dims["radius_um"]
                ax.add_patch(Circle((cx, 0), radius, fc=PALE, ec=color, lw=1.1))
                ax.plot([cx], [0], "o", ms=1.6, color=TEXT)
                ax.annotate("", xy=(cx + radius * 0.71, radius * 0.71), xytext=(cx, 0), arrowprops=dict(arrowstyle="->", lw=0.6, color=GREY))
                ax.text(cx + 0.18 * radius, 0.42 * radius, "r", style="italic", fontsize=7.2)
                top, bottom = radius, -radius
                dim_text = fr"$r={radius:.2f}$ µm"
            else:
                vertices = np.asarray(case["polygon"], float)
                vertices = vertices - (vertices.min(axis=0) + vertices.max(axis=0)) / 2 + np.array([cx, 0])
                ax.add_patch(Polygon(vertices, fc=PALE, ec=color, lw=1.1))
                top, bottom = vertices[:, 1].max(), vertices[:, 1].min()
                if key == "equilateral_triangle":
                    _dimension(ax, vertices[0], vertices[1], "a", (0, -0.13 * scale))
                    dim_text = fr"$a={dims['side_um']:.2f}$ µm"
                else:
                    _dimension(ax, vertices[0], vertices[1], "a", (0, -0.13 * scale))
                    _dimension(ax, vertices[0], vertices[2], "b", (-0.13 * scale, 0))
                    dim_text = fr"$a={dims['short_leg_um']:.2f}$ µm" + "\n" + fr"$b={dims['long_leg_um']:.2f}$ µm"
            ax.text(cx, top + 0.18 * scale, names.get(key, key), ha="center", va="bottom", fontsize=7.2, color=color)
            ax.text(cx, bottom - 0.3 * scale, dim_text, ha="center", va="top", fontsize=6.5)
        ax = flat[1]
        spectra = [np.asarray(result["cases"][k]["spectrum"]) for k in keys]
        top_scale = max(p.max() for p in spectra)
        peaks = [x[np.argmax(p)] for p in spectra]
        for key, p, color, peak in zip(keys, spectra, colors, peaks):
            ax.plot(x, p / top_scale, color=color, lw=0.8, label=f"{short.get(key, key)} ({peak:.0f} ms)")
        ax.set(xscale="log", xlim=(100, 3000), ylim=(0, 1.08), xlabel=r"$T_2$ (ms)", ylabel="Normalized amplitude")
        ax.legend(frameon=False, fontsize=6.6, loc="upper left")
        _title(ax, r"$T_2$ comparison")
        ins = ax.inset_axes([0.67, 0.42, 0.30, 0.50])
        for p, color in zip(spectra, colors):
            ins.plot(x, p / top_scale, color=color, lw=0.8)
        lo, hi = 0.78 * min(peaks), 1.32 * max(peaks)
        ins.set(xlim=(lo, hi), ylim=(0, 1.05), yticks=[])
        ins.set_xticks([round(lo, -1 if lo < 1000 else -2), round(hi, -1 if hi < 1000 else -2)])
        ins.tick_params(labelsize=5.5, length=1.5, pad=1)
        used = _two_d_panels(flat, result, keys, colors, (100, 3000))
        _finish_overlay(flat, used)
        fig.text(0.10, 0.987, fr"Equal pore area: ${area:.2f}\ \mu$m$^2$     $S_w=100\%$", fontsize=10, color=NAVY, va="top")
        return _save(fig, output_dir, name)


# ---------------------------------------------------------------------------
# Fig. 6: saturation series
# ---------------------------------------------------------------------------

def figure_saturation(result: dict, output_dir: Path, name: str = "Saturation comparison") -> Path:
    from matplotlib.patches import Polygon

    keys = list(result["cases"].keys())
    colors = case_colors(len(keys))
    side = float(result["side_um"])
    triangle = np.asarray(result["triangle"], float)
    x = np.asarray(result["t2_axis_ms"])
    n_2d = sum(1 for kind in ("dt2", "t1t2") if result.get(kind))
    with paper_style() as plt:
        fig, flat = _overlay_axes(plt, n_2d)
        ax = flat[0]
        ax.axis("off")
        _title(ax, "Water occupancy")
        cols = 2 if len(keys) > 1 else 1
        rows = math.ceil(len(keys) / cols)
        for j, (key, color) in enumerate(zip(keys, colors)):
            case = result["cases"][key]
            r, c = divmod(j, cols)
            sub = ax.inset_axes([c / cols + 0.02, 1 - (r + 1) / rows + 0.02, 1 / cols - 0.04, 1 / rows - 0.10])
            sub.add_patch(Polygon(triangle, fc=AIR, ec="none"))
            for polygon in case["polygons"]:
                sub.add_patch(Polygon(np.asarray(polygon), fc=PALE, ec=color, lw=0.6))
            sub.add_patch(Polygon(triangle, fc="none", ec=color, lw=1.1))
            if j == 0:
                _dimension(sub, triangle[1], triangle[2], "a", (0, -0.09 * side), fontsize=6.5)
            sub.set(xlim=(-0.62 * side, 0.62 * side), ylim=(-0.16 * side, 0.92 * side), aspect="equal")
            sub.axis("off")
            sub.set_title(fr"$S_w={100 * case['saturation']:.3g}\%$", fontsize=7.2, color=color, pad=2)
        ax = flat[1]
        for key, color in zip(keys, colors):
            p = np.asarray(result["cases"][key]["spectrum"])
            p = p / p.max()
            ax.plot(x, p, color=color, lw=0.8)
            peak = x[np.argmax(p)]
            ax.text(peak, 1.03, f"{peak:.0f}", color=color, ha="center", va="bottom", fontsize=7.2)
        ax.set(xscale="log", xlim=(10, 2000), ylim=(0, 1.14), xlabel=r"$T_2$ (ms)", ylabel="Peak-normalized amplitude")
        _title(ax, r"$T_2$ comparison")
        used = _two_d_panels(flat, result, keys, colors, (10, 2000))
        _finish_overlay(flat, used)
        fig.text(0.10, 0.987, fr"Equilateral pore: $a={side:g}$ µm     $\theta={result['contact_angle_deg']:g}^\circ$", fontsize=10, color=NAVY, va="top")
        return _save(fig, output_dir, name)


# ---------------------------------------------------------------------------
# Fig. 7: contact angles at a fixed saturation
# ---------------------------------------------------------------------------

def figure_contact_angle(result: dict, output_dir: Path, name: str = "Contact angle comparison") -> Path:
    from matplotlib.patches import Arc, Polygon, Rectangle

    keys = list(result["cases"].keys())
    colors = case_colors(len(keys))
    side = float(result["side_um"])
    triangle = np.asarray(result["triangle"], float)
    x = np.asarray(result["t2_axis_ms"])
    peaks = [x[np.argmax(result["cases"][k]["spectrum"])] for k in keys]
    nice = (3, 5, 10, 20, 30, 50, 100, 200, 300, 500, 1000, 2000, 3000, 5000)
    lower = max([v for v in nice if v <= 0.25 * min(peaks)] or [nice[0]])
    upper = min([v for v in nice if v >= 1.6 * max(peaks)] or [nice[-1]])
    xlim = (lower, upper)
    ticks = [v for v in nice if lower <= v <= upper]
    n_2d = sum(1 for kind in ("dt2", "t1t2") if result.get(kind))
    with paper_style() as plt:
        fig, flat = _overlay_axes(plt, n_2d)
        ax = flat[0]
        ax.add_patch(Polygon(triangle, fc="white", ec="#63727B", lw=0.55))
        for key, color in zip(keys, colors):
            case = result["cases"][key]
            for k, polygon in enumerate(case["polygons"]):
                polygon = np.asarray(polygon)
                ax.plot(polygon[1:, 0], polygon[1:, 1], color=color, lw=0.6, alpha=0.88, solid_capstyle="round",
                        label=fr"$\theta={case['contact_angle_deg']:g}^\circ$" if k == 0 else None)
        ax.set(xlim=(-0.6 * side, 0.6 * side), ylim=(-0.05 * side, 0.95 * side), aspect="equal")
        ax.axis("off")
        ax.legend(loc="center", bbox_to_anchor=(0.50, 0.38), fontsize=8, frameon=False, handlelength=1.6)
        _title(ax, "Equal water area")
        # Zoom on the contact points of the lower-right wedge on the inclined wall.
        contacts = np.asarray([np.asarray(result["cases"][k]["polygons"][2])[1] for k in keys])
        spread = float(np.ptp(contacts, axis=0).max())
        box = max(0.15 * side, 2.2 * spread)
        center = contacts.mean(axis=0)
        x0, y0 = center[0] - 0.5 * box, center[1] - 0.5 * box
        ax.add_patch(Rectangle((x0, y0), box, box, fill=False, ec="#A8B1B7", lw=0.35, zorder=5))
        detail = ax.inset_axes([0.70, 0.53, 0.50, 0.50])
        detail.add_patch(Polygon(triangle, fc="white", ec="#63727B", lw=0.55))
        wall = np.array([0.5, -math.sqrt(3) / 2])
        normal = np.array([math.sqrt(3) / 2, 0.5])
        mark = 0.04 * box
        for key, color in zip(keys, colors):
            case = result["cases"][key]
            polygon = np.asarray(case["polygons"][2])
            detail.plot(polygon[1:, 0], polygon[1:, 1], color=color, lw=0.65, alpha=0.88, solid_capstyle="round")
            cp = polygon[1]
            theta = case["contact_angle_deg"]
            angle = math.radians(-60 - theta)
            tangent = np.array([math.cos(angle), math.sin(angle)])
            detail.plot(*cp, "o", ms=2.1, color=color, zorder=9)
            detail.plot([cp[0], cp[0] + 0.2 * box * normal[0]], [cp[1], cp[1] + 0.2 * box * normal[1]], color=color, lw=0.5, ls=(0, (2, 1.7)), zorder=7)
            detail.plot([cp[0], cp[0] + 0.2 * box * tangent[0]], [cp[1], cp[1] + 0.2 * box * tangent[1]], color=color, lw=0.5, ls=(0, (2, 1.7)), zorder=7)
            q = np.array([cp + mark * wall, cp + mark * wall + mark * normal, cp + mark * normal])
            detail.plot(q[:, 0], q[:, 1], color=color, lw=0.35, zorder=7)
            if theta > 0:
                detail.add_patch(Arc(cp, 0.23 * box, 0.23 * box, theta1=-60 - theta, theta2=-60, color=color, lw=0.5, zorder=8))
            end = cp + 0.2 * box * normal
            detail.text(x0 + 0.97 * box, end[1] + 0.03 * box, fr"$\theta={theta:g}^\circ$", fontsize=5.3, color=color, ha="right", va="center")
        detail.set(xlim=(x0, x0 + box), ylim=(y0, y0 + box), aspect="equal", xticks=[], yticks=[])
        for spine in detail.spines.values():
            spine.set_color("#A8B1B7")
            spine.set_linewidth(0.4)
        detail.set_title("Contact region", fontsize=7, pad=4, color="#4D5A63")
        ax = flat[1]
        for key, color in zip(keys, colors):
            p = np.asarray(result["cases"][key]["spectrum"])
            ax.plot(x, p / p.max(), color=color, lw=0.8)
        ax.set(xscale="log", xlim=xlim, ylim=(0, 1.1), xlabel=r"$T_2$ (ms)", ylabel="Peak-normalized amplitude")
        _title(ax, r"$T_2$ comparison")
        used = _two_d_panels(flat, result, keys, colors, xlim)
        _finish_overlay(flat, used, ticks)
        fig.text(0.10, 0.987, fr"Contact-angle comparison at $S_w={100 * result['saturation']:.3g}\%$     $a={side:g}\ \mu$m", va="top", color=NAVY, fontsize=10)
        return _save(fig, output_dir, name)


# ---------------------------------------------------------------------------
# Fig. 5: coupled and uncoupled dual pore
# ---------------------------------------------------------------------------

def figure_coupling(result: dict, output_dir: Path, name: str = "Coupled and uncoupled") -> Path:
    from matplotlib.collections import LineCollection
    from matplotlib.patches import Patch, Polygon

    large_side = float(result["large_side_um"])
    small_side = float(result["small_side_um"])
    with paper_style() as plt:
        fig = plt.figure(figsize=(7.2, 3.3))
        gs = fig.add_gridspec(1, 2, width_ratios=[1.12, 1], left=0.035, right=0.98, bottom=0.27, top=0.86, wspace=0.29)
        ax = fig.add_subplot(gs[0, 0])
        unit = large_side / 20.0
        ax.set(xlim=(-15 * unit, 45 * unit), ylim=(-22 * unit, 24 * unit), aspect="equal")
        ax.axis("off")
        _label(ax, "a")

        def prism(vertices, water=True):
            sign = np.sign(np.sum(vertices[:, 0] * np.roll(vertices[:, 1], -1) - vertices[:, 1] * np.roll(vertices[:, 0], -1)))
            edges = np.roll(vertices, -1, axis=0) - vertices
            normals = sign * np.c_[edges[:, 1], -edges[:, 0]] / np.linalg.norm(edges, axis=1)[:, None]
            prev = np.roll(normals, 1, axis=0)
            outer = vertices + 0.34 * unit * (prev + normals) / (1 + (prev * normals).sum(axis=1))[:, None]
            back = outer + np.array([1.1, 1.5]) * unit
            ax.add_patch(Polygon(back, fc="#E4E5E7", ec="#78868E", lw=0.45, zorder=1))
            for i in range(len(outer)):
                k = (i + 1) % len(outer)
                ax.add_patch(Polygon([outer[i], outer[k], back[k], back[i]], fc="#C6CBCF", ec="#78868E", lw=0.45, zorder=2))
            ax.add_patch(Polygon(outer, fc="#DDE0E2", ec="#78868E", lw=0.45, zorder=3))
            ax.add_patch(Polygon(vertices, fc="#C7E4F1" if water else "#F4F4F4", ec="none", zorder=4))
            ax.add_patch(Polygon(vertices, fc="none", ec="#78868E", lw=0.4, zorder=6))

        def mesh_lines(segments, flip, shift):
            if not segments:
                return
            seg = np.asarray(segments, float).copy()
            if flip:
                seg[..., 1] *= -1
            seg += np.asarray(shift)
            ax.add_collection(LineCollection(seg, colors="#4D86A2", linewidths=0.11, alpha=0.46, zorder=5))

        hl, hs = large_side / 2, small_side / 2
        neck = 1.3 * unit
        for j, cx in enumerate([0, 30 * unit]):
            large = np.array([[-hl, -unit], [hl, -unit], [0, math.sqrt(3) * hl - unit]]) + np.array([cx, 0])
            small = np.array([[-hs, -6 * unit], [hs, -6 * unit], [0, -6 * unit - math.sqrt(3) * hs]]) + np.array([cx, 0])
            if j == 1:
                bridge = np.array([[-neck, -6 * unit], [neck, -6 * unit], [neck, -unit], [-neck, -unit]]) + np.array([cx, 0])
                prism(bridge, water=False)
                ax.add_patch(Polygon(bridge, fc="none", ec="#828F96", lw=0.5, ls=(0, (3, 2)), zorder=7))
                ax.text(cx + neck + 1.2 * unit, -3.5 * unit, r"Exchange bridge ($k_{\mathrm{ex}}$)", fontsize=5.5, color="#4D5A63", va="center")
            prism(large)
            prism(small)
            mesh_lines(result.get("mesh_segments", {}).get("large"), False, (cx, -unit))
            mesh_lines(result.get("mesh_segments", {}).get("small"), True, (cx, -6 * unit))
            ax.text(cx, 22 * unit, "Uncoupled" if j == 0 else "Coupled", ha="center", fontsize=9, color=NAVY if j == 0 else ORANGE)
            ax.text(cx, -18 * unit, "Independent relaxation" if j == 0 else "Inter-pore exchange", ha="center", fontsize=7)
        ax.legend(handles=[Patch(facecolor="#D1D4D7", edgecolor="#78868E", linewidth=0.5, label="Solid wall"),
                           Patch(facecolor="#BBDDED", edgecolor="#78868E", linewidth=0.5, label="Water")],
                  loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2, frameon=False, fontsize=7, handlelength=1.2, columnspacing=1.5)
        ax.text(0.5, -0.25, fr"$a_L={large_side:g}\ \mu$m   $a_S={small_side:g}\ \mu$m   $S_w=100\%$", transform=ax.transAxes, ha="center", fontsize=8)
        ax = fig.add_subplot(gs[0, 1])
        x = np.asarray(result["t2_axis_ms"])
        p = np.asarray(result["uncoupled_spectrum"])
        q = np.asarray(result["coupled_spectrum"])
        scale = max(p.max(), q.max())
        ax.plot(x, p / scale, color=NAVY, lw=0.95, label="Uncoupled")
        ax.plot(x, q / scale, color=ORANGE, lw=0.95, label="Coupled")
        peaks = [x[np.argmax(p)], x[np.argmax(q)]]
        ax.set(xscale="log", xlim=(max(5.0, 0.105 * min(peaks)), 2.5 * max(peaks)), ylim=(0, 1.12), xlabel=r"$T_2$ (ms)", ylabel="Normalized amplitude")
        _tidy(ax)
        _label(ax, "b")
        ax.legend(frameon=False, fontsize=7.5, loc="upper left")
        return _save(fig, output_dir, name)


# ---------------------------------------------------------------------------
# Fig. 9: segmented CT slice
# ---------------------------------------------------------------------------

def _phase_map(ax, labels, styles, pixel_mm):
    height, width = labels.shape
    xs = (np.arange(width + 2) - 0.5) * pixel_mm
    ys = (np.arange(height + 2) - 0.5) * pixel_mm
    for value, fill, edge in styles:
        mask = np.pad((labels == value).astype(float), 1, mode="constant")
        if mask.any():
            ax.contourf(xs, ys, mask, levels=[0.5, 1.5], colors=[fill], antialiased=True)
            ax.contour(xs, ys, mask, levels=[0.5], colors=[edge], linewidths=0.12, alpha=0.45)
    ax.set_xlim(0, width * pixel_mm)
    ax.set_ylim(0, height * pixel_mm)


def figure_slice(result: dict, output_dir: Path, name: str = "CT to NMR") -> Path:
    from matplotlib.patches import Patch

    labels = np.asarray(result["labels"])
    values = result["phase_values"]
    pixel_mm = float(result["pixel_size_um"]) / 1000.0
    solid_name = result.get("solid_name", "Solid")
    title = result.get("title", "Segmented slice")
    with paper_style() as plt:
        fig = plt.figure(figsize=(7.2, 5.6))
        gs = fig.add_gridspec(2, 6, left=0.085, right=0.98, bottom=0.10, top=0.89, hspace=0.65, wspace=1.05)
        ax = fig.add_subplot(gs[0, :2])
        _phase_map(ax, labels, [(values["air"], "#E9D8B3", "#C9B988"), (values["water"], BLUE, "#397794"), (values["solid"], "#91999F", "#737C82")], pixel_mm)
        ax.set_title("Three-phase slice", fontsize=9, pad=17)
        ax.set(xlabel="Width (mm)", ylabel="Height (mm)")
        _label(ax, "a", bold=True)
        _tidy(ax)
        ax.legend(handles=[Patch(fc="#91999F", label=solid_name), Patch(fc=BLUE, label="Water"), Patch(fc="#E9D8B3", label="Air")],
                  loc="lower left", fontsize=6, framealpha=0.95, handlelength=0.8, borderpad=0.3, labelspacing=0.2)
        ax = fig.add_subplot(gs[0, 2:4])
        _phase_map(ax, labels, [(values["water"], BLUE, "#397794")], pixel_mm)
        ax.set(xlabel="Width (mm)")
        ax.tick_params(labelleft=False)
        ax.set_title("Water-filled domain", fontsize=9, pad=17)
        _label(ax, "b", bold=True)
        _tidy(ax)
        ax = fig.add_subplot(gs[0, 4:])
        diameters = np.asarray(result["local_diameter_um"])
        if diameters.size:
            bin_width = max(float(result["pixel_size_um"]) * 5, 1.0)
            edges = np.arange(0, math.ceil(diameters.max() / bin_width) * bin_width + bin_width, bin_width)
            counts, edges = np.histogram(diameters, bins=edges)
            fractions = counts / max(counts.sum(), 1)
            ax.bar((edges[:-1] + edges[1:]) / 2, 100 * fractions, width=np.diff(edges) * 0.92, color=BLUE)
            ax.set(ylim=(0, max(fractions) * 115))
        ax.set(xlabel=r"Local pore diameter ($\mu$m)", ylabel="Pore area fraction (%)")
        ax.set_title("Local pore-size distribution", fontsize=9, pad=17)
        _label(ax, "c", bold=True)
        _tidy(ax)
        t = np.asarray(result["times_ms"])
        signal = np.asarray(result["signal"])
        fit = np.asarray(result["fit"])
        ax = fig.add_subplot(gs[1, :3])
        ax.plot(t, signal, color=NAVY, lw=0.85, label="Simulated echo envelope")
        idx = np.linspace(1, len(t) - 2, 18).astype(int)
        ax.plot(t[idx], fit[idx], "o", ms=3, mfc="white", mec=ORANGE, label="Spectral reconstruction")
        ax.set(xlabel="Echo time (ms)", ylabel="Normalized signal", ylim=(0, 1.05), xlim=(t.min(), t.max()))
        ax.legend(fontsize=7, frameon=False, loc="lower left")
        ax.set_title("Simulated response and fit", fontsize=9, pad=17)
        _label(ax, "d", bold=True)
        _tidy(ax)
        x = np.asarray(result["t2_axis_ms"])
        p_l = np.asarray(result["spectrum_lcurve"])
        p_f = np.asarray(result["spectrum_fixed"])
        ax = fig.add_subplot(gs[1, 3:])
        ax.plot(x, p_l / p_l.max(), color=NAVY, lw=0.85, label=fr"L-curve, $\alpha={result['alpha']:.2f}$")
        ix = np.where(p_f / p_f.max() > 0.01)[0][::3]
        ax.plot(x[ix], (p_f / p_f.max())[ix], "o", ms=3, mfc="white", mec=ORANGE, label=fr"Fixed, $\alpha={result['fixed_alpha']:g}$")
        ax.set(xscale="log", xlabel=r"$T_2$ (ms)", ylabel="Peak-normalized amplitude", ylim=(0, 1.1), xlim=(x.min(), x.max()))
        ax.legend(fontsize=7, frameon=False, loc="upper left")
        ax.set_title(r"$T_2$ distribution", fontsize=9, pad=17)
        _label(ax, "e", bold=True)
        _tidy(ax)
        stats = result["statistics"]
        fig.text(0.085, 0.988, fr"{title}: $\phi_{{2D}}={stats['porosity_2d'] * 100:.1f}\,\%$     $S_w={stats['water_saturation'] * 100:.1f}\,\%$",
                 color=NAVY, fontsize=9, va="top")
        return _save(fig, output_dir, name)
