from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from t2_agent import ct_phase as ct
from t2_agent.agent import AgentRuntimeContext, execute_agent_tool
from t2_agent.ct_workflow import (
    confirm_phase_assignment,
    confirm_run_parameters,
    missing_confirmation_fields,
    set_background_answer,
)
from tests.test_simulation_2d import pygimli_available


def _synthetic_labels(background: bool = True, air: bool = True, water_value: int = 102) -> np.ndarray:
    """Circular sample: solid matrix (255), two water channels, an air patch (153), outside (0)."""

    size = 64
    yy, xx = np.mgrid[0:size, 0:size]
    image = np.full((size, size), 255, dtype=np.uint8)
    image[10:19, 4:60] = water_value
    image[36:45, 4:60] = water_value
    if air:
        image[12:17, 26:34] = 153
    if background:
        image[(yy - 31.5) ** 2 + (xx - 31.5) ** 2 > 30**2] = 0
    return image


def _write_tif(path: Path, image: np.ndarray) -> Path:
    Image.fromarray(image, mode="L").save(path)
    return path


def _context(tmp_path: Path, image: np.ndarray, prompt: str, name: str = "slice.tif") -> AgentRuntimeContext:
    tmp_path.mkdir(parents=True, exist_ok=True)
    tif = _write_tif(tmp_path / name, image)
    context = AgentRuntimeContext(workspace=tmp_path / "ws", uploaded_path=tif, uploaded_paths=[tif])
    context.last_user_goal = prompt
    return context


def test_prompt_parsers_cover_labels_background_resolution_and_choices():
    assert ct.parse_phase_labels("标签：255 固体、102 水、153 空气、0 外部", [0, 102, 153, 255]) == {
        "solid": 255,
        "water": 102,
        "air": 153,
        "background": 0,
    }
    assert ct.parse_phase_labels("固体=255，水=102", [0, 102, 255]) == {"solid": 255, "water": 102}
    assert ct.parse_phase_labels("像素尺度：4.6 μm/pixel", [0, 102, 255]) == {}
    assert ct.parse_background_statement("这张图含背景像素") is True
    assert ct.parse_background_statement("这张切片没有背景像素") is False
    assert ct.parse_background_statement("no background pixels here") is False
    assert ct.parse_background_statement("帮我跑NMR模拟") is None
    assert ct.parse_pixel_size_um("像素尺度：4.6 μm/pixel") == pytest.approx(4.6)
    assert ct.parse_pixel_size_um("分辨率是4.6微米每像素") == pytest.approx(4.6)
    assert ct.parse_pixel_size_um("pixel size 2 um") == pytest.approx(2.0)
    assert ct.parse_run_preferences("执行lCurve，执行高斯分峰，3个峰，其余参数默认") == {
        "run_lcurve": True,
        "run_gaussian": True,
        "peak_count": 3,
        "defaults_accepted": True,
    }
    prefs = ct.parse_run_preferences("不做L-curve，平滑因子0.5，不分峰")
    assert prefs == {"run_lcurve": False, "regularization": 0.5, "run_gaussian": False}


def test_two_value_image_never_asks_about_background(tmp_path: Path):
    context = _context(tmp_path, _synthetic_labels(background=False, air=False, water_value=125), "跑NMR模拟")
    result = execute_agent_tool("inspect_ct_phase_image", {}, context)
    assert result.error == "needs_phase_confirmation"
    assert context.ct_state["has_background"] is False
    assert context.ct_state["assignment"] == {"125": "water", "255": "solid"}


def test_three_values_without_statement_ask_about_background(tmp_path: Path):
    context = _context(tmp_path, _synthetic_labels(background=True, air=False), "跑NMR模拟")
    result = execute_agent_tool("inspect_ct_phase_image", {}, context)
    assert result.status == "needs_confirmation"
    assert result.error == "needs_background_answer"
    assert context.ct_state["step"] == "background"

    answered = set_background_answer(context, True)
    assert answered.error == "needs_phase_confirmation"
    assert context.ct_state["assignment"] == {"0": "background", "102": "water", "255": "solid"}
    assert context.ct_state["has_background_source"] == "user_ui"


def test_three_values_with_no_background_statement_guess_air(tmp_path: Path):
    context = _context(tmp_path, _synthetic_labels(background=False, air=True), "这张图没有背景像素，跑模拟")
    result = execute_agent_tool("inspect_ct_phase_image", {}, context)
    assert result.error == "needs_phase_confirmation"
    assert context.ct_state["assignment"] == {"102": "water", "153": "air", "255": "solid"}


def test_four_values_ai_guess_and_prompt_labels_agree(tmp_path: Path):
    image = _synthetic_labels(background=True, air=True)
    context = _context(tmp_path, image, "含背景，跑模拟")
    execute_agent_tool("inspect_ct_phase_image", {}, context)
    assert context.ct_state["ai_assignment"] == {"0": "background", "102": "water", "153": "air", "255": "solid"}
    assert context.ct_state["assignment_source"] == "ai"

    labelled = _context(tmp_path / "b", image, "标签：255 固体、102 水、153 空气、0 外部；4.6 μm/pixel")
    execute_agent_tool("inspect_ct_phase_image", {}, labelled)
    assert labelled.ct_state["has_background"] is True
    assert labelled.ct_state["assignment_source"] == "prompt"
    assert labelled.ct_state["prompt_agrees_with_ai"] is True
    assert labelled.ct_state["prefill"]["pixel_size_um"] == pytest.approx(4.6)


def test_unsegmented_image_is_rejected(tmp_path: Path):
    image = np.arange(64 * 64, dtype=np.uint16).reshape(64, 64) % 37
    context = _context(tmp_path, image.astype(np.uint8), "跑模拟")
    result = execute_agent_tool("inspect_ct_phase_image", {}, context)
    assert result.status == "failed"
    assert result.error == "not_segmented"


def test_reassign_phase_swaps_and_validation():
    assignment = {"0": "background", "102": "water", "153": "air", "255": "solid"}
    swapped = ct.reassign_phase(assignment, "153", "water")
    assert swapped == {"0": "background", "102": "air", "153": "water", "255": "solid"}
    assert ct.validate_assignment(swapped, [0, 102, 153, 255], True) == []
    assert ct.validate_assignment({"0": "background", "102": "air", "255": "solid"}, [0, 102, 255], True)


def test_marker_events_apply_once_and_bump_revision():
    from t2_agent.ct_ui import apply_marker_event

    state = {"values": [102, 255], "assignment": {"102": "water", "255": "solid"}, "revision": 3}
    event = {"event_id": "e1", "revision": 3, "assignment": {"102": "solid", "255": "water"}, "markers": {"solid": [1, 2], "water": [3, 4]}}
    assert apply_marker_event(state, event) is True
    assert state["assignment"] == {"102": "solid", "255": "water"}
    assert state["revision"] == 4
    assert apply_marker_event(state, event) is False
    stale = {"event_id": "e2", "revision": 3, "assignment": {"102": "water", "255": "solid"}, "markers": {}}
    assert apply_marker_event(state, stale) is False
    assert state["assignment"] == {"102": "solid", "255": "water"}


def test_missing_confirmation_fields_drive_parameter_dialog():
    assert missing_confirmation_fields({}, []) == ["pixel_size_um", "run_lcurve", "run_gaussian", "simulation_core"]
    full = {"pixel_size_um": 4.6, "run_lcurve": True, "run_gaussian": True, "defaults_accepted": True}
    assert missing_confirmation_fields(full, list(full)) == []
    fixed = {"pixel_size_um": 4.6, "run_lcurve": False, "run_gaussian": False}
    assert "regularization" in missing_confirmation_fields(fixed, list(fixed))


def test_run_waits_for_confirmation_and_reinspect_keeps_confirmed_phases(tmp_path: Path):
    context = _context(tmp_path, _synthetic_labels(background=True, air=True), "含背景")
    execute_agent_tool("inspect_ct_phase_image", {}, context)
    pending = execute_agent_tool("run_ct_simulation_workflow", {}, context)
    assert pending.status == "needs_confirmation"
    assert pending.error == "needs_phase_confirmation"

    corrected = ct.reassign_phase(context.ct_state["assignment"], "153", "water")
    confirmed = confirm_phase_assignment(context, corrected)
    assert confirmed.status == "success"
    assert context.ct_state["step"] == "params"
    assert set(context.ct_state["user_corrections"]) == {"102", "153"}

    again = execute_agent_tool("inspect_ct_phase_image", {}, context)
    assert again.status == "success"
    assert context.ct_state["assignment"] == corrected
    assert context.ct_state["phase_confirmed"] is True

    waiting = execute_agent_tool("run_ct_simulation_workflow", {}, context)
    assert waiting.error == "needs_parameter_confirmation"


@pytest.mark.skipif(not pygimli_available(), reason="pyGIMLi is required for the CT mesh workflow")
def test_confirmed_ct_workflow_runs_all_stages(tmp_path: Path):
    context = _context(tmp_path, _synthetic_labels(background=True, air=True), "含背景")
    execute_agent_tool("inspect_ct_phase_image", {}, context)
    confirm_phase_assignment(context, dict(context.ct_state["assignment"]))
    confirm_run_parameters(context, {"pixel_size_um": 4.6, "run_lcurve": True, "run_gaussian": True, "peak_count": 2})
    seen: list[str] = []
    context.stage_callback = lambda result: seen.append(str(result.summary.get("stage")))

    result = execute_agent_tool("run_ct_simulation_workflow", {}, context)

    assert result.status == "success", result.error
    assert seen == ["ct_geometry", "ct_mesh", "ct_decay", "ct_t2_inversion", "ct_gaussian", "ct_interpretation"]
    assert all(item["status"] == "success" for item in result.summary["stage_status"])
    assert result.summary["mesh"]["gas_liquid_boundary_length_um"] > 0
    assert result.summary["mesh"]["solid_liquid_boundary_length_um"] > 0
    decay = pd.read_excel(result.summary["simulation_decay_xlsx"])
    assert decay["signal"].iloc[0] == pytest.approx(1.0)
    assert decay["signal"].iloc[-1] < 0.2
    assert Path(result.summary["spectrum_xlsx"]).exists()
    assert result.summary.get("metrics_xlsx")
    assert context.ct_state["step"] == "done"


CT_TEST_DATA = Path(__file__).resolve().parents[1] / "testData" / "ct_tif"
REAL_CT_CASES = [
    ("solid_water_2phase.tif", None, {"125": "water", "255": "solid"}),
    ("solid_water_air_3phase.tif", False, {"102": "water", "153": "air", "255": "solid"}),
    ("solid_water_back3phase.tif", True, {"0": "background", "125": "water", "255": "solid"}),
    ("solid_water_air_back4phase.tif", True, {"0": "background", "102": "water", "153": "air", "255": "solid"}),
]


@pytest.mark.parametrize(("name", "has_background", "expected"), REAL_CT_CASES)
def test_real_ct_tifs_background_rule_and_ai_guess(tmp_path: Path, name: str, has_background, expected):
    tif = CT_TEST_DATA / name
    context = AgentRuntimeContext(workspace=tmp_path / "ws", uploaded_path=tif, uploaded_paths=[tif])
    context.last_user_goal = "用这张CT图跑NMR模拟"

    first = execute_agent_tool("inspect_ct_phase_image", {}, context)
    if has_background is None:
        assert first.error == "needs_phase_confirmation"
    else:
        assert first.error == "needs_background_answer"
        first = set_background_answer(context, has_background)
        assert first.error == "needs_phase_confirmation"
    assert context.ct_state["assignment"] == expected
    assert context.ct_state["ai_confidence"] == "high"


@pytest.mark.skipif(not pygimli_available(), reason="pyGIMLi is required for meshing")
@pytest.mark.parametrize(("name", "has_background", "expected"), REAL_CT_CASES)
def test_real_ct_mesh_covers_whole_water_domain(name: str, has_background, expected):
    """Water touching the image edge must be meshed, not dropped (open-contour regression)."""

    from t2_agent import simulation_2d as sim

    array, _meta = ct.load_label_image(CT_TEST_DATA / name)
    labels = ct.apply_phase_assignment(array, expected)
    if has_background:
        labels, _bbox = ct.crop_to_sample(labels)
    params, _estimate = ct.simulation_params_for(ct.CtRunConfig(pixel_size_um=4.6), labels)
    _mesh, _k, mass, solid_robin, gas_robin, stats = sim.assemble_triangular_operator(labels, params, ct.ct_edge_classifier)

    water_area = np.count_nonzero(labels == sim.WATER) * params.pixel_size_x_um * params.pixel_size_y_um
    assert float(np.sum(mass)) / water_area > 0.97
    assert stats["solid_liquid_boundary_length_um"] > 0
    if not has_background:
        # Pores cut by the image edge get reflecting (no-flux) boundaries.
        assert stats["noflux_boundary_length_um"] > 0
    if "air" in expected.values():
        assert stats["gas_liquid_boundary_length_um"] > 0
