---
citation_key: Hurlimann1998EffectiveGradients
pdf: "05_relaxation_mechanism_mineralogy\Hurlimann1998_EffectiveGradients.pdf"
category: 05_relaxation_mechanism_mineralogy
tags: [cpmg, diffusion, echo_spacing, internal_gradient, long_t2_suppressed, susceptibility_contrast]
pages: 9
text_cache: "_extracted_text\Hurlimann1998_0480e8b2975e34b2.txt"
doi: 10.1006/jmre.1998.1364
---

# Hurlimann1998EffectiveGradients

- **题名/文件**：Effective Gradients in Porous Media Due to Susceptibility Differences (`Hurlimann1998_EffectiveGradients.pdf`)
- **建议引用格式**：`[@Hurlimann1998EffectiveGradients]`
- **AGU 参考文献**：Hürlimann, M. D. (1998). Effective gradients in porous media due to susceptibility differences. Journal of Magnetic Resonance, 131, 232–240. https://doi.org/10.1006/jmre.1998.1364
- **原始来源**：`NMR Theory and Review\Hurlimann1998_EffectiveGradients.pdf`
- **入选理由**：用有效梯度概念分析磁化率差异造成的内部梯度扩散衰减：只有大孔的衰减明显随回波间隔增加，且有效梯度存在上限。
- **在 T2 Agent 中的定位**：机理引用：内部梯度、回波间隔依赖、大孔/小孔分类。

## Agent 可用结论

### 回波间隔依赖性与内部梯度
- **什么结果时调用**：当用户比较不同回波间隔的数据，长 T2 组分随回波间隔变长而减弱，或样品磁化率差异大时。
- **物理/数学机制**：以孔径与特征长度比较把孔分为大孔和小孔；只有大孔的衰减速率随回波间隔 tE 明显增加，可用有效梯度分布近似描述；有效梯度存在只依赖扩散系数、拉莫尔频率和磁化率差的上限 gmax。低场与最短回波间隔可减小该效应。
- **可写入报告的引用句式**：若长 T2 组分随回波间隔增大而缩短，应优先考虑内部梯度扩散的影响，这一效应主要作用于较大孔隙 [@Hurlimann1998EffectiveGradients]。
- **证据定位**：见下方证据锚点；正式引用前需复核原 PDF。

## 检索关键词

`cpmg`, `diffusion`, `echo_spacing`, `internal_gradient`, `long_t2_suppressed`, `susceptibility_contrast`

## 证据锚点（非原文长引）

- p.1 / cache line 39-44: 摘要提出有效梯度存在最大值，并建议低场与最短回波间隔。
- p.3 / cache line 236-258: 自由扩散区制（大孔）下的回波间隔依赖。
- p.8 / cache line 751: 结论中只有大孔贡献随 tE 显著增加。

## 使用边界

- 本 agent 的正演模型不含内部梯度；该卡只用于解释实验数据，不用于解释模拟结果。
- 当同一现象可由多个机制导致时，优先使用“可能/提示/支持”而不是绝对判断。
