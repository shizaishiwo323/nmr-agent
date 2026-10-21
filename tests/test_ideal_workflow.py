import json
from pathlib import Path

import pandas as pd
import pytest

from t2_agent import ideal_workflow as iw
from t2_agent.agent import AgentRuntimeContext, execute_agent_tool
from tests.test_simulation_2d import pygimli_available


def _context(tmp_path: Path, prompt: str) -> AgentRuntimeContext:
    context = AgentRuntimeContext(workspace=tmp_path / "ws")
    context.last_user_goal = prompt
    return context


def test_prompt_parsing_and_missing_groups():
    values, explicit = iw.collect_prefill("跑一个不耦合的理想三角孔模拟，Sw=0.6", {})
    assert values["coupled"] is False
    assert values["large_water_saturation"] == pytest.approx(0.6)
    assert values["small_water_saturation"] == pytest.approx(0.6)
    missing = iw.missing_confirmation_fields(values, explicit)
    assert "coupling" not in missing and "saturation" not in missing
    assert {"geometry", "simulation_core", "run_lcurve", "run_gaussian"} <= set(missing)

    values, explicit = iw.collect_prefill("ideal triangle simulation", {"large_side_um": 30, "regularization": 0.5})
    assert values["run_lcurve"] is False
    assert "geometry" not in iw.missing_confirmation_fields(values, explicit)

    values, _ = iw.collect_prefill("", {"large_air_area_um2": iw.triangle_area_um2(20.0) * 0.25})
    assert values["large_water_saturation"] == pytest.approx(0.75)


def test_water_configuration_and_fast_diffusion_estimate():
    assert iw.water_configuration(1.0) == "full"
    assert iw.water_configuration(0.8) == "bubble"
    assert iw.water_configuration(0.3) == "corner"
    config = iw.IdealRunConfig()
    # Full equilateral triangle: S/V = 4*sqrt(3)/a.
    expected = 1.0 / (1.0 / 3000.0 + 0.005 * 4.0 * 3**0.5 / 20.0)
    assert iw.estimate_pore_t2_ms(config, "large") == pytest.approx(expected)
    axis = config.time_axis()
    assert axis["t_max_ms"] >= 5.0 * iw.estimate_pore_t2_ms(config, "large")
    assert config.to_tool_args()["large_air_area_um2"] == 0.0


def test_validation_blocks_coupled_corner_water_and_bad_sizes():
    assert iw.validate_config(iw.IdealRunConfig()) == []
    corner = iw.IdealRunConfig(large_water_saturation=0.3)
    assert any("角隅" in problem for problem in iw.validate_config(corner))
    assert iw.validate_config(iw.IdealRunConfig(large_water_saturation=0.3, coupled=False)) == []
    assert iw.validate_config(iw.IdealRunConfig(small_side_um=25.0))


def test_rule_simulation_waits_for_confirmation(tmp_path: Path):
    context = _context(tmp_path, "运行理想三角孔模拟和 T2 反演")
    result = execute_agent_tool("run_2d_simulation_full_workflow", {"geometry_mode": "rule"}, context)
    assert result.status == "needs_confirmation"
    assert result.error == "needs_ideal_parameter_confirmation"
    assert context.ideal_state["open_dialog"] == "ideal_params"
    assert not (context.workspace / "ideal_simulation").exists()


def test_geometry_preview_draws_every_water_configuration(tmp_path: Path):
    for sw, coupled in ((1.0, True), (0.7, True), (0.3, False)):
        config = iw.IdealRunConfig(large_water_saturation=sw, small_water_saturation=sw, coupled=coupled)
        path = iw.save_geometry_preview(config, tmp_path / f"preview_{sw}.png")
        assert path.stat().st_size > 0


@pytest.mark.skipif(not pygimli_available(), reason="pyGIMLi not installed")
def test_confirmed_ideal_workflow_runs_all_stages(tmp_path: Path):
    context = _context(tmp_path, "运行理想三角孔模拟")
    execute_agent_tool("run_2d_simulation_full_workflow", {"geometry_mode": "rule"}, context)
    iw.confirm_ideal_parameters(context, {"coupled": False, "large_side_um": 12.0, "small_side_um": 6.0, "ideal_mesh_area_um2": 0.2, "peak_count": 2})
    seen: list[str] = []
    context.stage_callback = lambda result: seen.append(str(result.summary.get("stage")))

    result = execute_agent_tool("run_2d_simulation_full_workflow", {"geometry_mode": "rule"}, context)

    assert result.status == "success", result.error
    assert seen == ["ideal_geometry", "ideal_mesh_decay", "ideal_t2_inversion", "ideal_gaussian", "ideal_interpretation"]
    run_dir = Path(result.summary["run_dir"])
    assert run_dir.parent.name == "ideal_simulation" and run_dir.name.startswith("uncoupled__")
    config = json.loads((run_dir / "00_geometry" / "ideal_run_config.json").read_text(encoding="utf-8"))
    assert config["confirmed_config"]["large_side_um"] == 12.0
    decay = pd.read_excel(result.summary["simulation_decay_xlsx"])
    signal = decay.iloc[:, -1].to_numpy(dtype=float)
    assert signal[-1] / signal[0] < 0.05  # automatic time axis lets the decay reach the baseline
    assert context.ideal_state["params_confirmed"] is False  # the next request asks again
    # The model receives the literature findings and AGU references in the aggregate summary.
    assert result.summary["literature_findings"] and result.summary["literature_references"]
    assert any("et al., " in finding or ", 19" in finding for finding in result.summary["literature_findings"])
