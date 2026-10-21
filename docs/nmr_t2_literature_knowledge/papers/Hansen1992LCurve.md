---
citation_key: Hansen1992LCurve
pdf: "01_core_theory_inversion\Hansen1992_LCurve.pdf"
category: 01_core_theory_inversion
tags: [core_theory_inversion, ill_posed, lcurve, regularization, regularization_parameter, regularized_inversion, tikhonov]
pages: 20
text_cache: "_extracted_text\Hansen1992_6a8752140cf748b5.txt"
doi: 10.1137/1034115
---

# Hansen1992LCurve

- **题名/文件**：Analysis of Discrete Ill-Posed Problems by Means of the L-Curve (`Hansen1992_LCurve.pdf`)
- **建议引用格式**：`[@Hansen1992LCurve]`
- **AGU 参考文献**：Hansen, P. C. (1992). Analysis of discrete ill-posed problems by means of the L-curve. SIAM Review, 34(4), 561–580. https://doi.org/10.1137/1034115
- **原始来源**：`NMR Theory and Review\Hansen1992_LCurve.pdf`
- **入选理由**：L-curve 的原始方法文献：残差范数与解的（半）范数构成的 L 形曲线及其拐角与正则化参数选择的关系。
- **在 T2 Agent 中的定位**：反演方法引用：L-curve 概念、Tikhonov 正则化、正则化参数选择。

## Agent 可用结论

### L-curve 与正则化参数选择
- **什么结果时调用**：当报告需要说明 L-curve 图是什么、为什么选拐角附近的平滑因子，或 L-curve 平坦/无明显拐角时。
- **物理/数学机制**：离散病态问题中，把正则化解的（半）范数对残差范数作图得到 L 形曲线；拐角附近在“贴合数据”和“抑制解的振荡”之间取得平衡，多种参数选择方法都与定位这一拐角相关。
- **可写入报告的引用句式**：L-curve 把残差范数与谱粗糙度放在同一图中，拐角附近的平滑因子在拟合误差与谱线平滑之间取得折中 [@Hansen1992LCurve]。
- **证据定位**：见下方证据锚点；正式引用前需复核原 PDF。

## 检索关键词

`core_theory_inversion`, `ill_posed`, `lcurve`, `regularization`, `regularization_parameter`, `regularized_inversion`, `tikhonov`

## 证据锚点（非原文长引）

- p.1 / cache line 12-16: 摘要指出 Tikhonov 正则化对应的残差-解范数图起核心作用，多种参数选择方法与定位 L 形“corner”相关。
- p.2 / cache line 89-92: 论文结构说明，讨论 L 形外观及拐角附近的正则化解。
- p.6 / cache line 403: 拐角区域的定义。

## 使用边界

- 本 agent 的自动选择规则是“斜率倒数最接近 0.25（有效范围 0.1–10）”，不是 Hansen 文中的最大曲率拐角；引用本文只支撑 L-curve 概念，不支撑这条具体规则。
- 不要把本文写成 NMR 应用文献；它是通用数值方法来源。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。
