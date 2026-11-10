"""High-level runs of the paper's controlled cases and CT-slice solver.

Every run writes a workbook with signals and spectra, a JSON summary and a
manuscript-style figure into its own folder, and returns a summary dictionary.
"""

from __future__ import annotations

from datetime import datetime
import json
import math
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from . import exchange as X
from . import fem
from . import figures
from . import geometry as G
from . import inversion as I
from .settings import DT2Acquisition, ExchangeSettings, InversionGrids, PaperSettings, T1T2Acquisition

Progress = Callable[[str], None] | None


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


def _run_dir(base: Path, tag: str) -> Path:
    path = Path(base) / f"{tag}__{_stamp()}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _note(progress: Progress, text: str) -> None:
    if progress:
        progress(text)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value


def _fast_diffusion_t2(settings: PaperSettings, perimeter_um: float, area_um2: float) -> float:
    return 1.0 / (1.0 / settings.t2_bulk_ms + settings.rho2_um_per_ms * perimeter_um / area_um2)


def _two_d(mesh, settings: PaperSettings, grids: InversionGrids, include_dt2: bool, include_t1t2: bool, t1t2_step_ms: float) -> dict:
    out: dict[str, Any] = {}
    if include_dt2:
        acquisition = DT2Acquisition()
        signal, _ = fem.solve_dt2(mesh, settings, acquisition)
        distribution, diag = I.invert_dt2(signal, acquisition.b_axis, acquisition.te_axis_ms, grids.d_axis, grids.dt2_t2_axis_ms, grids.two_d_alpha)
        out["dt2"] = {"signal": signal, "map": distribution, "y_axis": grids.d_axis, "t2_axis_ms": grids.dt2_t2_axis_ms, "diagnostics": diag,
                      "row_axis": acquisition.b_axis, "column_axis": acquisition.te_axis_ms}
    if include_t1t2:
        acquisition = T1T2Acquisition(maximum_time_step_ms=t1t2_step_ms)
        signal, _ = fem.solve_t1t2(mesh, settings, acquisition)
        distribution, diag = I.invert_t1t2(signal, acquisition.recovery_times_ms, acquisition.detection_times_ms, grids.t1_axis_ms, grids.t1t2_t2_axis_ms, grids.two_d_alpha)
        out["t1t2"] = {"signal": signal, "map": distribution, "y_axis": grids.t1_axis_ms, "t2_axis_ms": grids.t1t2_t2_axis_ms, "diagnostics": diag,
                       "row_axis": acquisition.recovery_times_ms, "column_axis": acquisition.detection_times_ms}
    return out


def _write_workbook(path: Path, settings: PaperSettings, grids: InversionGrids, signals: dict, spectra: dict, two_d: dict, diagnostics: list[dict]) -> Path:
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame(diagnostics).to_excel(writer, sheet_name="diagnostics", index=False)
        pd.DataFrame({"time_ms": settings.t2_times_ms, **signals}).to_excel(writer, sheet_name="T2_signals", index=False)
        pd.DataFrame({"T2_ms": grids.t2_axis_ms, **spectra}).to_excel(writer, sheet_name="T2_spectra", index=False)
        for key, data in two_d.items():
            for kind, label in (("dt2", "DT2"), ("t1t2", "T1T2")):
                if kind in data:
                    item = data[kind]
                    sheet = f"{label}_map_{key}"[:31]
                    pd.DataFrame(item["map"], index=item["y_axis"], columns=item["t2_axis_ms"]).to_excel(writer, sheet_name=sheet)
                    sheet = f"{label}_signal_{key}"[:31]
                    pd.DataFrame(item["signal"], index=item["row_axis"], columns=item["column_axis"]).to_excel(writer, sheet_name=sheet)
    return path


def _figure_maps(two_d: dict, keys: list[str]) -> dict:
    result: dict[str, Any] = {}
    for kind in ("dt2", "t1t2"):
        if all(kind in two_d.get(key, {}) for key in keys) and keys:
            result[kind] = {key: two_d[key][kind] for key in keys}
    return result


# ---------------------------------------------------------------------------
# Equal-area pore shapes (Fig. 4)
# ---------------------------------------------------------------------------

def run_shape_comparison(output_base: Path, *, area_um2: float | None = None, include_dt2: bool = True, include_t1t2: bool = True,
                         settings: PaperSettings | None = None, grids: InversionGrids | None = None, progress: Progress = None) -> dict:
    settings = settings or PaperSettings()
    grids = grids or InversionGrids()
    area = float(area_um2 or G.equilateral_area(20.0))
    run_dir = _run_dir(output_base, "pore_shapes")
    dims = G.shape_dimensions(area)
    labels = {
        "circle": fr"$r={dims['circle']['radius_um']:.2f}\ \mu$m",
        "equilateral_triangle": fr"$a={dims['equilateral_triangle']['side_um']:.2f}\ \mu$m",
        "right_triangle_30_60_90": fr"$a={dims['right_triangle_30_60_90']['short_leg_um']:.2f},\ b={dims['right_triangle_30_60_90']['long_leg_um']:.2f}\ \mu$m",
    }
    cases, signals, spectra, two_d, diagnostics = {}, {}, {}, {}, []
    for key, polygon in G.shape_polygons(area).items():
        _note(progress, f"Solving {G.SHAPE_LABELS[key]}")
        mesh = G.build_mesh(G.saturated_polygon_geometry(polygon), settings.maximum_triangle_area_um2, settings.mesh_quality)
        signal, meta = fem.solve_t2(mesh, settings)
        spectrum = I.invert_t2_controlled(settings.t2_times_ms, signal, grids.t2_axis_ms, grids.t2_alpha)
        two_d[key] = _two_d(mesh, settings, grids, include_dt2, include_t1t2, 2.0)
        perimeter = dims[key]["perimeter_um"]
        estimate = _fast_diffusion_t2(settings, perimeter, area)
        signals[key], spectra[key] = signal, spectrum
        row = {"case": key, "perimeter_um": perimeter, "mesh_area_um2": G.mesh_area(mesh), "nodes": meta["nodes"], "cells": meta["cells"],
               "peak_T2_ms": I.peak_position(grids.t2_axis_ms, spectrum), "fast_diffusion_T2_ms": estimate}
        for kind in ("dt2", "t1t2"):
            if kind in two_d[key]:
                row.update({f"{kind}_{k}": v for k, v in two_d[key][kind]["diagnostics"].items() if k != "alpha"})
        diagnostics.append(row)
        cases[key] = {"label": G.SHAPE_LABELS[key], "dimension_label": labels[key], "dimensions": dims[key], "polygon": polygon, "spectrum": spectrum}
    workbook = _write_workbook(run_dir / "pore_shapes_responses.xlsx", settings, grids, signals, spectra, two_d, diagnostics)
    figure = figures.figure_shapes({"cases": cases, "area_um2": area, "t2_axis_ms": grids.t2_axis_ms, **_figure_maps(two_d, list(cases))}, run_dir)
    circle_peak = diagnostics[0]["peak_T2_ms"]
    summary = {
        "case": "equal_area_pore_shapes",
        "area_um2": area,
        "dimensions": dims,
        "results": [{k: v for k, v in row.items()} for row in diagnostics],
        "peak_shift_vs_circle_percent": {row["case"]: 100.0 * (row["peak_T2_ms"] / circle_peak - 1.0) for row in diagnostics},
        "settings": settings.as_dict(),
        "inversion": grids.as_dict(),
        "two_d": {"dt2": include_dt2, "t1t2": include_t1t2},
        "interpretation_basis": "At equal area the shapes differ only in perimeter, so S/V and the fast-diffusion T2 differ (Brownstein & Tarr, 1979).",
    }
    (run_dir / "summary.json").write_text(json.dumps(_jsonable(summary), indent=2), encoding="utf-8")
    return {"summary": summary, "artifacts": [str(figure), str(figure.with_suffix(".pdf")), str(workbook), str(run_dir / "summary.json")], "run_dir": str(run_dir)}


# ---------------------------------------------------------------------------
# Saturation series and contact angles (Figs. 6 and 7)
# ---------------------------------------------------------------------------

def _corner_case(saturation: float, theta: float, side: float, settings: PaperSettings, grids: InversionGrids,
                 include_dt2: bool, include_t1t2: bool):
    if saturation >= 1.0 - 1e-12:
        polygons = [G.equilateral_vertices(side)]
        geometry = G.saturated_polygon_geometry(polygons[0])
        info = {"radius_um": None, "contact_length_um": side / 2.0, "solid_water_length_um": 3.0 * side, "water_air_length_um": 0.0}
    else:
        water = G.corner_water(saturation, theta, side)
        polygons = water.polygons
        geometry = G.corner_water_geometry(water)
        info = {"radius_um": water.radius_um, "contact_length_um": water.contact_length_um,
                "solid_water_length_um": water.solid_water_length_um, "water_air_length_um": water.water_air_length_um}
    mesh = G.build_mesh(geometry, settings.maximum_triangle_area_um2, settings.mesh_quality)
    signal, meta = fem.solve_t2(mesh, settings)
    spectrum = I.invert_t2_controlled(settings.t2_times_ms, signal, grids.t2_axis_ms, grids.t2_alpha)
    two_d = _two_d(mesh, settings, grids, include_dt2, include_t1t2, 0.5)
    water_area = saturation * G.equilateral_area(side)
    row = {
        "saturation": saturation,
        "contact_angle_deg": theta,
        "represented_saturation": G.mesh_area(mesh) / G.equilateral_area(side),
        **info,
        "nodes": meta["nodes"],
        "cells": meta["cells"],
        "peak_T2_ms": I.peak_position(grids.t2_axis_ms, spectrum),
        "fast_diffusion_T2_ms": _fast_diffusion_t2(settings, info["solid_water_length_um"], water_area),
        "solid_wall_wetted_fraction": info["solid_water_length_um"] / (3.0 * side),
    }
    for kind in ("dt2", "t1t2"):
        if kind in two_d:
            row.update({f"{kind}_{k}": v for k, v in two_d[kind]["diagnostics"].items() if k != "alpha"})
    return polygons, signal, spectrum, two_d, row


def _saturated_pore_estimate(side: float, settings: PaperSettings) -> float:
    return _fast_diffusion_t2(settings, 3.0 * side, G.equilateral_area(side))


def run_saturation_series(output_base: Path, *, saturations: list[float] | None = None, contact_angle_deg: float = 0.0, side_um: float = 20.0,
                          include_dt2: bool = True, include_t1t2: bool = True, settings: PaperSettings | None = None,
                          grids: InversionGrids | None = None, progress: Progress = None) -> dict:
    settings = settings or PaperSettings()
    grids = grids or InversionGrids()
    saturations = sorted({float(s) for s in (saturations or [0.0226, 0.153, 0.380, 1.0])})
    limits = G.corner_water_limits(contact_angle_deg, side_um)
    bad = [s for s in saturations if not (s >= 1.0 - 1e-12 or 0.0 < s <= limits["max_saturation"] + 1e-9)]
    if bad:
        raise ValueError(
            f"Saturations {bad} are outside the corner-water range (0, {limits['max_saturation']:.3f}] for theta = {contact_angle_deg:g} degrees; "
            "use Sw = 1 for the saturated pore."
        )
    run_dir = _run_dir(output_base, "saturation_series")
    cases, signals, spectra, two_d, diagnostics = {}, {}, {}, {}, []
    for sw in saturations:
        key = f"Sw_{sw:.4f}"
        _note(progress, f"Solving Sw = {100 * sw:g}%")
        polygons, signal, spectrum, maps, row = _corner_case(sw, contact_angle_deg, side_um, settings, grids, include_dt2, include_t1t2)
        cases[key] = {"saturation": sw, "polygons": polygons, "spectrum": spectrum}
        signals[key], spectra[key], two_d[key] = signal, spectrum, maps
        diagnostics.append(row)
    workbook = _write_workbook(run_dir / "saturation_responses.xlsx", settings, grids, signals, spectra, two_d, diagnostics)
    figure = figures.figure_saturation({"cases": cases, "side_um": side_um, "contact_angle_deg": contact_angle_deg,
                                        "triangle": G.equilateral_vertices(side_um), "t2_axis_ms": grids.t2_axis_ms,
                                        **_figure_maps(two_d, list(cases))}, run_dir)
    saturated = _saturated_pore_estimate(side_um, settings)
    summary = {
        "case": "saturation_series",
        "side_um": side_um,
        "contact_angle_deg": contact_angle_deg,
        "corner_water_max_saturation": limits["max_saturation"],
        "results": diagnostics,
        "saturated_pore_fast_diffusion_T2_ms": saturated,
        "settings": settings.as_dict(),
        "inversion": grids.as_dict(),
        "interpretation_basis": "Corner water relaxes with the S/V of the wedge, set by the meniscus radius, not by the pore size (Mohnke et al., 2015; Zhou & Zhang, 2025).",
    }
    (run_dir / "summary.json").write_text(json.dumps(_jsonable(summary), indent=2), encoding="utf-8")
    return {"summary": summary, "artifacts": [str(figure), str(figure.with_suffix(".pdf")), str(workbook), str(run_dir / "summary.json")], "run_dir": str(run_dir)}


def run_contact_angle_series(output_base: Path, *, saturation: float = 0.153, contact_angles_deg: list[float] | None = None, side_um: float = 20.0,
                             include_dt2: bool = True, include_t1t2: bool = True, settings: PaperSettings | None = None,
                             grids: InversionGrids | None = None, progress: Progress = None) -> dict:
    settings = settings or PaperSettings()
    grids = grids or InversionGrids()
    angles = [float(a) for a in (contact_angles_deg or [0.0, 30.0, 45.0])]
    for angle in angles:
        limit = G.corner_water_limits(angle, side_um)["max_saturation"]
        if not 0.0 < saturation <= limit + 1e-9:
            raise ValueError(f"Sw = {saturation:g} is not a corner-water state at theta = {angle:g} degrees (limit {limit:.3f}).")
    run_dir = _run_dir(output_base, "contact_angle_series")
    cases, signals, spectra, two_d, diagnostics = {}, {}, {}, {}, []
    for angle in angles:
        key = f"CA{angle:g}"
        _note(progress, f"Solving contact angle {angle:g} degrees")
        polygons, signal, spectrum, maps, row = _corner_case(saturation, angle, side_um, settings, grids, include_dt2, include_t1t2)
        cases[key] = {"contact_angle_deg": angle, "polygons": polygons, "spectrum": spectrum, "contact_length_um": row["contact_length_um"]}
        signals[key], spectra[key], two_d[key] = signal, spectrum, maps
        diagnostics.append(row)
    workbook = _write_workbook(run_dir / "contact_angle_responses.xlsx", settings, grids, signals, spectra, two_d, diagnostics)
    figure = figures.figure_contact_angle({"cases": cases, "side_um": side_um, "saturation": saturation, "triangle": G.equilateral_vertices(side_um),
                                           "t2_axis_ms": grids.t2_axis_ms, **_figure_maps(two_d, list(cases))}, run_dir)
    base = diagnostics[0]
    summary = {
        "case": "contact_angle_series",
        "side_um": side_um,
        "saturation": saturation,
        "results": diagnostics,
        "peak_change_vs_first_angle_percent": {f"{row['contact_angle_deg']:g}": 100.0 * (row["peak_T2_ms"] / base["peak_T2_ms"] - 1.0) for row in diagnostics},
        "settings": settings.as_dict(),
        "inversion": grids.as_dict(),
        "interpretation_basis": "The water stays as three corner wedges in every case. At fixed water area a larger contact angle shortens the wetted wall (solid_water_length_um), lowers the relaxing S/V and lengthens T2; the meniscus radius and the capillary pressure change with it. Do not describe the water as droplets.",
    }
    (run_dir / "summary.json").write_text(json.dumps(_jsonable(summary), indent=2), encoding="utf-8")
    return {"summary": summary, "artifacts": [str(figure), str(figure.with_suffix(".pdf")), str(workbook), str(run_dir / "summary.json")], "run_dir": str(run_dir)}


# ---------------------------------------------------------------------------
# Dual pore with effective exchange (Fig. 5)
# ---------------------------------------------------------------------------

def run_dual_pore_exchange(output_base: Path, *, large_side_um: float = 20.0, small_side_um: float = 8.0, exchange: ExchangeSettings | None = None,
                           settings: PaperSettings | None = None, grids: InversionGrids | None = None, progress: Progress = None) -> dict:
    settings = settings or PaperSettings()
    grids = grids or InversionGrids()
    exchange = exchange or ExchangeSettings()
    run_dir = _run_dir(output_base, "dual_pore_exchange")
    times = np.arange(0.0, float(settings.t2_times_ms[-1]) + 0.5 * exchange.time_step_ms, exchange.time_step_ms)
    signals, meshes, segments = {}, {}, {}
    for tag, side in (("large", large_side_um), ("small", small_side_um)):
        _note(progress, f"Solving the {tag} pore")
        area = G.equilateral_area(side)
        mesh = G.build_mesh(G.saturated_polygon_geometry(G.equilateral_vertices(side)), area / 900.0, 33.0)
        signals[tag], meta = fem.solve_t2(mesh, settings, times)
        meshes[tag] = {"nodes": meta["nodes"], "cells": meta["cells"], "area_um2": area}
        segments[tag] = [[[b.node(0).x(), b.node(0).y()], [b.node(1).x(), b.node(1).y()]] for b in mesh.boundaries()]
    volume_l = G.equilateral_area(large_side_um) * large_side_um
    volume_s = G.equilateral_area(small_side_um) * small_side_um
    w_l, w_s = volume_l / (volume_l + volume_s), volume_s / (volume_l + volume_s)
    large, small = w_l * signals["large"], w_s * signals["small"]
    k_ex = exchange.k_ex_per_ms
    coupled_l, coupled_s = X.apply_exchange(large, small, times, k_ex)
    axis = grids.t2_axis_ms
    unc = I.invert_t2_controlled(times, large, axis, grids.t2_alpha) + I.invert_t2_controlled(times, small, axis, grids.t2_alpha)
    cpl = I.invert_t2_controlled(times, coupled_l, axis, grids.t2_alpha) + I.invert_t2_controlled(times, coupled_s, axis, grids.t2_alpha)
    from scipy.signal import find_peaks

    def peaks(p):
        return [float(axis[i]) for i in find_peaks(p, height=0.02 * p.max())[0]]

    est_l = _saturated_pore_estimate(large_side_um, settings)
    est_s = _saturated_pore_estimate(small_side_um, settings)
    fast_exchange = 1.0 / X.fast_exchange_rate((1.0 / est_l, 1.0 / est_s), (w_l, w_s))
    rate_difference = abs(1.0 / est_s - 1.0 / est_l)
    with pd.ExcelWriter(run_dir / "dual_pore_responses.xlsx") as writer:
        pd.DataFrame({"time_ms": times, "large_uncoupled": large, "small_uncoupled": small, "large_coupled": coupled_l, "small_coupled": coupled_s}).to_excel(
            writer, sheet_name="signals", index=False)
        pd.DataFrame({"T2_ms": axis, "uncoupled": unc, "coupled": cpl}).to_excel(writer, sheet_name="T2_spectra", index=False)
    figure = figures.figure_coupling({"large_side_um": large_side_um, "small_side_um": small_side_um, "k_ex_per_ms": k_ex, "t2_axis_ms": axis,
                                      "uncoupled_spectrum": unc, "coupled_spectrum": cpl, "mesh_segments": segments}, run_dir)
    summary = {
        "case": "dual_pore_exchange",
        "large_side_um": large_side_um,
        "small_side_um": small_side_um,
        "volume_weights": {"large": w_l, "small": w_s},
        "exchange_length_um": exchange.exchange_length_um,
        "effective_diffusion_um2_per_ms": exchange.effective_diffusion_um2_per_ms,
        "k_ex_per_ms": k_ex,
        "time_step_ms": exchange.time_step_ms,
        "isolated_pore_fast_diffusion_T2_ms": {"large": est_l, "small": est_s},
        "fast_exchange_limit_T2_ms": fast_exchange,
        "relaxation_rate_difference_per_ms": rate_difference,
        "k_ex_over_rate_difference": k_ex / rate_difference if rate_difference > 0 else None,
        "uncoupled_peaks_ms": peaks(unc),
        "coupled_peaks_ms": peaks(cpl),
        "meshes": meshes,
        "settings": settings.as_dict(),
        "inversion": {**grids.as_dict(), "note": "compartment spectra fitted separately and summed"},
        "interpretation_basis": "Two populations stay separate only while k_ex is small compared with the difference of their relaxation rates (McCall et al., 1991).",
    }
    (run_dir / "summary.json").write_text(json.dumps(_jsonable(summary), indent=2), encoding="utf-8")
    return {"summary": summary, "artifacts": [str(figure), str(figure.with_suffix(".pdf")), str(run_dir / "dual_pore_responses.xlsx"), str(run_dir / "summary.json")],
            "run_dir": str(run_dir)}


# ---------------------------------------------------------------------------
# Segmented CT slice on the pixel grid (Fig. 9)
# ---------------------------------------------------------------------------

def run_slice_pixel_fv(output_base: Path, image_path: Path, *, pixel_size_um: float, phase_values: dict[str, int], clean: bool = True,
                       fixed_alpha: float = 1.0, progress: Progress = None) -> dict:
    from PIL import Image

    from . import slice_fv as F

    raw = np.asarray(Image.open(image_path))
    if raw.ndim > 2:
        raw = raw[..., 0]
    present = {int(v) for v in np.unique(raw)}
    named = {int(v) for v in phase_values.values() if v is not None}
    background = phase_values.get("background")
    if background is None:
        if present - named:
            raise ValueError(f"Pixel values {sorted(present - named)} are not assigned to a phase; state the background value.")
        # No background pixels: use an unused label so nothing is treated as outside.
        background = next(v for v in range(256) if v not in present and v not in named)
    settings = F.SliceSettings(
        pixel_size_um=float(pixel_size_um),
        solid_value=int(phase_values["solid"]),
        water_value=int(phase_values["water"]),
        air_value=int(phase_values["air"]) if phase_values.get("air") is not None else next(v for v in range(256) if v not in present and v not in named and v != background),
        outside_value=int(background),
        smooth_radius_px=2 if clean else 0,
        interface_sigma_px=1.25 if clean else 0.0,
    )
    run_dir = _run_dir(output_base, "ct_slice_pixel_fv")
    _note(progress, "Cleaning labels")
    labels = F.classify_and_clean(raw, settings) if clean else raw.astype(np.uint8)
    Image.fromarray(labels).save(run_dir / "cleaned_labels.tif")
    _note(progress, "Solving the pixel-grid decay")
    _, laplacian, sink = F.build_water_operator(labels, settings)
    signal = F.solve_decay(laplacian, sink, settings)
    axis = settings.t2_axis_ms
    _note(progress, "L-curve inversion")
    spectrum, alpha, metrics = I.invert_t2_lcurve_slice(settings.times_ms, signal, axis)
    fixed = I.invert_t2_fixed_slice(settings.times_ms, signal, axis, fixed_alpha)
    fit = np.exp(-settings.times_ms[:, None] / axis[None, :]) @ spectrum
    stats = F.phase_statistics(labels, settings)
    diameters = F.local_thickness_um(labels, settings, "pore")
    water_diameters = F.local_thickness_um(labels, settings, "water")
    from ..literature import water_regions_from_labels

    encoded = np.full(labels.shape, 3, dtype=np.uint8)  # 1 water, 2 solid, 0 background, 3 air
    encoded[labels == settings.water_value] = 1
    encoded[labels == settings.solid_value] = 2
    encoded[labels == settings.outside_value] = 0
    regions = water_regions_from_labels(encoded, settings.pixel_size_um, settings.rho_um_per_ms, settings.t2_bulk_ms)
    peak = I.peak_position(axis, spectrum)
    with pd.ExcelWriter(run_dir / "slice_responses.xlsx") as writer:
        pd.DataFrame({"time_ms": settings.times_ms, "signal": signal, "fit": fit}).to_excel(writer, sheet_name="signal_and_fit", index=False)
        pd.DataFrame({"T2_ms": axis, "lcurve": spectrum, "fixed": fixed}).to_excel(writer, sheet_name="T2_spectrum", index=False)
        pd.DataFrame({k: v for k, v in metrics.items() if k != "best_index"}).to_excel(writer, sheet_name="L_curve", index=False)
    figure = figures.figure_slice({
        "labels": labels, "pixel_size_um": settings.pixel_size_um,
        "phase_values": {"solid": settings.solid_value, "water": settings.water_value, "air": settings.air_value},
        "local_diameter_um": diameters, "times_ms": settings.times_ms, "signal": signal, "fit": fit, "t2_axis_ms": axis,
        "spectrum_lcurve": spectrum, "spectrum_fixed": fixed, "alpha": alpha, "fixed_alpha": fixed_alpha, "statistics": stats,
    }, run_dir)
    bulk_share = peak / settings.t2_bulk_ms  # (1/T2b) / (1/T2peak)
    summary = {
        "case": "ct_slice_pixel_fv",
        "image_shape": list(raw.shape),
        "pixel_size_um": settings.pixel_size_um,
        "phase_values": phase_values,
        "labels_cleaned": clean,
        "statistics": stats,
        "selected_alpha": alpha,
        "peak_T2_ms": peak,
        "bulk_relaxation_share_of_rate_at_peak": bulk_share,
        "median_local_diameter_pore_space_um": float(np.median(diameters)) if diameters.size else None,
        "median_local_diameter_water_phase_um": float(np.median(water_diameters)) if water_diameters.size else None,
        "water_regions": regions,
        "fit_relative_l2": float(np.linalg.norm(fit - signal) / np.linalg.norm(signal)),
        "grid": {"bins": int(axis.size), "max_ms": float(axis[-1])},
        "settings": {k: v for k, v in settings.__dict__.items()},
        "solver": "finite-volume pixel grid, implicit Euler; surface relaxation on water faces against solid, background and the image edge",
        "interpretation_basis": "Bulk relaxation share = T2_peak / T2_bulk. water_regions gives the disconnected water regions: the largest region and the smaller isolated ones (share and S/V-based T2); smaller regions relax faster and form the short-T2 side of the peak. Describe connectivity only from these numbers. The water-phase median local diameter is the one to compare with a pore size derived from T2.",
    }
    (run_dir / "summary.json").write_text(json.dumps(_jsonable(summary), indent=2), encoding="utf-8")
    return {"summary": summary, "artifacts": [str(figure), str(figure.with_suffix(".pdf")), str(run_dir / "slice_responses.xlsx"), str(run_dir / "summary.json")],
            "run_dir": str(run_dir)}
