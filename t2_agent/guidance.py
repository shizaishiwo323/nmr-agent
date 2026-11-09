"""Rule-based parameter guidance used with or without DeepSeek."""

from __future__ import annotations

import re

from .models import UserWorkflowPlan


CN_NUMBER_MAP = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
}


def _extract_peak_count(text: str) -> int | None:
    match = re.search(r"(?:分|拆|拟合)?\s*(\d+)\s*(?:个)?\s*峰", text)
    if match:
        return max(1, int(match.group(1)))

    for token, value in CN_NUMBER_MAP.items():
        if re.search(fr"(?:分|拆|拟合)?\s*{token}\s*(?:个)?\s*峰", text):
            return value
    return None


def _extract_regularization(text: str) -> float | None:
    patterns = (
        r"(?:平滑因子|正则化因子|regularization|alpha|eps)\s*(?:=|为|是|设为|固定为|固定)?\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
        r"固定\s*(?:平滑因子|正则化因子)?\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def infer_requested_plan(user_text: str) -> UserWorkflowPlan:
    """Infer a conservative processing plan from natural-language intent."""

    text = (user_text or "").strip()
    lowered = text.lower()
    peak_intent = any(token in lowered for token in ("gaussian", "peak", "分峰", "峰"))
    inversion_intent = any(token in text for token in ("反演", "inversion", "l曲线", "L曲线", "l-curve", "L-curve", "平滑因子", "正则化"))
    only_peak_intent = peak_intent and any(
        token in lowered
        for token in ("只做", "仅做", "单独", "只要", "只需", "不用反演", "不要反演", "不做反演", "skip inversion", "without inversion", "only")
    )

    plan = UserWorkflowPlan()
    plan.user_is_unsure = any(token in text for token in ("不懂", "不知道", "默认", "推荐", "你来", "自动"))

    regularization = _extract_regularization(text)
    if regularization is not None:
        plan.workflow = "fixed_nnls"
        plan.regularization = regularization
        plan.user_is_unsure = False

    peak_count = _extract_peak_count(text)
    if peak_count is not None:
        plan.needs_gaussian = True
        plan.peak_count = peak_count
        if plan.workflow == "lcurve_inversion" and (only_peak_intent or any(token in text for token in ("已有", "谱", "spectrum"))):
            plan.workflow = "gaussian_only"
    elif peak_intent:
        plan.needs_gaussian = True
        plan.peak_count = 2
        if only_peak_intent or (not inversion_intent and any(token in text for token in ("已有", "谱", "spectrum"))):
            plan.workflow = "gaussian_only"

    if any(token in text for token in ("全流程", "都做", "反演并分峰", "反演和分峰")):
        plan.workflow = "full_analysis"
        plan.needs_gaussian = True

    if any(token in text for token in ("l曲线", "L曲线", "l-curve", "L-curve", "自动平滑")):
        plan.workflow = "lcurve_inversion"

    simulation_intent = any(
        token in lowered
        for token in (
            "模拟",
            "正演",
            "网格",
            "几何",
            "pygimli",
            "png",
            "phase map",
            "phase-map",
            "nmr simulation",
        )
    )
    png_intent = any(token in lowered for token in ("png", "图片", "图像", "相图", "phase map", "phase-map"))
    rule_intent = any(token in lowered for token in ("规则", "几何", "耦合", "喉道", "尺寸", "rule", "geometry"))
    if simulation_intent:
        plan.workflow = "simulation_2d_full"
        if png_intent:
            plan.workflow = "simulation_2d_png"
        elif rule_intent:
            plan.workflow = "simulation_2d_rule"
        if any(token in text for token in ("默认", "测试", "你来", "自动", "完整")):
            plan.user_is_unsure = True

    return plan


def build_parameter_guidance(plan: UserWorkflowPlan, language: str = "中文") -> str:
    """Return user-facing guidance for the inferred plan."""

    if language.lower().startswith("english"):
        if plan.workflow.startswith("simulation_2d"):
            return "\n".join(
                [
                    "For a 2D NMR simulation workflow, I will first check the geometry input, then generate a pyGIMLi triangular mesh, solve the time-domain NMR/T2 decay, and send that simulated decay into the existing T2 inversion pipeline.",
                    "",
                    "- PNG input must be a two-phase red/yellow map with optional white outside background: red means liquid/water pore space, yellow means solid, and white borders can be cropped automatically.",
                    "- Rule geometry can be used for a quick controlled test with coupled or uncoupled pore bodies and user-set sizes.",
                    "- For a first test run, defaults are acceptable, but diffusion, bulk T2, surface relaxivity, geometry scale, and mesh spacing should be confirmed before scientific interpretation.",
                    "- If you only need T2 inversion, I will skip simulation and use the existing workbook inversion tools.",
                ]
            )
        lines = [
            "I will explain the key parameters first, then give a conservative recommendation:",
            "",
            "- Smoothing/regularization factor: controls how smooth the T2 spectrum is. Smaller values fit the raw data more closely but can turn noise into false peaks; larger values make the spectrum smoother but may hide real small peaks.",
            "- L-curve: automatically finds a compromise between fitting error and spectrum smoothness. It is a good default when you do not yet know which smoothing factor to choose.",
            "- T2 range: defines which relaxation times are searched during inversion. Too narrow a range can miss peaks; too wide a range can make the result less stable. The default range is suitable for exploratory analysis.",
            "- Number of peaks: approximates the T2 spectrum with Gaussian peaks to help interpret pore or fluid components. More peaks are not always better; too many peaks can overfit.",
            "",
        ]

        if plan.workflow == "fixed_nnls":
            lines.append(
                f"You specified a fixed smoothing factor of {plan.regularization:g}. I will use fixed-regularization NNLS and note in the report that this depends more on manual judgment than L-curve."
            )
        elif plan.workflow == "gaussian_only":
            lines.append("Your request looks like peak decomposition for an existing T2 spectrum, so I will skip decay inversion and go directly to Gaussian peak decomposition.")
        else:
            lines.append("Default recommendation: use L-curve to choose the smoothing factor automatically. This is safer for first-pass analysis and reduces subjective tuning.")

        if plan.needs_gaussian:
            lines.append(f"Peak decomposition recommendation: use {plan.peak_count} peaks as requested. After running, I will report each peak position, area fraction, and fitting figure.")
        else:
            lines.append("Peak decomposition is not enabled by default. After the T2 spectrum is generated, start with 2 to 3 peaks if you want to interpret pore or fluid components.")

        return "\n".join(lines)

    if plan.workflow.startswith("simulation_2d"):
        return "\n".join(
            [
                "二维模拟会先检查几何/PNG，再用 pyGIMLi 三角网格生成网格，随后求解 NMR/T2 时域衰减曲线，并把得到的时域曲线送入现有 T2 反演流程。",
                "",
                "- PNG 输入必须是红/黄两相图，可带白色外部背景：红色表示液体/水相孔隙，黄色表示固体，白边会自动裁剪。",
                "- 规则几何可用于快速测试，可设置孔体是否耦合以及主要尺寸。",
                "- 测试运行可以先用默认物理参数，但正式解释前需要确认扩散系数、体相 T2、表面弛豫率、几何尺度和网格尺寸。",
                "- 如果你只需要 T2 反演，我会跳过模拟，继续使用已有的 Excel 反演工具。",
            ]
        )

    lines = [
        "我会先解释关键参数，再给出推荐方案：",
        "",
        "- 平滑因子/正则化因子：控制 T2 谱的平滑程度。值越小，结果越贴近原始数据，但更容易把噪声变成假峰；值越大，谱线越平滑，但可能把真实的小峰抹掉。",
        "- L-curve：自动在“拟合误差”和“谱线平滑”之间找折中点，适合还不知道该选多大平滑因子的用户。",
        "- T2 范围：决定反演搜索哪些弛豫时间。范围太窄可能漏峰，范围太宽会增加不稳定性。默认范围适合先做探索性分析。",
        "- 分峰数量：把 T2 谱拆成几个 Gaussian 峰，用来近似解释不同孔隙或流体组分。峰数不是越多越好，太多容易过拟合。",
        "",
    ]

    if plan.workflow == "fixed_nnls":
        lines.append(f"你已经指定固定平滑因子 {plan.regularization:g}，我会使用固定 NNLS 反演，并在报告里提示它可能比 L-curve 更依赖人工经验。")
    elif plan.workflow == "gaussian_only":
        lines.append("你更像是要对已有 T2 谱做分峰解释。我会跳过 decay 反演，直接进入 Gaussian 分峰。")
    else:
        lines.append("默认推荐：使用 L-curve 自动选择平滑因子。这样对新手更稳妥，也能减少人工调参带来的主观性。")

    if plan.needs_gaussian:
        lines.append(f"分峰推荐：按你的需求使用 {plan.peak_count} 个峰。运行后我会报告每个峰的位置、面积比例和拟合图。")
    else:
        lines.append("分峰默认不自动开启。先得到 T2 谱后，如果你要解释孔隙/流体组分，再选择 2 到 3 个峰开始比较合适。")

    return "\n".join(lines)
