from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from t2_agent.simulation_2d import (
    RuleGeometry2D,
    SOLID,
    Simulation2DParams,
    WATER,
    build_rule_geometry_labels,
    build_triangular_water_mesh,
    save_pygimli_mesh,
    inspect_png_phase_map,
    normalize_png_phase_colors,
    run_png_mesh_decay,
    run_reduced_t2_t2_from_spectrum_workbook,
    run_rule_geometry_mesh_decay,
    write_standard_decay_workbook,
)


def _write_phase_png(path: Path) -> None:
    rgb = np.full((10, 12, 3), 255, dtype=np.uint8)
    rgb[2:8, 2:10] = [255, 255, 0]
    rgb[3:7, 4:8] = [255, 0, 0]
    Image.fromarray(rgb, mode="RGB").save(path)


def test_inspect_png_phase_map_crops_white_border_and_counts_phases(tmp_path: Path):
    png_path = tmp_path / "phase.png"
    _write_phase_png(png_path)

    result = inspect_png_phase_map(png_path, tmp_path / "inspect")

    assert result.status == "success"
    assert result.raw_shape == [10, 12]
    assert result.cropped_shape == [6, 8]
    assert result.phase_counts["water_px"] == 16
    assert result.phase_counts["solid_px"] == 32
    assert result.phase_counts["outside_px"] == 0
    assert result.cropped_png.exists()
    assert result.preview_png.exists()
    assert result.labels.shape == (6, 8)
    assert np.count_nonzero(result.labels == WATER) == 16
    assert np.count_nonzero(result.labels == SOLID) == 32


def test_inspect_png_phase_map_rejects_missing_water(tmp_path: Path):
    png_path = tmp_path / "solid.png"
    rgb = np.full((5, 5, 3), [255, 255, 0], dtype=np.uint8)
    Image.fromarray(rgb, mode="RGB").save(png_path)

    result = inspect_png_phase_map(png_path, tmp_path / "inspect")

    assert result.status == "failed"
    assert result.error == "no_liquid_pixels"


def test_inspect_png_phase_map_rejects_unexpected_colors(tmp_path: Path):
    png_path = tmp_path / "bad_colors.png"
    rgb = np.full((6, 6, 3), [255, 255, 0], dtype=np.uint8)
    rgb[2:4, 2:4] = [255, 0, 0]
    rgb[0, 0] = [0, 0, 255]
    Image.fromarray(rgb, mode="RGB").save(png_path)

    result = inspect_png_phase_map(png_path, tmp_path / "inspect")

    assert result.status == "failed"
    assert result.error == "unsupported_colors"


def test_normalize_png_phase_colors_maps_edge_colors_to_exact_phases(tmp_path: Path):
    png_path = tmp_path / "soft_edges.png"
    rgb = np.full((4, 4, 3), [255, 255, 255], dtype=np.uint8)
    rgb[1:3, 1:3] = [255, 255, 223]
    rgb[1, 1] = [255, 223, 223]
    rgb[2, 2] = [255, 0, 0]
    Image.fromarray(rgb, mode="RGB").save(png_path)

    result = normalize_png_phase_colors(png_path, tmp_path / "normalized")

    normalized = np.asarray(Image.open(result["normalized_png"]).convert("RGB"))
    colors = {tuple(color.tolist()) for color in np.unique(normalized.reshape(-1, 3), axis=0)}
    assert colors <= {(255, 255, 255), (255, 0, 0), (255, 255, 0)}
    assert result["unsupported_pixel_count_before"] > 0
    assert result["changed_pixel_count"] > 0


def test_write_standard_decay_workbook_uses_time_ms_signal_columns(tmp_path: Path):
    output = write_standard_decay_workbook(
        tmp_path / "decay.xlsx",
        time_ms=np.array([0.0, 5.0, 10.0]),
        signal=np.array([1.0, 0.8, 0.6]),
    )

    frame = pd.read_excel(output)

    assert list(frame.columns) == ["time_ms", "signal"]
    assert frame["time_ms"].tolist() == [0, 5, 10]
    assert frame["signal"].tolist() == [1.0, 0.8, 0.6]


def pygimli_available() -> bool:
    try:
        import pygimli  # noqa: F401
        import pygimli.meshtools  # noqa: F401
    except Exception:
        return False
    return True


@pytest.mark.skipif(not pygimli_available(), reason="pyGIMLi is not installed")
def test_run_png_mesh_decay_writes_mesh_decay_and_workbook(tmp_path: Path):
    png_path = tmp_path / "phase.png"
    _write_phase_png(png_path)
    params = Simulation2DParams(
        dt_ms=25.0,
        t_max_ms=50.0,
        max_grid_size=None,
        mesh_bulk_size_um=3.0,
        mesh_boundary_size_um=1.5,
        mesh_max_points=5000,
    )

    result = run_png_mesh_decay(
        png_path,
        tmp_path / "run",
        params,
        physical_size_x_um=80.0,
        physical_size_y_um=60.0,
    )

    assert result["status"] == "success"
    assert Path(result["mesh_png"]).exists()
    assert Path(result["pygimli_mesh_bms"]).exists()
    assert Path(result["mesh_quality_csv"]).exists()
    assert Path(result["mesh_quality_histogram_png"]).exists()
    assert Path(result["curve_csv"]).exists()
    assert Path(result["curve_png"]).exists()
    assert Path(result["standard_decay_xlsx"]).exists()
    assert result["time_point_count"] == 3
    assert result["physical_size_um"]["applied_after_white_border_crop"] is True
    assert result["base_pixel_size_um"] == {"x": 10.0, "y": 10.0}


def test_run_reduced_t2_t2_from_spectrum_workbook_writes_map_artifacts(tmp_path: Path):
    spectrum_path = tmp_path / "spectrum.xlsx"
    t2_ms = np.logspace(0, 3, 24)
    amplitude = np.exp(-((np.log10(t2_ms) - 2.0) ** 2) / 0.08)
    pd.DataFrame({"t2_ms": t2_ms, "amplitude": amplitude}).to_excel(spectrum_path, index=False)

    result = run_reduced_t2_t2_from_spectrum_workbook(
        spectrum_path,
        tmp_path / "t2_t2",
        alpha=0.02,
        t1_points=8,
        t2_points=9,
        bin_points=10,
    )

    assert result["status"] == "success"
    assert result["t2_t2_enabled"] is True
    assert Path(result["t2_t2_signal_csv"]).exists()
    assert Path(result["t2_t2_map_csv"]).exists()
    assert Path(result["t2_t2_map_xlsx"]).exists()
    assert Path(result["t2_t2_png"]).exists()
    map_frame = pd.read_csv(result["t2_t2_map_csv"], index_col=0)
    assert map_frame.shape == (10, 10)
    assert np.isclose(map_frame.to_numpy(dtype=float).sum(), 1.0)


def test_build_rule_geometry_labels_can_make_uncoupled_two_pore_domain():
    geometry = RuleGeometry2D(coupled=False, canvas_width_px=80, canvas_height_px=50)

    labels = build_rule_geometry_labels(geometry)

    assert labels.shape == (50, 80)
    assert np.count_nonzero(labels == WATER) > 0
    assert np.count_nonzero(labels == SOLID) > 0
    mid_col = labels[:, labels.shape[1] // 2]
    assert np.count_nonzero(mid_col == WATER) == 0


def test_build_rule_geometry_labels_can_make_coupled_throat():
    geometry = RuleGeometry2D(coupled=True, canvas_width_px=80, canvas_height_px=50, throat_width_px=6)

    labels = build_rule_geometry_labels(geometry)

    mid_col = labels[:, labels.shape[1] // 2]
    assert np.count_nonzero(mid_col == WATER) > 0


@pytest.mark.skipif(not pygimli_available(), reason="pyGIMLi is not installed")
def test_rule_geometry_mesh_decay_uses_ideal_triangle_input_not_generated_png(tmp_path: Path):
    geometry = RuleGeometry2D(coupled=True)
    params = Simulation2DParams(dt_ms=25.0, t_max_ms=50.0)

    result = run_rule_geometry_mesh_decay(geometry, tmp_path / "ideal_triangle", params)

    assert result["status"] == "success"
    assert result["geometry_mode"] == "rule"
    assert result["geometry_source"] == "builtin_ideal_triangle"
    assert "phase_png" not in result
    assert not (tmp_path / "ideal_triangle" / "input" / "rule_geometry_phase.png").exists()
    assert Path(result["standard_decay_xlsx"]).exists()
    assert result["modules"] == ["T2"]
    assert result["t2_t2_enabled"] is False
    assert result["dt2_enabled"] is False
    assert Path(result["t2_components_xlsx"]).exists()
    assert Path(result["t2_dashboard_png"]).exists()

    components = pd.read_excel(result["t2_components_xlsx"])
    assert {"T2_Time_ms", "IdealTriangle_Total", "IdealTriangle_Large", "IdealTriangle_Small"}.issubset(
        set(components.columns)
    )
    assert float(components["IdealTriangle_Total"].sum()) > 0.0
    np.testing.assert_allclose(
        components["IdealTriangle_Total"].to_numpy(dtype=float),
        (
            components["IdealTriangle_Large"].to_numpy(dtype=float)
            + components["IdealTriangle_Small"].to_numpy(dtype=float)
        ),
        rtol=1e-9,
        atol=1e-12,
    )
    assert float(components["IdealTriangle_Large"].sum()) > float(components["IdealTriangle_Small"].sum())


@pytest.mark.skipif(not pygimli_available(), reason="pyGIMLi is not installed")
def test_enclosed_solid_island_is_a_hole_in_the_mesh(tmp_path):
    import pygimli as pg

    labels = np.full((60, 60), WATER, dtype=np.uint8)
    yy, xx = np.mgrid[0:60, 0:60]
    labels[(yy - 30) ** 2 + (xx - 30) ** 2 <= 12**2] = SOLID  # grain fully surrounded by water
    params = Simulation2DParams(pixel_size_x_um=1.0, pixel_size_y_um=1.0, mesh_bulk_size_um=3.0, mesh_boundary_size_um=1.0)
    mesh = build_triangular_water_mesh(labels, params)
    raw = mesh["pygimli_mesh"]
    centres = np.array([[cell.center().x(), cell.center().y()] for cell in raw.cells()])
    inside = (centres[:, 0] - 30.5) ** 2 + (centres[:, 1] - 29.5) ** 2 < 10**2
    assert not inside.any()  # Triangle created no cells inside the grain
    assert mesh["plc_hole_contours"] == 1

    path = tmp_path / "mesh.bms"
    assert save_pygimli_mesh(mesh, path)
    assert pg.load(str(path)).cellCount() == len(mesh["triangles"])
