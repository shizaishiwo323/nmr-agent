"""Checks of the ported paper calculations against values reported in the manuscript."""

import math
from pathlib import Path

import numpy as np
import pytest

from t2_agent.agent import AgentRuntimeContext, build_tool_specs, execute_agent_tool
from t2_agent.paper_sim import exchange as X
from t2_agent.paper_sim import geometry as G
from t2_agent.paper_sim import inversion as I
from t2_agent.paper_sim.settings import InversionGrids, PaperSettings

pytest.importorskip("pygimli")


def test_corner_water_area_and_limits():
    water = G.corner_water(0.153, 30.0, 20.0, arc_points=2000)
    area = sum(G.polygon_area(p) for p in water.polygons)
    assert area / G.equilateral_area(20.0) == pytest.approx(0.153, rel=2e-3)
    assert G.corner_water_limits(0.0)["max_saturation"] == pytest.approx(1 - math.pi / (3 * math.sqrt(3)), rel=1e-9)
    assert G.corner_water_limits(60.0)["max_saturation"] == 0.0
    with pytest.raises(ValueError):
        G.corner_water(0.5, 0.0, 20.0)


def test_equal_area_shapes_have_equal_area():
    area = G.equilateral_area(20.0)
    for polygon in G.shape_polygons(area).values():
        assert G.polygon_area(polygon) == pytest.approx(area, rel=1e-9)


def test_exchange_conserves_magnetization_without_relaxation():
    times = np.arange(0.0, 200.0, 2.0)
    large = 0.9 * np.ones_like(times)
    small = 0.1 * np.ones_like(times)
    coupled_l, coupled_s = X.apply_exchange(large, small, times, 0.0667)
    np.testing.assert_allclose(coupled_l + coupled_s, 1.0, atol=1e-12)
    np.testing.assert_allclose(coupled_l, large, atol=1e-12)  # equal densities stay equal


def test_saturated_triangle_peak_matches_paper():
    from t2_agent.paper_sim import fem

    settings = PaperSettings(maximum_triangle_area_um2=0.2)
    mesh = G.build_mesh(G.saturated_polygon_geometry(G.equilateral_vertices(20.0)), settings.maximum_triangle_area_um2)
    signal, _ = fem.solve_t2(mesh, settings)
    grids = InversionGrids()
    spectrum = I.invert_t2_controlled(settings.t2_times_ms, signal, grids.t2_axis_ms, grids.t2_alpha)
    assert I.peak_position(grids.t2_axis_ms, spectrum) == pytest.approx(478, rel=0.03)


def test_paper_tools_are_registered():
    names = {spec["function"]["name"] for spec in build_tool_specs()}
    assert {"simulate_pore_shapes", "simulate_saturation_series", "simulate_contact_angle_series",
            "simulate_dual_pore_exchange", "simulate_ct_slice_pixel_grid"} <= names


def test_dual_pore_tool_reproduces_merged_peak(tmp_path):
    context = AgentRuntimeContext(workspace=tmp_path)
    result = execute_agent_tool("simulate_dual_pore_exchange", {}, context, response_language="English")
    assert result.status == "success", result.message
    assert len(result.summary["uncoupled_peaks_ms"]) == 2
    assert len(result.summary["coupled_peaks_ms"]) == 1
    assert result.summary["coupled_peaks_ms"][0] == pytest.approx(450, rel=0.03)
    assert Path(result.artifacts[0]).suffix == ".png" and Path(result.artifacts[0]).exists()


def test_saturation_tool_rejects_merged_corner_state(tmp_path):
    context = AgentRuntimeContext(workspace=tmp_path)
    result = execute_agent_tool("simulate_saturation_series", {"saturations": [60]}, context, response_language="English")
    assert result.status == "failed" and result.error == "invalid_parameters"


def test_ct_pixel_tool_asks_for_missing_inputs(tmp_path):
    from PIL import Image

    image = tmp_path / "slice.tif"
    labels = np.full((20, 20), 255, dtype=np.uint8)
    labels[5:15, 5:15] = 102
    Image.fromarray(labels).save(image)
    context = AgentRuntimeContext(workspace=tmp_path, uploaded_path=image)
    result = execute_agent_tool("simulate_ct_slice_pixel_grid", {}, context, response_language="English")
    assert result.status == "failed" and result.error == "missing_ct_inputs"
    result = execute_agent_tool("simulate_ct_slice_pixel_grid", {"pixel_size_um": 4.6, "phase_labels": {"solid": 255, "water": 102}, "clean_labels": False},
                                context, response_language="English")
    assert result.status == "success", result.message
    assert result.summary["statistics"]["water_saturation"] == pytest.approx(1.0)
