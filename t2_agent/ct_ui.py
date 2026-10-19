"""Streamlit widgets for the segmented-CT TIF workflow.

* background question (only when the image has >= 3 pixel values and the
  prompt did not say whether background pixels exist);
* phase preview dialog with draggable AI markers on the real CT label image;
* parameter confirmation dialog when the prompt did not provide everything.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Callable

import streamlit as st
import streamlit.components.v1 as components

from . import ct_phase as ct
from .ct_workflow import confirm_phase_assignment, confirm_run_parameters, is_ct_upload, set_background_answer

_COMPONENT_DIR = Path(__file__).resolve().parent / "components" / "phase_marker"
_phase_marker = components.declare_component("ct_phase_marker", path=str(_COMPONENT_DIR))



def _zh(language: str) -> bool:
    return not str(language).lower().startswith("english")


def _L(language: str, zh: str, en: str) -> str:
    return zh if _zh(language) else en


def _lang_key(language: str) -> str:
    return "中文" if _zh(language) else "English"


def _data_url(path: str | None) -> str | None:
    if not path or not Path(path).exists():
        return None
    return "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode("ascii")


def markers_for(state: dict[str, Any], assignment: dict[str, str]) -> dict[str, list[float]]:
    points = state.get("value_points", {})
    return {phase: list(points.get(value, [0.0, 0.0])) for value, phase in assignment.items()}


def apply_marker_event(state: dict[str, Any], event: Any) -> bool:
    """Apply a drag/keyboard/reset event from the browser component once."""

    if not isinstance(event, dict) or not event.get("event_id"):
        return False
    if event["event_id"] == state.get("last_event_id"):
        return False
    state["last_event_id"] = event["event_id"]
    if event.get("revision") != state.get("revision"):
        return False
    assignment = {str(key): str(value) for key, value in (event.get("assignment") or {}).items()}
    if sorted(assignment) != sorted(str(value) for value in state.get("values", [])):
        return False
    state["assignment"] = assignment
    markers = event.get("markers") or {}
    state["markers"] = {str(key): [float(value[0]), float(value[1])] for key, value in markers.items() if isinstance(value, (list, tuple)) and len(value) == 2}
    # New revision -> the dropdown fallback gets fresh widget keys instead of
    # keeping its stale selection and swapping the drag result back.
    state["revision"] = int(state.get("revision", 0)) + 1
    return True


def _component_args(state: dict[str, Any], language: str) -> dict[str, Any]:
    key = _lang_key(language)
    gray = state.get("display_gray_levels", {})
    entries = [
        {
            "value": int(value),
            "gray": int(gray.get(str(value), value)),
            "fraction": float(state.get("value_stats", {}).get(str(value), {}).get("fraction", 0.0)),
        }
        for value in state.get("values", [])
    ]
    used = set(state.get("assignment", {}).values())
    phases = {
        phase: {
            "color": list(ct.PHASE_COLORS[phase]),
            "name": ct.PHASE_NAMES[key][phase],
            "short": ct.PHASE_SHORT[key][phase],
        }
        for phase in ct.PHASES
        if phase in used or phase in state.get("ai_assignment", {}).values()
    }
    text = {
        "overlay": _L(language, "显示相态着色", "Phase colours"),
        "opacity": _L(language, "透明度", "Opacity"),
        "reset": _L(language, "恢复 AI 初判", "Reset to AI guess"),
        "hint": _L(
            language,
            "每个圆形标记代表 AI 对一个相的判断。若标记所在区域不是该相，把标记拖到正确的相区域上即可；被占用的相会自动交换。拖拽时左上会出现放大镜；也可用键盘方向键微调已聚焦的标记。",
            "Each round marker is the AI's guess for one phase. If a marker sits on the wrong material, drag it onto the correct region; phases swap automatically. A magnifier appears while dragging, and focused markers can be nudged with arrow keys.",
        ),
        "col_value": _L(language, "像素值", "Pixel value"),
        "col_fraction": _L(language, "面积占比", "Area"),
        "col_phase": _L(language, "当前判定", "Assigned phase"),
        "col_ai": _L(language, "与 AI 初判", "vs AI guess"),
        "changed_from": _L(language, "已修改，AI 原判：", "changed, AI said"),
        "same_as_ai": _L(language, "与 AI 一致", "same as AI"),
        "under_cursor": _L(language, "光标处像素值", "value under cursor"),
        "marker_aria": _L(language, "标记，当前像素值", "marker on value"),
    }
    return {
        "image": _data_url(state.get("display_png")),
        "entries": entries,
        "phases": phases,
        "assignment": state.get("assignment", {}),
        "ai_assignment": state.get("ai_assignment", {}),
        "markers": state.get("markers") or markers_for(state, state.get("assignment", {})),
        "ai_markers": markers_for(state, state.get("ai_assignment", {})),
        "revision": int(state.get("revision", 0)),
        "max_height": 520,
        "text": text,
    }


def _assignment_table_controls(state: dict[str, Any], language: str, key_prefix: str) -> None:
    """Accessible dropdown fallback for the drag markers."""

    key = _lang_key(language)
    options = sorted(set(state.get("assignment", {}).values()), key=ct.PHASES.index)
    columns = st.columns(len(state.get("values", [])) or 1)
    for column, value in zip(columns, state.get("values", [])):
        value_key = str(value)
        current = state["assignment"][value_key]
        with column:
            selected = st.selectbox(
                _L(language, f"像素值 {value_key}", f"Value {value_key}"),
                options,
                index=options.index(current),
                format_func=lambda phase: ct.PHASE_NAMES[key][phase],
                key=f"{key_prefix}-select-{value_key}-{state.get('revision', 0)}",
            )
        if selected != current:
            state["assignment"] = ct.reassign_phase(state["assignment"], value_key, selected)
            state["markers"] = markers_for(state, state["assignment"])
            state["revision"] = int(state.get("revision", 0)) + 1
            st.rerun(scope="fragment")


def _source_note(state: dict[str, Any], language: str) -> str:
    source = state.get("assignment_source")
    if source == "prompt":
        agree = state.get("prompt_agrees_with_ai")
        return _L(
            language,
            "标记已按你在提示词里给出的标签放置" + ("，且与 AI 独立初判一致。" if agree else "；注意它与 AI 独立初判不一致，请仔细核对。"),
            "Markers follow the labels from your prompt" + (", which agree with the independent AI guess." if agree else "; note they differ from the independent AI guess — please check."),
        )
    confidence = state.get("ai_confidence", "medium")
    conf_text = {"high": _L(language, "高", "high"), "medium": _L(language, "中", "medium"), "low": _L(language, "低", "low")}.get(confidence, confidence)
    return _L(language, f"标记为 AI 初判，置信度：{conf_text}。", f"Markers show the AI first guess (confidence: {conf_text}).")


def render_phase_dialog(context, language: str, on_confirmed: Callable[[], None]) -> None:
    state = context.ct_state

    def dismissed() -> None:
        context.ct_state["open_dialog"] = None

    @st.dialog(_L(language, "CT 相态确认预览", "CT Phase Confirmation"), width="large", on_dismiss=dismissed)
    def dialog() -> None:
        st.caption(
            _L(
                language,
                f"文件：{Path(state['image_path']).name} · 像素值 {state.get('values')} · "
                + ("含背景像素" if state.get("has_background") else "无背景像素"),
                f"File: {Path(state['image_path']).name} · values {state.get('values')} · "
                + ("with background" if state.get("has_background") else "no background"),
            )
        )
        st.info(_source_note(state, language))
        event = _phase_marker(**_component_args(state, language), key=f"ct-phase-marker-{Path(state['image_path']).name}", default=None)
        apply_marker_event(state, event)

        with st.expander(_L(language, "不方便拖拽？用下拉框指定", "Prefer dropdowns? Assign here"), expanded=False):
            _assignment_table_controls(state, language, "ct-phase")
        with st.expander(_L(language, "AI 初判依据", "Why the AI guessed this"), expanded=False):
            for phase, reason in (state.get("ai_reasons") or {}).items():
                st.markdown(f"- **{ct.phase_name(phase, language)}**: {reason}")

        problems = ct.validate_assignment(state.get("assignment", {}), state.get("values", []), bool(state.get("has_background")))
        for problem in problems:
            st.error(problem)
        summary = " · ".join(
            f"{value} → {ct.phase_name(phase, language)}"
            for value, phase in sorted(state.get("assignment", {}).items(), key=lambda item: int(item[0]))
        )
        st.markdown(_L(language, f"**当前判定：** {summary}", f"**Current assignment:** {summary}"))
        left, right = st.columns([0.62, 0.38])
        with left:
            if st.button(_L(language, "确认相态并继续", "Confirm phases and continue"), type="primary", disabled=bool(problems), width="stretch", key="ct-confirm-phases"):
                result = confirm_phase_assignment(context, dict(state["assignment"]), language)
                st.session_state["ct_last_phase_message"] = result.message
                on_confirmed()
                st.rerun()
        with right:
            if st.button(_L(language, "恢复 AI 初判", "Reset to AI guess"), width="stretch", key="ct-reset-phases"):
                state["assignment"] = dict(state.get("ai_assignment", {}))
                state["markers"] = markers_for(state, state["assignment"])
                state["revision"] = int(state.get("revision", 0)) + 1
                st.rerun(scope="fragment")

    dialog()


def _field_note(field: str, state: dict[str, Any], language: str) -> str:
    if field in state.get("explicit_fields", []):
        return _L(language, "来自你的提示词", "from your prompt")
    return _L(language, "提示词未提供，已填默认值，请确认", "not in prompt — default filled in, please confirm")


def render_params_dialog(context, language: str, on_confirmed: Callable[[], None]) -> None:
    state = context.ct_state
    prefill = dict(state.get("prefill", {}))
    defaults = ct.CtRunConfig()

    def dismissed() -> None:
        context.ct_state["open_dialog"] = None

    @st.dialog(_L(language, "确认模拟与反演参数", "Confirm Simulation & Inversion Parameters"), width="large", on_dismiss=dismissed)
    def dialog() -> None:
        missing = state.get("missing_fields", [])
        if missing:
            st.warning(
                _L(
                    language,
                    "你的提示词没有给全以下信息，已预填默认值：" + "、".join(_missing_label(field, language) for field in missing) + "。请核对后再运行。",
                    "Your prompt did not give: " + ", ".join(_missing_label(field, language) for field in missing) + ". Defaults are pre-filled; please check before running.",
                )
            )
        st.markdown(_L(language, "#### 1. CT 分辨率", "#### 1. CT resolution"))
        pixel = st.number_input(
            _L(language, "每个像素对应的尺寸（μm/pixel）", "Pixel size (μm/pixel)"),
            min_value=0.001,
            value=float(prefill.get("pixel_size_um", defaults.pixel_size_um)),
            step=0.1,
            format="%.3f",
            help=_L(language, "决定孔隙的物理尺寸，直接影响表面弛豫和 T2 位置。", "Sets the physical pore size; it directly shifts T2."),
            key="ct-param-pixel",
        )
        st.caption(_field_note("pixel_size_um", state, language))

        st.markdown(_L(language, "#### 2. 模拟核心参数", "#### 2. Simulation core parameters"))
        c1, c2 = st.columns(2)
        with c1:
            diffusion = st.number_input(_L(language, "扩散系数 D（μm²/ms）", "Diffusion D (μm²/ms)"), min_value=0.0001, value=float(prefill.get("diffusion_um2_per_ms", defaults.diffusion_um2_per_ms)), step=0.1, key="ct-param-d", help=_L(language, "30 °C 水约 2.3 μm²/ms。", "Water at 30 °C ≈ 2.3 μm²/ms."))
            rho_solid = st.number_input(_L(language, "固-液表面弛豫率 ρ（μm/ms）", "Solid-water relaxivity ρ (μm/ms)"), min_value=0.0, value=float(prefill.get("rho_solid_um_per_ms", defaults.rho_solid_um_per_ms)), step=0.001, format="%.4f", key="ct-param-rho", help=_L(language, "0.005 μm/ms = 5 μm/s；砂岩常见 1–50 μm/s。", "0.005 μm/ms = 5 μm/s; sandstones are typically 1–50 μm/s."))
        with c2:
            bulk = st.number_input(_L(language, "体弛豫 T2,bulk（ms）", "Bulk T2 (ms)"), min_value=1.0, value=float(prefill.get("bulk_t2_ms", defaults.bulk_t2_ms)), step=100.0, key="ct-param-bulk")
            rho_gas = st.number_input(_L(language, "气-液界面弛豫率（μm/ms）", "Air-water relaxivity (μm/ms)"), min_value=0.0, value=float(prefill.get("rho_gas_um_per_ms", defaults.rho_gas_um_per_ms)), step=0.001, format="%.4f", key="ct-param-rhogas", help=_L(language, "气-液界面通常不产生表面弛豫，默认 0。", "Gas-liquid interfaces usually do not relax; default 0."))
        st.caption(_field_note("simulation_core", state, language) if "simulation_core" in missing else _L(language, "部分参数来自你的提示词", "Some values come from your prompt"))

        s_over_v_px = state.get("surface_to_volume_per_px")
        estimate_ms = None
        if s_over_v_px:
            estimate_ms = 1.0 / (1.0 / bulk + rho_solid * float(s_over_v_px) / pixel)
        auto_time = st.checkbox(_L(language, "根据估计 T2 自动设置模拟时长与步长（推荐）", "Set simulated time and step from the estimated T2 (recommended)"), value=prefill.get("t_max_ms") is None, key="ct-param-autotime")
        t_max = dt = None
        if estimate_ms is not None:
            recommended = ct.recommend_time_axis(estimate_ms)
            st.caption(
                _L(
                    language,
                    f"快扩散估计 T2 ≈ {estimate_ms:.0f} ms → 建议模拟 {recommended['t_max_ms']:g} ms，步长 {recommended['dt_ms']:g} ms。",
                    f"Fast-diffusion estimate T2 ≈ {estimate_ms:.0f} ms → simulate {recommended['t_max_ms']:g} ms with dt {recommended['dt_ms']:g} ms.",
                )
            )
        if not auto_time:
            t1, t2 = st.columns(2)
            with t1:
                t_max = st.number_input(_L(language, "最大模拟时间（ms）", "Max time (ms)"), min_value=10.0, value=float(prefill.get("t_max_ms") or 6000.0), step=500.0, key="ct-param-tmax")
            with t2:
                dt = st.number_input(_L(language, "时间步长（ms）", "Time step (ms)"), min_value=0.01, value=float(prefill.get("dt_ms") or 10.0), step=1.0, key="ct-param-dt")

        st.markdown(_L(language, "#### 3. T2 反演", "#### 3. T2 inversion"))
        run_lcurve = st.checkbox(_L(language, "执行 L-curve 自动选择平滑因子（推荐）", "Run L-curve to choose the smoothing factor (recommended)"), value=bool(prefill.get("run_lcurve", True)), key="ct-param-lcurve")
        st.caption(_field_note("run_lcurve", state, language))
        regularization = st.number_input(
            _L(language, "反演平滑因子（固定值，关闭 L-curve 时使用）", "Smoothing factor (used when L-curve is off)"),
            min_value=0.0,
            value=float(prefill.get("regularization", defaults.regularization)),
            format="%.6g",
            disabled=run_lcurve,
            help=_L(language, "越大谱越平滑但可能合并真实峰；越小越尖锐但可能放大噪声。", "Larger = smoother spectrum that may merge peaks; smaller = sharper but noisier."),
            key="ct-param-reg",
        )

        st.markdown(_L(language, "#### 4. 高斯分峰", "#### 4. Gaussian decomposition"))
        g1, g2 = st.columns([0.6, 0.4])
        with g1:
            run_gaussian = st.checkbox(_L(language, "执行高斯分峰", "Run Gaussian peak decomposition"), value=bool(prefill.get("run_gaussian", True)), key="ct-param-gauss")
            st.caption(_field_note("run_gaussian", state, language))
        with g2:
            peak_count = st.number_input(_L(language, "峰数", "Peak count"), min_value=1, max_value=8, value=int(prefill.get("peak_count", defaults.peak_count)), step=1, disabled=not run_gaussian, key="ct-param-peaks")

        with st.expander(_L(language, "高级设置（网格与 T2 范围）", "Advanced (mesh and T2 range)"), expanded=False):
            a1, a2 = st.columns(2)
            with a1:
                boundary_px = st.number_input(_L(language, "边界网格尺寸（像素）", "Boundary mesh size (px)"), min_value=0.25, value=float(prefill.get("mesh_boundary_px", defaults.mesh_boundary_px)), step=0.25, key="ct-param-mb")
                num_bins = st.number_input(_L(language, "T2 bin 数", "T2 bins"), min_value=20, max_value=500, value=int(prefill.get("num_bins", defaults.num_bins)), step=10, key="ct-param-bins")
            with a2:
                bulk_px = st.number_input(_L(language, "内部网格尺寸（像素）", "Interior mesh size (px)"), min_value=1.0, value=float(prefill.get("mesh_bulk_px", defaults.mesh_bulk_px)), step=0.5, key="ct-param-mbulk")

        if st.button(_L(language, "确认参数并开始执行", "Confirm and run"), type="primary", width="stretch", key="ct-confirm-params"):
            params = {
                "pixel_size_um": float(pixel),
                "diffusion_um2_per_ms": float(diffusion),
                "bulk_t2_ms": float(bulk),
                "rho_solid_um_per_ms": float(rho_solid),
                "rho_gas_um_per_ms": float(rho_gas),
                "t_max_ms": None if auto_time else float(t_max),
                "dt_ms": None if auto_time else float(dt),
                "run_lcurve": bool(run_lcurve),
                "regularization": float(regularization),
                "run_gaussian": bool(run_gaussian),
                "peak_count": int(peak_count),
                "mesh_boundary_px": float(boundary_px),
                "mesh_bulk_px": float(bulk_px),
                "num_bins": int(num_bins),
            }
            confirm_run_parameters(context, params)
            on_confirmed()
            st.rerun()

    dialog()


def _missing_label(field: str, language: str) -> str:
    labels = {
        "pixel_size_um": _L(language, "CT 分辨率", "CT resolution"),
        "simulation_core": _L(language, "模拟核心参数", "simulation core parameters"),
        "run_lcurve": _L(language, "是否执行 L-curve", "whether to run L-curve"),
        "regularization": _L(language, "反演平滑因子", "smoothing factor"),
        "run_gaussian": _L(language, "是否执行高斯分峰", "whether to run Gaussian decomposition"),
    }
    return labels.get(field, field)


STEP_LABELS = {
    "background": ("等待回答：是否含背景像素", "Waiting: does the image contain background?"),
    "phases": ("等待确认相态标记", "Waiting: confirm phase markers"),
    "params": ("等待确认运行参数", "Waiting: confirm run parameters"),
    "ready": ("相态与参数已确认，准备执行", "Confirmed, ready to run"),
    "running": ("正在执行", "Running"),
    "done": ("流程已完成", "Workflow completed"),
    "failed": ("流程失败", "Workflow failed"),
}


def render_ct_panel(context, language: str, on_background_answer: Callable[[Any], None]) -> None:
    """CT workflow status card in the right-hand result panel."""

    if context is None or not is_ct_upload(context.uploaded_path):
        return
    state = context.ct_state or {}
    with st.container(border=True):
        st.markdown(_L(language, "**CT 分割图工作流**", "**Segmented CT workflow**"))
        if not state or state.get("image_path") != str(Path(context.uploaded_path)):
            st.caption(
                _L(
                    language,
                    "在左侧告诉我目标，例如“用这张分割好的 CT 图跑 NMR 模拟和 T2 反演”。我会先识别像素值，必要时问你是否含背景，再给出相态预览供你确认。",
                    "Tell me your goal on the left, e.g. “run NMR simulation and T2 inversion on this segmented CT slice”. I will count pixel values, ask about background if needed, then show a phase preview for you to confirm.",
                )
            )
            return
        step = state.get("step")
        zh, en = STEP_LABELS.get(step, (str(step), str(step)))
        st.caption(_L(language, f"像素值：{state.get('values')} · 状态：{zh}", f"Values: {state.get('values')} · Status: {en}"))
        if step == "background":
            suggestion = state.get("suggested_has_background")
            st.info(
                _L(
                    language,
                    f"检测到 {len(state.get('values', []))} 种像素值，多出的值可能是“气相”也可能是“背景（样品外部）”。图像中是否含背景像素？"
                    + (f"（AI 倾向：{'含背景' if suggestion else '不含背景'}）" if suggestion is not None else ""),
                    f"{len(state.get('values', []))} pixel values found; the extra value may be air or outside-sample background. Does the image contain background pixels?"
                    + (f" (AI leans: {'yes' if suggestion else 'no'})" if suggestion is not None else ""),
                )
            )
            b1, b2 = st.columns(2)
            with b1:
                if st.button(_L(language, "含背景像素", "Has background"), width="stretch", type="primary" if suggestion else "secondary", key="ct-bg-yes"):
                    on_background_answer(set_background_answer(context, True, language))
                    st.rerun()
            with b2:
                if st.button(_L(language, "不含背景像素", "No background"), width="stretch", type="primary" if suggestion is False else "secondary", key="ct-bg-no"):
                    on_background_answer(set_background_answer(context, False, language))
                    st.rerun()
            if state.get("display_png") and Path(state["display_png"]).exists():
                st.image(state["display_png"], caption=_L(language, "原始分割图（灰度）", "Segmented labels (gray)"), width="stretch")
            return
        if state.get("assignment"):
            st.markdown(
                " · ".join(
                    f"`{value}` → {ct.phase_name(phase, language)}"
                    for value, phase in sorted(state["assignment"].items(), key=lambda item: int(item[0]))
                )
            )
        cols = st.columns(2)
        with cols[0]:
            if st.button(_L(language, "打开相态确认预览", "Open phase preview"), width="stretch", key="ct-open-phases", disabled=step in {"running"}):
                state["open_dialog"] = "phases"
                st.rerun()
        with cols[1]:
            if st.button(_L(language, "打开参数确认", "Open parameters"), width="stretch", key="ct-open-params", disabled=not state.get("phase_confirmed") or step == "running"):
                state["open_dialog"] = "params"
                st.rerun()
        if state.get("phase_confirmed") and state.get("prefill"):
            config = ct.CtRunConfig.from_mapping(state.get("prefill"))
            st.caption(
                _L(
                    language,
                    f"分辨率 {config.pixel_size_um:g} μm/px · L-curve：{'是' if config.run_lcurve else f'否（平滑因子 {config.regularization:g}）'} · 高斯分峰：{'是，' + str(config.peak_count) + ' 峰' if config.run_gaussian else '否'}",
                    f"{config.pixel_size_um:g} μm/px · L-curve: {'yes' if config.run_lcurve else f'no (smoothing {config.regularization:g})'} · Gaussian: {str(config.peak_count) + ' peaks' if config.run_gaussian else 'no'}",
                )
            )


def open_pending_dialog(context, language: str, on_ready_to_run: Callable[[], None]) -> None:
    """Open whichever CT dialog the workflow state asks for (one per run)."""

    if context is None or not is_ct_upload(context.uploaded_path):
        return
    state = context.ct_state or {}
    if state.get("image_path") != str(Path(context.uploaded_path)):
        return
    target = state.get("open_dialog")

    def after_confirm() -> None:
        if context.ct_state.get("step") == "ready":
            on_ready_to_run()

    if target == "phases" and state.get("assignment"):
        render_phase_dialog(context, language, after_confirm)
    elif target == "params" and state.get("phase_confirmed"):
        render_params_dialog(context, language, after_confirm)
