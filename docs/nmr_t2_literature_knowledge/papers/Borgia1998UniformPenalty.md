---
citation_key: Borgia1998UniformPenalty
pdf: "01_core_theory_inversion\Borgia1998_UniformPenaltyInversion.pdf"
category: 01_core_theory_inversion
tags: [core_theory_inversion, false_peaks, multimodal, peak_broadening, peak_splitting, regularization, regularized_inversion, smoothing]
pages: 13
text_cache: "_extracted_text\Borgia1998_ca489669566ddcff.txt"
doi: 10.1006/jmre.1998.1387
---

# Borgia1998UniformPenalty

- **题名/文件**：Uniform-Penalty Inversion of Multiexponential Decay Data (`Borgia1998_UniformPenaltyInversion.pdf`)
- **建议引用格式**：`[@Borgia1998UniformPenalty]`
- **AGU 参考文献**：Borgia, G. C., Brown, R. J. S., & Fantazzini, P. (1998). Uniform-penalty inversion of multiexponential decay data. Journal of Magnetic Resonance, 132, 65–77. https://doi.org/10.1006/jmre.1998.1387
- **原始来源**：`NMR Theory and Review\Borgia1998_UniformPenaltyInversion.pdf`
- **入选理由**：说明固定平滑系数会展宽尖峰或把宽峰/拖尾拆成假多峰，并提出局部可变平滑（UPEN）。
- **在 T2 Agent 中的定位**：反演伪影引用：固定平滑导致的峰展宽、宽峰拆分、拖尾假峰。

## Agent 可用结论

### 固定平滑因子造成的峰形伪影
- **什么结果时调用**：当谱同时有尖峰和宽峰/拖尾，改变平滑因子后出现峰被展宽、宽峰被拆成几个小峰，或拖尾上出现“卫星峰”时。
- **物理/数学机制**：同一分布中存在尖峰和宽峰时，使用单一固定平滑系数的反演可能把尖峰展宽，或把宽峰/拖尾拆成多个分离峰；作者通过让各处罚项贡献大致均匀来缓解。
- **可写入报告的引用句式**：当谱同时含尖峰与宽拖尾时，固定平滑因子可能把尖峰展宽或把拖尾拆成数个小峰，这些小峰不宜直接解释为独立孔群 [@Borgia1998UniformPenalty]。
- **证据定位**：见下方证据锚点；正式引用前需复核原 PDF。

## 检索关键词

`core_theory_inversion`, `false_peaks`, `multimodal`, `peak_broadening`, `peak_splitting`, `regularization`, `regularized_inversion`, `smoothing`

## 证据锚点（非原文长引）

- p.1 / cache line 25-27: 摘要指出固定平滑系数可能展宽尖峰并把宽峰或拖尾拆成数个分离峰。
- p.2 / cache line 162-169: 说明通过调整平滑系数使罚项大致均匀。
- p.5 / cache line 483-488: 均匀罚项（uniform penalty）的反馈实现。

## 使用边界

- 本 agent 使用全局单一平滑因子，并未实现 UPEN；引用本文用于提示伪影风险，不能写成本工具采用了该方法。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。
