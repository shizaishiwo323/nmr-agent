from pathlib import Path
from zipfile import ZipFile
import io
import inspect

import pandas as pd
import pytest

from t2_agent.agent import AgentRuntimeContext
from t2_agent.models import AgentToolResult
import streamlit_app
from streamlit_app import (
    DEFAULT_MODEL,
    DEFAULT_THINKING_ENABLED,
    INTRO_QUERY_KEY,
    TURN_ARTIFACT_EXPANDER_MARKER_CLASS,
    TURN_RESULT_EXPANDER_MARKER_CLASS,
    artifact_kind,
    collect_turn_artifacts,
    clear_query_param,
    enhance_report_with_conversation,
    exportable_assistant_analysis,
    group_simulation_stage_artifacts,
    make_zip,
    query_param_enabled,
    render_artifact_chip,
    render_turn_artifacts,
    render_turn_result_sections,
    resolve_artifact_image_reference,
    selected_alpha_fixed_nnls_params,
    should_run_local_demo_without_api,
    should_offer_lcurve_parameter_picker,
    lcurve_picker_state_keys,
    lcurve_source_decay_path,
    stop_if_runtime_environment_invalid,
    turn_image_paths_for_display,
    turn_scoped_result_for_display,
    turn_result_groups,
    workspace_style_css,
)


def test_default_chat_model_uses_deepseek_pro_thinking_mode():
    assert DEFAULT_MODEL == "deepseek-v4-pro"
    assert DEFAULT_THINKING_ENABLED is True


def test_runtime_environment_guard_stops_streamlit_when_invalid(monkeypatch):
    calls: list[tuple[str, str]] = []

    class FakeStreamlit:
        def error(self, message):
            calls.append(("error", message))

        def code(self, message):
            calls.append(("code", message))

        def stop(self):
            raise RuntimeError("stopped")

    monkeypatch.setattr(streamlit_app, "st", FakeStreamlit())

    with pytest.raises(RuntimeError, match="stopped"):
        stop_if_runtime_environment_invalid(
            streamlit_app.RuntimeEnvironmentStatus(
                False,
                "bad runtime",
                "3.14.6",
                "C:/Python314/python.exe",
                "C:/Python314",
                True,
            )
        )

    assert ("error", "This Streamlit process is not using the verified T2/pyGIMLi runtime environment.") in calls
    assert ("code", "bad runtime") in calls


def test_workspace_style_keeps_first_chat_message_above_fixed_input():
    css = streamlit_app.workspace_style_css()

    assert ".st-key-t2_chat_history_panel" in css
    assert "display: flex;" in css
    assert "flex-direction: column;" in css
    assert "justify-content: flex-start;" in css
    assert "padding-bottom: var(--t2-chat-input-clearance);" in css
    assert "min-height: max(360px, calc(100vh - 430px)) !important;" in css
    assert "scroll-padding-bottom: var(--t2-chat-input-clearance);" in css


def test_live_agent_turns_can_render_inside_chat_history_panel():
    assert "live_chat_container" in inspect.signature(streamlit_app.run_agent_prompt).parameters
    assert "live_chat_container" in inspect.signature(streamlit_app.run_local_demo_prompt).parameters
    assert "live_chat_container" in inspect.signature(streamlit_app.run_offline_debug_prompt).parameters


def test_agent_tool_result_can_carry_simulation_stage_metadata():
    result = AgentToolResult(
        "success",
        "mesh generated",
        artifacts=["mesh.png"],
        summary={"stage": "mesh", "simulation_stages": {"mesh": ["mesh.png"]}},
    )

    assert result.summary["stage"] == "mesh"
    assert result.summary["simulation_stages"]["mesh"] == ["mesh.png"]


def test_group_simulation_stage_artifacts_uses_summary_stage_map(tmp_path):
    mesh = tmp_path / "mesh.png"
    decay = tmp_path / "decay.png"
    mesh.write_bytes(b"mesh")
    decay.write_bytes(b"decay")
    result = AgentToolResult(
        "success",
        "ok",
        artifacts=[str(mesh), str(decay)],
        summary={"simulation_stages": {"mesh": [str(mesh)], "decay": [str(decay)]}},
    )

    grouped = group_simulation_stage_artifacts(result)

    assert grouped["mesh"] == [mesh]
    assert grouped["decay"] == [decay]


def test_resolve_artifact_image_reference_matches_stem_and_basename(tmp_path):
    image_path = tmp_path / "ExperimentalDecay__amplitude__decay_t2.png"
    image_path.write_bytes(b"fake-png")
    lcurve_path = tmp_path / "amplitude__lcurve.png"
    lcurve_path.write_bytes(b"fake-png")

    artifacts = [image_path, lcurve_path]

    assert resolve_artifact_image_reference("decay_t2", artifacts) == image_path
    assert resolve_artifact_image_reference("amplitude__lcurve.png", artifacts) == lcurve_path


def test_artifact_kind_groups_figures_tables_and_reports():
    assert artifact_kind(Path("plot.png")) == "image"
    assert artifact_kind(Path("spectrum.xlsx")) == "table"
    assert artifact_kind(Path("summary.csv")) == "table"
    assert artifact_kind(Path("report.md")) == "report"
    assert artifact_kind(Path("notes.bin")) == "file"


def test_collect_turn_artifacts_keeps_existing_unique_files(tmp_path):
    figure = tmp_path / "decay_t2.png"
    table = tmp_path / "summary.xlsx"
    missing = tmp_path / "missing.csv"
    figure.write_bytes(b"figure")
    table.write_bytes(b"table")

    artifacts = collect_turn_artifacts(
        [
            AgentToolResult("success", "first", artifacts=[str(figure), str(table)]),
            AgentToolResult("success", "duplicate", artifacts=[str(figure), str(missing)]),
        ]
    )

    assert artifacts == [str(figure), str(table)]


def test_artifact_chip_previews_table_even_in_compact_mode(monkeypatch, tmp_path):
    table_path = tmp_path / "summary.xlsx"
    pd.DataFrame({"t2_ms": [1.0, 10.0], "amplitude": [0.2, 0.8]}).to_excel(table_path, index=False)
    calls: list[tuple[str, object]] = []

    class FakeStreamlit:
        def markdown(self, *_args, **_kwargs):
            return None

        def caption(self, *_args, **_kwargs):
            return None

        def dataframe(self, data, **_kwargs):
            calls.append(("dataframe", data))

        def download_button(self, *_args, **_kwargs):
            calls.append(("download", None))

    monkeypatch.setattr(streamlit_app, "st", FakeStreamlit())

    render_artifact_chip(table_path, "中文", "artifact-preview", compact=True)

    dataframe_calls = [item for name, item in calls if name == "dataframe"]
    assert len(dataframe_calls) == 1
    assert list(dataframe_calls[0].columns) == ["t2_ms", "amplitude"]
    assert ("download", None) in calls


def test_turn_artifacts_renders_every_file_in_left_chat(monkeypatch, tmp_path):
    files = []
    for index in range(8):
        path = tmp_path / f"artifact_{index}.txt"
        path.write_text(f"artifact {index}", encoding="utf-8")
        files.append(path)

    calls: list[tuple[str, object]] = []

    class FakeExpander:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeStreamlit:
        def expander(self, *_args, **_kwargs):
            return FakeExpander()

        def markdown(self, *_args, **_kwargs):
            return None

        def caption(self, message, *_args, **_kwargs):
            calls.append(("caption", message))

        def download_button(self, *_args, **_kwargs):
            calls.append(("download", None))

    monkeypatch.setattr(streamlit_app, "st", FakeStreamlit())

    render_turn_artifacts([str(path) for path in files], "中文", 0)

    assert [name for name, _item in calls].count("download") == len(files)
    assert not any("还有" in str(item) for name, item in calls if name == "caption")


def test_turn_artifact_expander_header_is_sticky_only_in_chat_history(monkeypatch, tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("artifact", encoding="utf-8")
    calls: list[tuple[str, object]] = []

    class FakeExpander:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeStreamlit:
        def expander(self, label, *_args, **_kwargs):
            calls.append(("expander", label))
            return FakeExpander()

        def markdown(self, message, *_args, **_kwargs):
            calls.append(("markdown", message))

        def caption(self, message, *_args, **_kwargs):
            calls.append(("caption", message))

        def download_button(self, *_args, **_kwargs):
            calls.append(("download", None))

    monkeypatch.setattr(streamlit_app, "st", FakeStreamlit())

    render_turn_artifacts([str(artifact)], "中文", 0)

    css = workspace_style_css()
    assert any(TURN_ARTIFACT_EXPANDER_MARKER_CLASS in str(item) for name, item in calls if name == "markdown")
    assert "st-key-t2_chat_history_panel" in css
    assert TURN_ARTIFACT_EXPANDER_MARKER_CLASS in css
    assert "position: sticky" in css


def test_turn_result_expander_header_is_sticky_only_in_results_panel(monkeypatch, tmp_path):
    calls: list[tuple[str, object]] = []

    class FakeExpander:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeStreamlit:
        session_state = {
            "display_messages": [("user", "第二轮"), ("assistant", "完成")],
            "display_tool_results": [[], [AgentToolResult("success", "ok")]],
            "display_artifacts": [[], []],
            "live_turn_tool_results": [],
        }

        def info(self, message, *_args, **_kwargs):
            calls.append(("info", message))

        def expander(self, label, *_args, **_kwargs):
            calls.append(("expander", label))
            return FakeExpander()

        def markdown(self, message, *_args, **_kwargs):
            calls.append(("markdown", message))

        def caption(self, message, *_args, **_kwargs):
            calls.append(("caption", message))

        def success(self, message, *_args, **_kwargs):
            calls.append(("success", message))

        def error(self, message, *_args, **_kwargs):
            calls.append(("error", message))

        def code(self, message, *_args, **_kwargs):
            calls.append(("code", message))

        def json(self, message, *_args, **_kwargs):
            calls.append(("json", message))

        def image(self, *_args, **_kwargs):
            calls.append(("image", None))

    monkeypatch.setattr(streamlit_app, "st", FakeStreamlit())

    render_turn_result_sections(AgentRuntimeContext(workspace=tmp_path), "中文")

    css = workspace_style_css()
    assert any(TURN_RESULT_EXPANDER_MARKER_CLASS in str(item) for name, item in calls if name == "markdown")
    assert "st-key-t2_results_scroll_panel" in css
    assert TURN_RESULT_EXPANDER_MARKER_CLASS in css
    assert "position: sticky" in css


def test_intro_query_preference_helpers(monkeypatch):
    query_params = {INTRO_QUERY_KEY: "1", "other": "kept"}
    monkeypatch.setattr(streamlit_app.st, "query_params", query_params)

    assert query_param_enabled(INTRO_QUERY_KEY) is True

    clear_query_param(INTRO_QUERY_KEY)

    assert INTRO_QUERY_KEY not in query_params
    assert query_params["other"] == "kept"


def test_should_run_local_demo_without_api_is_narrow():
    assert should_run_local_demo_without_api("请运行本地 NMR 理想三角 T2-T2 演示")
    assert should_run_local_demo_without_api("Run the local NMR ideal triangle T2-T2 demo")
    assert should_run_local_demo_without_api("用默认理想三角孔跑完整二维NMR模拟并做T2反演")
    assert not should_run_local_demo_without_api("我不懂参数，请自动做 T2 反演")
    assert not should_run_local_demo_without_api("用红黄 PNG 相图跑二维模拟")


def test_resolve_artifact_image_reference_rejects_non_images(tmp_path):
    table_path = tmp_path / "summary.csv"
    table_path.write_text("x,y\n1,2\n")

    assert resolve_artifact_image_reference("summary.csv", [table_path]) is None


def test_make_zip_preserves_batch_result_folders(tmp_path):
    file_a_report = tmp_path / "batch_results" / "sample_a.xlsx" / "report" / "report.md"
    file_b_report = tmp_path / "batch_results" / "sample_b.xlsx" / "report" / "report.md"
    file_a_report.parent.mkdir(parents=True)
    file_b_report.parent.mkdir(parents=True)
    file_a_report.write_text("a", encoding="utf-8")
    file_b_report.write_text("b", encoding="utf-8")

    zip_bytes = make_zip([file_a_report, file_b_report])

    with ZipFile(io.BytesIO(zip_bytes)) as archive:
        names = set(archive.namelist())

    assert "batch_results/sample_a.xlsx/report/report.md" in names
    assert "batch_results/sample_b.xlsx/report/report.md" in names


def test_make_zip_preserves_gaussian_peak_count_folders(tmp_path):
    peak_2 = tmp_path / "tasks" / "sample.xlsx" / "gaussian" / "peaks_2" / "sample__gaussian_figures" / "col_2__gaussian.png"
    peak_3 = tmp_path / "tasks" / "sample.xlsx" / "gaussian" / "peaks_3" / "sample__gaussian_figures" / "col_2__gaussian.png"
    peak_2.parent.mkdir(parents=True)
    peak_3.parent.mkdir(parents=True)
    peak_2.write_bytes(b"two")
    peak_3.write_bytes(b"three")

    zip_bytes = make_zip([peak_2, peak_3])

    with ZipFile(io.BytesIO(zip_bytes)) as archive:
        names = set(archive.namelist())

    assert "sample.xlsx/gaussian/peaks_2/sample__gaussian_figures/col_2__gaussian.png" in names
    assert "sample.xlsx/gaussian/peaks_3/sample__gaussian_figures/col_2__gaussian.png" in names


def test_make_zip_preserves_parameter_run_folders(tmp_path):
    run_a = tmp_path / "tasks" / "sample.xlsx" / "lcurve" / "bins_50__alpha_n_8" / "sample__lcurve_spectrum.xlsx"
    run_b = tmp_path / "tasks" / "sample.xlsx" / "lcurve" / "bins_80__alpha_n_10" / "sample__lcurve_spectrum.xlsx"
    run_a.parent.mkdir(parents=True)
    run_b.parent.mkdir(parents=True)
    run_a.write_bytes(b"a")
    run_b.write_bytes(b"b")

    zip_bytes = make_zip([run_a, run_b])

    with ZipFile(io.BytesIO(zip_bytes)) as archive:
        names = set(archive.namelist())

    assert "sample.xlsx/lcurve/bins_50__alpha_n_8/sample__lcurve_spectrum.xlsx" in names
    assert "sample.xlsx/lcurve/bins_80__alpha_n_10/sample__lcurve_spectrum.xlsx" in names


def test_should_offer_lcurve_parameter_picker_only_for_successful_lcurve_metrics(tmp_path):
    metrics_path = tmp_path / "sample__lcurve_metrics.xlsx"
    metrics_path.write_bytes(b"fake")
    lcurve_result = AgentToolResult(
        "success",
        "ok",
        summary={"metrics_xlsx": str(metrics_path)},
    )
    failed_result = AgentToolResult(
        "failed",
        "no",
        summary={"metrics_xlsx": str(metrics_path)},
    )
    missing_metrics = AgentToolResult("success", "ok", summary={"metrics_xlsx": str(tmp_path / "missing.xlsx")})

    assert should_offer_lcurve_parameter_picker(lcurve_result) is True
    assert should_offer_lcurve_parameter_picker(failed_result) is False
    assert should_offer_lcurve_parameter_picker(missing_metrics) is False


def test_selected_alpha_fixed_nnls_params_preserve_lcurve_settings():
    lcurve_result = AgentToolResult(
        "success",
        "ok",
        summary={
            "parameters": {
                "num_bins": 240,
                "t2_min_ms": 0.02,
                "t2_max_ms": 50000.0,
                "time_to_ms_scale": 1000.0,
                "trim_from_peak": False,
                "alpha_min": 0.001,
                "alpha_max": 10000.0,
                "alpha_count": 300,
            }
        },
    )

    params = selected_alpha_fixed_nnls_params(lcurve_result, 0.1234)

    assert params == {
        "regularization": 0.1234,
        "num_bins": 240,
        "t2_min_ms": 0.02,
        "t2_max_ms": 50000.0,
        "time_to_ms_scale": 1000.0,
        "trim_from_peak": False,
    }


def test_lcurve_picker_open_state_does_not_reuse_button_widget_key():
    keys = lcurve_picker_state_keys(0)

    assert keys["open_state"] != keys["open_button"]
    assert keys["open_state"].endswith("-state")
    assert keys["open_button"].endswith("-button")


def test_lcurve_picker_keys_can_be_scoped_to_chat_turns():
    first_turn = lcurve_picker_state_keys("turn-1-result-0")
    second_turn = lcurve_picker_state_keys("turn-2-result-0")

    assert first_turn["base"] != second_turn["base"]
    assert first_turn["open_button"] == "lcurve-alpha-picker-turn-1-result-0-open-button"
    assert second_turn["open_button"] == "lcurve-alpha-picker-turn-2-result-0-open-button"


def test_lcurve_picker_keys_include_result_files_to_prevent_turn_reuse():
    first_run = lcurve_picker_state_keys("turn-1-result-0", "metrics-a.xlsx", "decay-a.xlsx")
    second_run = lcurve_picker_state_keys("turn-1-result-0", "metrics-b.xlsx", "decay-b.xlsx")

    assert first_run["base"] != second_run["base"]
    assert first_run["open_button"] != second_run["open_button"]


def test_turn_result_groups_follow_assistant_message_turns():
    first = AgentToolResult("success", "first")
    second = AgentToolResult("success", "second")
    messages = [
        ("user", "第一轮"),
        ("assistant", "第一轮完成"),
        ("user", "第二轮"),
        ("assistant", "第二轮完成"),
    ]
    per_message_results = [[], [first], [], [second]]

    groups = turn_result_groups(messages, per_message_results)

    assert [group["turn_number"] for group in groups] == [1, 2]
    assert [group["message_index"] for group in groups] == [1, 3]
    assert [group["user_prompt"] for group in groups] == ["第一轮", "第二轮"]
    assert groups[0]["results"] == [first]
    assert groups[1]["results"] == [second]


def test_turn_image_paths_include_message_artifacts_not_present_in_tool_results(tmp_path):
    lcurve = tmp_path / "col_2__lcurve__20260619_111643_819.png"
    gaussian = tmp_path / "col_2__gaussian__20260619_111644_754.png"
    table = tmp_path / "col_2__gaussian_summary__20260619_111644_754.xlsx"
    for path in [lcurve, gaussian, table]:
        path.write_bytes(b"artifact")
    result = AgentToolResult("success", "workflow", artifacts=[str(lcurve)])

    paths = turn_image_paths_for_display([result], [str(lcurve), str(gaussian), str(table)])

    assert paths == [lcurve, gaussian]


def test_turn_scoped_full_workflow_result_filters_prior_lcurve_artifacts(tmp_path):
    current_decay = tmp_path / "ideal_triangle__standard_decay__20260619_110204_628.xlsx"
    old_lcurve = tmp_path / "col_2__lcurve__20260619_110123_282.png"
    current_metrics = tmp_path / "ideal_triangle__standard_decay__lcurve_metrics__20260619_110221_317.xlsx"
    current_lcurve = tmp_path / "col_2__lcurve__20260619_110221_317.png"
    for path in [current_decay, old_lcurve, current_metrics, current_lcurve]:
        path.write_bytes(b"artifact")
    result = AgentToolResult(
        "success",
        "workflow",
        artifacts=[str(old_lcurve), str(current_metrics), str(current_lcurve)],
        summary={"stage": "full_workflow", "simulation_decay_xlsx": str(current_decay)},
    )

    scoped = turn_scoped_result_for_display(result)

    assert str(old_lcurve) not in scoped.artifacts
    assert str(current_lcurve) in scoped.artifacts
    assert scoped.summary["metrics_xlsx"] == str(current_metrics)


def test_lcurve_source_decay_path_prefers_result_specific_decay(tmp_path):
    first_decay = tmp_path / "first_decay.xlsx"
    latest_decay = tmp_path / "latest_decay.xlsx"
    first_decay.write_bytes(b"first")
    latest_decay.write_bytes(b"latest")
    context = AgentRuntimeContext(workspace=tmp_path, repaired_path=latest_decay)
    result = AgentToolResult("success", "ok", summary={"simulation_decay_xlsx": str(first_decay)})

    assert lcurve_source_decay_path(context, result) == first_decay


def test_lcurve_picker_dialog_does_not_pass_unsupported_key(monkeypatch, tmp_path):
    metrics_path = tmp_path / "metrics.xlsx"
    pd.DataFrame(
        {
            "alpha_regularization": [0.001, 0.01, 0.1],
            "residual_norm": [3.0, 2.0, 1.0],
            "roughness_norm": [1.0, 2.0, 3.0],
            "slope_reciprocal": [0.2, 0.3, 0.4],
            "is_selected": [False, True, False],
        }
    ).to_excel(metrics_path, index=False)
    decay_path = tmp_path / "decay.xlsx"
    decay_path.write_bytes(b"placeholder")
    context = AgentRuntimeContext(workspace=tmp_path, repaired_path=decay_path)
    result = AgentToolResult("success", "ok", summary={"metrics_xlsx": str(metrics_path), "source_decay_xlsx": str(decay_path)})
    dialog_kwargs: list[dict] = []

    class FakeColumn:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeStreamlit:
        def __init__(self):
            self.session_state = {}
            self.captions: list[str] = []

        def caption(self, message, *_args, **_kwargs):
            self.captions.append(str(message))
            return None

        def button(self, _label, key=None, **_kwargs):
            return bool(key and key.endswith("-open-button"))

        def dialog(self, *_args, **kwargs):
            dialog_kwargs.append(dict(kwargs))

            def decorator(fn):
                return fn

            return decorator

        def selectbox(self, _label, options, **_kwargs):
            return list(options)[0]

        def columns(self, *_args, **_kwargs):
            return [FakeColumn(), FakeColumn()]

        def plotly_chart(self, *_args, **_kwargs):
            return None

        def number_input(self, _label, value=None, **_kwargs):
            return value

        def success(self, *_args, **_kwargs):
            return None

    fake_st = FakeStreamlit()
    monkeypatch.setattr(streamlit_app, "st", fake_st)

    streamlit_app.render_lcurve_parameter_picker(context, result, "turn-1-result-0", "中文")

    assert dialog_kwargs
    assert "key" not in dialog_kwargs[0]


def test_opening_lcurve_picker_closes_other_lcurve_dialog_states(monkeypatch, tmp_path):
    metrics_path = tmp_path / "metrics.xlsx"
    pd.DataFrame(
        {
            "alpha_regularization": [0.001, 0.01, 0.1],
            "residual_norm": [3.0, 2.0, 1.0],
            "roughness_norm": [1.0, 2.0, 3.0],
            "slope_reciprocal": [0.2, 0.3, 0.4],
            "is_selected": [False, True, False],
        }
    ).to_excel(metrics_path, index=False)
    decay_path = tmp_path / "decay.xlsx"
    decay_path.write_bytes(b"placeholder")
    context = AgentRuntimeContext(workspace=tmp_path, repaired_path=decay_path)
    result = AgentToolResult("success", "ok", summary={"metrics_xlsx": str(metrics_path), "source_decay_xlsx": str(decay_path)})
    keys = lcurve_picker_state_keys("turn-2-result-0", metrics_path, decay_path)

    class FakeColumn:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeStreamlit:
        def __init__(self):
            self.session_state = {
                "lcurve-alpha-picker-turn-1-result-0-old-open-state": True,
                keys["open_state"]: False,
            }

        def caption(self, *_args, **_kwargs):
            return None

        def button(self, _label, key=None, **_kwargs):
            return key == keys["open_button"]

        def dialog(self, *_args, **_kwargs):
            def decorator(fn):
                return fn

            return decorator

        def selectbox(self, _label, options, **_kwargs):
            return list(options)[0]

        def columns(self, *_args, **_kwargs):
            return [FakeColumn(), FakeColumn()]

        def plotly_chart(self, *_args, **_kwargs):
            return None

        def number_input(self, _label, value=None, **_kwargs):
            return value

        def success(self, *_args, **_kwargs):
            return None

    fake_st = FakeStreamlit()
    monkeypatch.setattr(streamlit_app, "st", fake_st)

    streamlit_app.render_lcurve_parameter_picker(context, result, "turn-2-result-0", "中文")

    assert fake_st.session_state[keys["open_state"]] is True
    assert fake_st.session_state["lcurve-alpha-picker-turn-1-result-0-old-open-state"] is False


def test_lcurve_picker_preview_output_dir_is_scoped_to_turn_and_result(monkeypatch, tmp_path):
    metrics_a = tmp_path / "metrics_a.xlsx"
    metrics_b = tmp_path / "metrics_b.xlsx"
    frame = pd.DataFrame(
        {
            "alpha_regularization": [0.001, 0.01, 0.1],
            "residual_norm": [3.0, 2.0, 1.0],
            "roughness_norm": [1.0, 2.0, 3.0],
            "slope_reciprocal": [0.2, 0.3, 0.4],
            "is_selected": [False, True, False],
        }
    )
    frame.to_excel(metrics_a, index=False)
    frame.to_excel(metrics_b, index=False)
    decay_a = tmp_path / "decay_a.xlsx"
    decay_b = tmp_path / "decay_b.xlsx"
    decay_a.write_bytes(b"a")
    decay_b.write_bytes(b"b")
    context = AgentRuntimeContext(workspace=tmp_path, repaired_path=decay_b)
    first_result = AgentToolResult("success", "first", summary={"metrics_xlsx": str(metrics_a), "source_decay_xlsx": str(decay_a)})
    second_result = AgentToolResult("success", "second", summary={"metrics_xlsx": str(metrics_b), "source_decay_xlsx": str(decay_b)})
    captured_output_dirs: list[Path] = []

    def fake_run_fixed_nnls(_input_workbook, output_dir, _params, language="中文"):
        captured_output_dirs.append(Path(output_dir))
        return AgentToolResult("success", "preview", summary={"spectrum_xlsx": str(tmp_path / "preview.xlsx")})

    class FakeColumn:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeStatus:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def update(self, **_kwargs):
            return None

    class FakeStreamlit:
        def __init__(self):
            self.session_state = {}
            self.captions: list[str] = []

        def caption(self, message, *_args, **_kwargs):
            self.captions.append(str(message))
            return None

        def button(self, _label, key=None, **_kwargs):
            return bool(key and (key.endswith("-open-button") or key.endswith("-preview-button")))

        def dialog(self, *_args, **_kwargs):
            def decorator(fn):
                return fn

            return decorator

        def selectbox(self, _label, options, **_kwargs):
            return list(options)[0]

        def columns(self, *_args, **_kwargs):
            return [FakeColumn(), FakeColumn()]

        def plotly_chart(self, *_args, **_kwargs):
            return None

        def number_input(self, _label, value=None, **_kwargs):
            return value

        def success(self, *_args, **_kwargs):
            return None

        def info(self, *_args, **_kwargs):
            return None

        def status(self, *_args, **_kwargs):
            return FakeStatus()

    fake_st = FakeStreamlit()
    monkeypatch.setattr(streamlit_app, "st", fake_st)
    monkeypatch.setattr(streamlit_app, "run_fixed_nnls", fake_run_fixed_nnls)

    streamlit_app.render_lcurve_parameter_picker(context, first_result, "turn-1-result-0", "中文", owner_message_index=1)
    streamlit_app.render_lcurve_parameter_picker(context, second_result, "turn-2-result-0", "中文", owner_message_index=3)

    assert len(captured_output_dirs) == 2
    assert captured_output_dirs[0] != captured_output_dirs[1]
    assert "turn-1-result-0" in captured_output_dirs[0].as_posix()
    assert "turn-2-result-0" in captured_output_dirs[1].as_posix()
    caption_text = "\n".join(fake_st.captions)
    assert "metrics_a.xlsx" in caption_text
    assert "metrics_b.xlsx" in caption_text
    assert "decay_a.xlsx" in caption_text
    assert "decay_b.xlsx" in caption_text


def test_lcurve_picker_render_does_not_mutate_widget_keys(monkeypatch, tmp_path):
    metrics_path = tmp_path / "metrics.xlsx"
    pd.DataFrame(
            {
                "alpha_regularization": [0.001, 0.01, 0.1],
                "residual_norm": [3.0, 2.0, 1.0],
                "roughness_norm": [1.0, 2.0, 3.0],
                "slope_reciprocal": [0.2, 0.3, 0.4],
                "is_selected": [False, True, False],
            }
    ).to_excel(metrics_path, index=False)
    repaired_path = tmp_path / "repaired.xlsx"
    repaired_path.write_bytes(b"placeholder")
    context = AgentRuntimeContext(workspace=tmp_path, repaired_path=repaired_path)
    result = AgentToolResult("success", "ok", summary={"metrics_xlsx": str(metrics_path)})

    class GuardedSessionState(dict):
        def __init__(self):
            super().__init__()
            self.widget_keys: set[str] = set()

        def __setitem__(self, key, value):
            if key in self.widget_keys:
                raise AssertionError(f"attempted to mutate widget key {key}")
            super().__setitem__(key, value)

    class FakeColumn:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeStreamlit:
        def __init__(self):
            self.session_state = GuardedSessionState()

        def caption(self, *_args, **_kwargs):
            return None

        def button(self, _label, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return bool(key and (key.endswith("-open-button") or key.endswith("-open")))

        def dialog(self, *_args, **_kwargs):
            def decorator(fn):
                return fn

            return decorator

        def selectbox(self, _label, options, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return list(options)[0]

        def number_input(self, _label, value=None, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return value

        def columns(self, *_args, **_kwargs):
            return [FakeColumn(), FakeColumn()]

        def plotly_chart(self, *_args, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return None

        def success(self, *_args, **_kwargs):
            return None

    fake_st = FakeStreamlit()
    monkeypatch.setattr(streamlit_app, "st", fake_st)

    streamlit_app.render_lcurve_parameter_picker(context, result, 0, "中文")

    keys = lcurve_picker_state_keys(0, metrics_path, repaired_path)
    assert fake_st.session_state[keys["open_state"]] is True
    assert fake_st.session_state[f"{keys['base']}-Sheet1-alpha"] == 0.01


def test_lcurve_picker_preview_does_not_append_formal_result(monkeypatch, tmp_path):
    metrics_path = tmp_path / "metrics.xlsx"
    pd.DataFrame(
        {
            "alpha_regularization": [0.001, 0.01, 0.1],
            "residual_norm": [3.0, 2.0, 1.0],
            "roughness_norm": [1.0, 2.0, 3.0],
            "slope_reciprocal": [0.2, 0.3, 0.4],
            "is_selected": [False, True, False],
        }
    ).to_excel(metrics_path, index=False)
    repaired_path = tmp_path / "repaired.xlsx"
    repaired_path.write_bytes(b"placeholder")
    context = AgentRuntimeContext(workspace=tmp_path, repaired_path=repaired_path)
    result = AgentToolResult("success", "ok", summary={"metrics_xlsx": str(metrics_path)})
    captured_params: list[dict] = []

    def fake_run_fixed_nnls(_input_workbook, _output_dir, params, language="中文"):
        captured_params.append(dict(params))
        spectrum_path = tmp_path / "preview_spectrum.xlsx"
        pd.DataFrame({"t2_ms": [1.0, 10.0, 100.0], "amplitude": [0.0, 5.0, 0.0]}).to_excel(spectrum_path, index=False)
        return AgentToolResult("success", "preview", artifacts=[str(spectrum_path)], summary={"spectrum_xlsx": str(spectrum_path)})

    class GuardedSessionState(dict):
        def __init__(self):
            super().__init__()
            self.widget_keys: set[str] = set()

        def __setitem__(self, key, value):
            if key in self.widget_keys:
                raise AssertionError(f"attempted to mutate widget key {key}")
            super().__setitem__(key, value)

    class FakeColumn:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeStatus:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def update(self, **_kwargs):
            return None

    class FakeStreamlit:
        def __init__(self):
            self.session_state = GuardedSessionState()

        def caption(self, *_args, **_kwargs):
            return None

        def markdown(self, *_args, **_kwargs):
            return None

        def button(self, _label, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return bool(key and (key.endswith("-open-button") or key.endswith("-preview-button")))

        def dialog(self, *_args, **_kwargs):
            def decorator(fn):
                return fn

            return decorator

        def selectbox(self, _label, options, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return list(options)[0]

        def number_input(self, _label, value=None, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return 0.25

        def columns(self, *_args, **_kwargs):
            return [FakeColumn(), FakeColumn()]

        def plotly_chart(self, *_args, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return None

        def success(self, *_args, **_kwargs):
            return None

        def info(self, *_args, **_kwargs):
            return None

        def status(self, *_args, **_kwargs):
            return FakeStatus()

    fake_st = FakeStreamlit()
    monkeypatch.setattr(streamlit_app, "st", fake_st)
    monkeypatch.setattr(streamlit_app, "run_fixed_nnls", fake_run_fixed_nnls)

    streamlit_app.render_lcurve_parameter_picker(context, result, 0, "中文")

    keys = lcurve_picker_state_keys(0, metrics_path, repaired_path)
    assert fake_st.session_state[keys["open_state"]] is True
    assert captured_params[0]["regularization"] == 0.25
    assert context.results == []
    assert context.tool_history == []
    assert f"{keys['base']}-Sheet1-preview-result" in fake_st.session_state


def test_enhance_report_with_conversation_exports_substantive_chat_analysis(tmp_path):
    report_path = tmp_path / "report.md"
    report_path.write_text("# T2 反演智能体报告\n\n## 工具运行结果\n- 原始工具摘要\n", encoding="utf-8")
    report = AgentToolResult("success", "ok", artifacts=[str(report_path)])
    messages = [
        ("assistant", "准备好后再上传 Excel，并告诉我你的目标。"),
        (
            "assistant",
            "## 五种分峰方案对比分析\n\n3 峰方案最推荐，因为它在拟合曲线、面积分布和解释稳定性之间取得较好平衡。2 峰偏粗，5 和 6 峰出现过度拆分风险。",
        ),
    ]

    assert enhance_report_with_conversation(report, messages, "中文") is True
    first_text = report_path.read_text(encoding="utf-8")
    assert "## 对话综合分析" in first_text
    assert "五种分峰方案对比分析" in first_text
    assert "3 峰方案最推荐" in first_text

    assert enhance_report_with_conversation(report, messages, "中文") is False
    second_text = report_path.read_text(encoding="utf-8")
    assert second_text.count("## 对话综合分析") == 1
    assert second_text == first_text


def test_exportable_assistant_analysis_filters_seed_messages():
    messages = [
        ("assistant", "准备好后再上传 Excel，并告诉我你的目标。"),
        ("user", "请分析"),
        ("assistant", "太短"),
        ("assistant", "这是一段足够长的分析内容，用于说明不同参数结果的优劣、风险和建议选择，应该进入最终报告导出。"),
    ]

    analyses = exportable_assistant_analysis(messages, "中文")

    assert analyses == ["这是一段足够长的分析内容，用于说明不同参数结果的优劣、风险和建议选择，应该进入最终报告导出。"]
