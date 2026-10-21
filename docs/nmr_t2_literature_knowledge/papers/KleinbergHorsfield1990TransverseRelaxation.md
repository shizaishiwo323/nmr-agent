---
citation_key: KleinbergHorsfield1990TransverseRelaxation
pdf: "05_relaxation_mechanism_mineralogy\KleinbergHorsfield1990_TransverseRelaxation.pdf"
category: 05_relaxation_mechanism_mineralogy
tags: [cpmg, echo_spacing, internal_gradient, relaxation_mechanism, restricted_diffusion, surface_relaxation, susceptibility_contrast]
pages: 11
text_cache: "_extracted_text\KleinbergHorsfield1990_a8c2a76a411e7449.txt"
doi: 10.1016/0022-2364(90)90104-H
---

# KleinbergHorsfield1990TransverseRelaxation

- **题名/文件**：Transverse relaxation processes in porous sedimentary rock (`KleinbergHorsfield1990_TransverseRelaxation.pdf`)
- **建议引用格式**：`[@KleinbergHorsfield1990TransverseRelaxation]`
- **AGU 参考文献**：Kleinberg, R. L., & Horsfield, M. A. (1990). Transverse relaxation processes in porous sedimentary rock. Journal of Magnetic Resonance, 88, 9–19. https://doi.org/10.1016/0022-2364(90)90104-H
- **原始来源**：`NMR Theory and Review\KleinbergHorsfield1990_TransverseRelaxation.pdf`
- **入选理由**：实测 T2 随静磁场强度与 CPMG 脉冲间隔变化：低场短间隔时以表面弛豫为主，高场长间隔时出现梯度中扩散。
- **在 T2 Agent 中的定位**：机理引用：表面弛豫与内部梯度扩散的区分、回波间隔依赖性。

## Agent 可用结论

### T2 何时由表面弛豫主导
- **什么结果时调用**：当需要论证低场、短回波间隔条件下 T2 可近似视为表面弛豫控制，或解释为什么结果依赖仪器场强与回波间隔时。
- **物理/数学机制**：在最低场强和最短脉冲间隔下，T2 主要受流固界面弛豫控制；场强升高、间隔变长时出现明显的磁场梯度中扩散贡献，该梯度来自颗粒与孔隙流体的磁化率差异。总弛豫率并不是各过程弛豫率的简单相加。
- **可写入报告的引用句式**：低场、短回波间隔条件下 T2 主要反映表面弛豫；若场强较高或回波间隔较长，需考虑磁化率差异引起的梯度扩散贡献 [@KleinbergHorsfield1990TransverseRelaxation]。
- **证据定位**：见下方证据锚点；正式引用前需复核原 PDF。

## 检索关键词

`cpmg`, `echo_spacing`, `internal_gradient`, `relaxation_mechanism`, `restricted_diffusion`, `surface_relaxation`, `susceptibility_contrast`

## 证据锚点（非原文长引）

- p.1 / cache line 15-20: 摘要给出场强与脉冲间隔的对比结论，以及梯度来源于磁化率差异。
- p.1 / cache line 20-30: 小孔样品受限扩散最明显；理论中总弛豫率并非各过程简单相加。

## 使用边界

- 样品为含水沉积岩；用于实验数据解释时需注意用户的仪器场强与回波间隔是否与论文条件可比。
- 本 agent 的二维正演不含内部梯度项，模拟结果不能用本文来解释梯度效应。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。
