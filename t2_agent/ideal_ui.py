"""Streamlit dialog and status card for the ideal-structure parameter confirmation."""

from __future__ import annotations

from typing import Any, Callable

import streamlit as st

from . import ideal_workflow as iw


def _L(language: str, zh: str, en: str) -> str:
    return en if language == "English" else zh


MISSING_LABELS = {
    "geometry": ("孔隙尺寸", "pore sizes"),
    "coupling": ("是否耦合", "coupling"),
    "saturation": ("含水饱和度", "water saturation"),
    "simulation_core": ("模拟物理参数", "physical parameters"),
    "run_lcurve": ("是否执行 L-curve", "whether to run the L-curve"),
    "run_gaussian": ("是否执行高斯分峰", "whether to run Gaussian decomposition"),
}

STEP_LABELS = {
    "params": ("等待确认参数", "Waiting: confirm parameters"),
    "ready": ("参数已确认，准备执行", "Confirmed, ready to run"),
    "running": ("正在执行", "Running"),
    "done": ("流程已完成", "Workflow completed"),
    "failed": ("流程失败", "Workflow failed"),
}


def _note(group: str, state: dict[str, Any], language: str) -> None:
    if group in state.get("missing_fields", []):
        st.caption(_L(language, "提示词未提供，已填默认值，请确认", "Not in your prompt — default filled in, please confirm"))
    else:
        st.caption(_L(language, "来自你的提示词", "From your prompt"))


def _water_label(saturation: float, language: str) -> str:
    kind = iw.water_configuration(saturation)
    if kind == "full":
        return _L(language, "全饱和", "fully water-filled")
    if kind == "bubble":
        return _L(language, "中心气泡，水沿孔壁连续分布", "central gas bubble, water along the walls")
    return _L(language, "水只留在三个角隅（接触角 0°）", "water only in the three corners (0° contact angle)")


def render_ideal_params_dialog(context, language: str, on_confirmed: Callable[[], None]) -> None:
    state = context.ideal_state
    prefill = iw.IdealRunConfig.from_mapping(state.get("prefill"))

    def dismissed() -> None:
        context.ideal_state["open_dialog"] = None

    @st.dialog(_L(language, "确认理想结构模拟参数", "Confirm Ideal-Structure Simulation Parameters"), width="large", on_dismiss=dismissed)
    def dialog() -> None:
        missing = state.get("missing_fields", [])
        if missing:
            st.warning(
                _L(
                    language,
                    "你的提示词没有给全以下信息，已预填默认值：" + "、".join(MISSING_LABELS[m][0] for m in missing if m in MISSING_LABELS) + "。请核对后再运行。",
                    "Your prompt did not give: " + ", ".join(MISSING_LABELS[m][1] for m in missing if m in MISSING_LABELS) + ". Defaults are pre-filled; please check before running.",
                )
            )
        left, right = st.columns([0.58, 0.42])
        with left:
            st.markdown(_L(language, "#### 1. 孔隙形状", "#### 1. Pore shape"))
            st.selectbox(
                _L(language, "形状（当前唯一支持）", "Shape (only supported option)"),
                [_L(language, "等边三角形双孔：大孔 + 倒置小孔", "Equilateral triangle pair: large pore + inverted small pore")],
                disabled=True,
                key="ideal-shape",
                help=_L(language, "圆形、狭缝、矩形等形状暂不支持。", "Circles, slits and rectangles are not supported yet."),
            )

            st.markdown(_L(language, "#### 2. 孔隙尺寸", "#### 2. Pore sizes"))
            c1, c2 = st.columns(2)
            with c1:
                large_side = st.number_input(_L(language, "大孔边长（μm）", "Large pore side (μm)"), min_value=1.0, max_value=500.0, value=float(prefill.large_side_um), step=1.0, key="ideal-large-side")
                large_depth = st.number_input(_L(language, "大孔厚度（μm，体积加权）", "Large pore depth (μm, volume weight)"), min_value=0.1, value=float(prefill.large_depth_um), step=1.0, key="ideal-large-depth")
            with c2:
                small_side = st.number_input(_L(language, "小孔边长（μm）", "Small pore side (μm)"), min_value=0.5, max_value=500.0, value=float(prefill.small_side_um), step=1.0, key="ideal-small-side")
                small_depth = st.number_input(_L(language, "小孔厚度（μm，体积加权）", "Small pore depth (μm, volume weight)"), min_value=0.1, value=float(prefill.small_depth_um), step=1.0, key="ideal-small-depth")
            _note("geometry", state, language)

            st.markdown(_L(language, "#### 3. 是否耦合", "#### 3. Coupling"))
            coupled = st.toggle(
                _L(language, "两孔经喉道连通（孔间扩散耦合）", "Join the pores with a throat (diffusive coupling)"),
                value=bool(prefill.coupled),
                key="ideal-coupled",
                help=_L(language, "耦合时水分子可在两孔间扩散交换，T2 峰可能向彼此靠拢或合并。", "When coupled, water molecules diffuse between the pores and the T2 peaks can move together or merge."),
            )
            t1, t2 = st.columns(2)
            with t1:
                throat_length = st.number_input(_L(language, "喉道长度（μm）", "Throat length (μm)"), min_value=0.1, value=float(prefill.throat_length_um), step=0.5, disabled=not coupled, key="ideal-throat-l")
            with t2:
                throat_width = st.number_input(_L(language, "喉道宽度（μm）", "Throat width (μm)"), min_value=0.05, value=float(prefill.throat_width_um), step=0.1, disabled=not coupled, key="ideal-throat-w")
            _note("coupling", state, language)

            st.markdown(_L(language, "#### 4. 含水饱和度", "#### 4. Water saturation"))
            s1, s2 = st.columns(2)
            with s1:
                large_sw = st.slider(_L(language, "大孔 Sw", "Large pore Sw"), min_value=0.05, max_value=1.0, value=float(prefill.large_water_saturation), step=0.01, key="ideal-large-sw")
                st.caption(_water_label(large_sw, language))
            with s2:
                small_sw = st.slider(_L(language, "小孔 Sw", "Small pore Sw"), min_value=0.05, max_value=1.0, value=float(prefill.small_water_saturation), step=0.01, key="ideal-small-sw")
                st.caption(_water_label(small_sw, language))
            _note("saturation", state, language)

            st.markdown(_L(language, "#### 5. 模拟物理参数", "#### 5. Physical parameters"))
            p1, p2 = st.columns(2)
            with p1:
                diffusion = st.number_input(_L(language, "扩散系数 D（μm²/ms）", "Diffusion D (μm²/ms)"), min_value=0.0001, value=float(prefill.diffusion_um2_per_ms), step=0.1, key="ideal-d", help=_L(language, "30 °C 水约 2.3 μm²/ms。", "Water at 30 °C ≈ 2.3 μm²/ms."))
                rho = st.number_input(_L(language, "固-液表面弛豫率 ρ（μm/ms）", "Solid-water relaxivity ρ (μm/ms)"), min_value=0.0, value=float(prefill.rho_solid_um_per_ms), step=0.001, format="%.4f", key="ideal-rho", help=_L(language, "0.005 μm/ms = 5 μm/s；石英砂约 0.3 μm/s，含铁矿物可达数十 μm/s。", "0.005 μm/ms = 5 μm/s; quartz sand ≈ 0.3 μm/s, iron-bearing minerals tens of μm/s."))
            with p2:
                bulk = st.number_input(_L(language, "体弛豫 T2,bulk（ms）", "Bulk T2 (ms)"), min_value=1.0, value=float(prefill.bulk_t2_ms), step=100.0, key="ideal-bulk")
                st.caption(_L(language, "气-液界面与喉道壁按无通量处理（不产生表面弛豫）。", "Gas-water interfaces and throat walls are no-flux (no surface relaxation)."))
            _note("simulation_core", state, language)

            draft = iw.IdealRunConfig.from_mapping(
                prefill.to_dict()
                | {
                    "large_side_um": large_side,
                    "small_side_um": small_side,
                    "large_depth_um": large_depth,
                    "small_depth_um": small_depth,
                    "coupled": coupled,
                    "throat_length_um": throat_length,
                    "throat_width_um": throat_width,
                    "large_water_saturation": large_sw,
                    "small_water_saturation": small_sw,
                    "diffusion_um2_per_ms": diffusion,
                    "bulk_t2_ms": bulk,
                    "rho_solid_um_per_ms": rho,
                    "t_max_ms": None,
                    "dt_ms": None,
                }
            )
            large_t2 = iw.estimate_pore_t2_ms(draft, "large")
            small_t2 = iw.estimate_pore_t2_ms(draft, "small")
            recommended = draft.time_axis()
            auto_time = st.checkbox(_L(language, "根据估计 T2 自动设置模拟时长与步长（推荐）", "Set simulated time and step from the estimated T2 (recommended)"), value=prefill.t_max_ms is None, key="ideal-autotime")
            st.caption(
                _L(
                    language,
                    f"快扩散估计：大孔 T2 ≈ {large_t2:.0f} ms，小孔 T2 ≈ {small_t2:.0f} ms → 建议模拟 {recommended['t_max_ms']:g} ms，步长 {recommended['dt_ms']:g} ms。",
                    f"Fast-diffusion estimate: large T2 ≈ {large_t2:.0f} ms, small T2 ≈ {small_t2:.0f} ms → simulate {recommended['t_max_ms']:g} ms with dt {recommended['dt_ms']:g} ms.",
                )
            )
            t_max = dt = None
            if not auto_time:
                m1, m2 = st.columns(2)
                with m1:
                    t_max = st.number_input(_L(language, "最大模拟时间（ms）", "Max time (ms)"), min_value=10.0, value=float(prefill.t_max_ms or recommended["t_max_ms"]), step=100.0, key="ideal-tmax")
                with m2:
                    dt = st.number_input(_L(language, "时间步长（ms）", "Time step (ms)"), min_value=0.01, value=float(prefill.dt_ms or recommended["dt_ms"]), step=1.0, key="ideal-dt")

            st.markdown(_L(language, "#### 6. T2 反演与分峰", "#### 6. T2 inversion and peaks"))
            run_lcurve = st.checkbox(_L(language, "执行 L-curve 自动选择平滑因子（推荐）", "Run the L-curve to choose the smoothing factor (recommended)"), value=bool(prefill.run_lcurve), key="ideal-lcurve")
            criterion_labels = {
                "ratio": _L(language, "斜率倒数准则（与实测数据相同）", "Slope-reciprocal ratio (same as measured data)"),
                "curvature": _L(language, "最大曲率准则（适合无噪声模拟衰减）", "Maximum curvature (suited to noise-free simulated decays)"),
            }
            criterion = st.radio(
                _L(language, "L-curve 选择准则", "L-curve selection rule"),
                list(criterion_labels),
                index=list(criterion_labels).index(prefill.lcurve_criterion if prefill.lcurve_criterion in criterion_labels else "ratio"),
                format_func=criterion_labels.get,
                disabled=not run_lcurve,
                horizontal=True,
                key="ideal-criterion",
            )
            regularization = st.number_input(_L(language, "固定平滑因子（关闭 L-curve 时使用）", "Fixed smoothing factor (used when the L-curve is off)"), min_value=0.0, value=float(prefill.regularization), format="%.6g", disabled=run_lcurve, key="ideal-reg")
            g1, g2 = st.columns([0.6, 0.4])
            with g1:
                run_gaussian = st.checkbox(_L(language, "执行高斯分峰", "Run Gaussian peak decomposition"), value=bool(prefill.run_gaussian), key="ideal-gauss")
            with g2:
                peak_count = st.number_input(_L(language, "峰数", "Peak count"), min_value=1, max_value=8, value=int(prefill.peak_count), step=1, disabled=not run_gaussian, key="ideal-peaks")
            with st.expander(_L(language, "高级设置（网格与 T2 bin）", "Advanced (mesh and T2 bins)"), expanded=False):
                mesh_area = st.number_input(_L(language, "目标三角形单元面积（μm²）", "Target triangle area (μm²)"), min_value=0.001, value=float(prefill.ideal_mesh_area_um2), step=0.01, format="%.3f", key="ideal-mesh-area", help=_L(language, "越小网格越细、计算越慢。", "Smaller is finer and slower."))
                num_bins = st.number_input(_L(language, "T2 bin 数", "T2 bins"), min_value=20, max_value=500, value=int(prefill.num_bins), step=10, key="ideal-bins")

        final = iw.IdealRunConfig.from_mapping(
            draft.to_dict()
            | {
                "t_max_ms": None if auto_time else float(t_max),
                "dt_ms": None if auto_time else float(dt),
                "run_lcurve": bool(run_lcurve),
                "lcurve_criterion": str(criterion),
                "regularization": float(regularization),
                "run_gaussian": bool(run_gaussian),
                "peak_count": int(peak_count),
                "ideal_mesh_area_um2": float(mesh_area),
                "num_bins": int(num_bins),
            }
        )
        with right:
            st.markdown(_L(language, "#### 几何预览", "#### Geometry preview"))
            fig = iw.draw_geometry_figure(final, language)
            st.pyplot(fig, width="stretch")
            import matplotlib.pyplot as plt

            plt.close(fig)
            st.caption(
                _L(
                    language,
                    f"{'耦合' if final.coupled else '不耦合'} · 大孔 {final.large_side_um:g} μm / Sw {final.large_water_saturation:.2f} · 小孔 {final.small_side_um:g} μm / Sw {final.small_water_saturation:.2f}",
                    f"{'Coupled' if final.coupled else 'Uncoupled'} · large {final.large_side_um:g} μm / Sw {final.large_water_saturation:.2f} · small {final.small_side_um:g} μm / Sw {final.small_water_saturation:.2f}",
                )
            )

        problems = iw.validate_config(final, language)
        for problem in problems:
            st.error(problem)
        if st.button(_L(language, "确认参数并开始执行", "Confirm and run"), type="primary", width="stretch", disabled=bool(problems), key="ideal-confirm"):
            iw.confirm_ideal_parameters(context, final.to_dict())
            on_confirmed()
            st.rerun()

    dialog()


def render_ideal_panel(context, language: str) -> None:
    """Status card for the ideal-structure workflow in the results panel."""

    state = (context.ideal_state if context is not None else {}) or {}
    if not state:
        return
    with st.container(border=True):
        st.markdown(_L(language, "**理想结构模拟工作流**", "**Ideal-structure workflow**"))
        zh, en = STEP_LABELS.get(str(state.get("step")), (str(state.get("step")), str(state.get("step"))))
        config = iw.IdealRunConfig.from_mapping(state.get("prefill"))
        st.caption(
            _L(
                language,
                f"状态：{zh} · {'耦合' if config.coupled else '不耦合'} · 大孔 {config.large_side_um:g} μm（Sw {config.large_water_saturation:.2f}） · 小孔 {config.small_side_um:g} μm（Sw {config.small_water_saturation:.2f}）",
                f"Status: {en} · {'coupled' if config.coupled else 'uncoupled'} · large {config.large_side_um:g} μm (Sw {config.large_water_saturation:.2f}) · small {config.small_side_um:g} μm (Sw {config.small_water_saturation:.2f})",
            )
        )
        if state.get("step") in {"params", "failed"}:
            if st.button(_L(language, "打开参数确认", "Open parameters"), width="stretch", key="ideal-open-params"):
                state["open_dialog"] = "ideal_params"
                st.rerun()


def open_pending_dialog(context, language: str, on_ready_to_run: Callable[[], None]) -> None:
    if context is None:
        return
    state = context.ideal_state or {}
    if state.get("open_dialog") != "ideal_params":
        return

    def after_confirm() -> None:
        if context.ideal_state.get("step") == "ready":
            on_ready_to_run()

    render_ideal_params_dialog(context, language, after_confirm)
