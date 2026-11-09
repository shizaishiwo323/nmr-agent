---
citation_key: Borgia1998UniformPenalty
category: 01_core_theory_inversion
tags: [core_theory_inversion, false_peaks, multimodal, peak_broadening, peak_splitting, regularization, regularized_inversion, smoothing]
pages: 13
doi: 10.1006/jmre.1998.1387
---

# Borgia1998UniformPenalty

- **Title**: Uniform-Penalty Inversion of Multiexponential Decay Data
- **Suggested citation format**: `[@Borgia1998UniformPenalty]`
- **AGU reference**: Borgia, G. C., Brown, R. J. S., & Fantazzini, P. (1998). Uniform-penalty inversion of multiexponential decay data. Journal of Magnetic Resonance, 132, 65–77. https://doi.org/10.1006/jmre.1998.1387
- **Reason for inclusion**: Shows that a fixed smoothing coefficient can broaden sharp peaks or split a broad peak/tail into spurious multiple peaks, and proposes locally variable smoothing (UPEN).
- **Role in the T2 agent**: Inversion-artifact reference: peak broadening, splitting of broad peaks and spurious tail peaks caused by fixed smoothing.

## Conclusions usable by the agent

### Peak-shape artifacts from a fixed smoothing factor
- **When to invoke**: When a spectrum contains both sharp peaks and broad peaks/tails, and changing the smoothing factor broadens peaks, splits a broad peak into several small peaks, or produces "satellite peaks" on a tail.
- **Physical/mathematical mechanism**: When a distribution contains both sharp and broad features, an inversion with a single fixed smoothing coefficient may broaden the sharp peak or split the broad peak/tail into several separate peaks; the authors mitigate this by making the penalty contributions roughly uniform across the distribution.
- **Citable sentence for reports**: When a spectrum contains both sharp peaks and a broad tail, a fixed smoothing factor may broaden the sharp peak or split the tail into several small peaks, and these small peaks should not be interpreted directly as independent pore populations [@Borgia1998UniformPenalty].
- **Evidence location**: See the evidence anchors below. Check against the original publication before citing.

## Search keywords

`core_theory_inversion`, `false_peaks`, `multimodal`, `peak_broadening`, `peak_splitting`, `regularization`, `regularized_inversion`, `smoothing`

## Evidence anchors

- p.1: The abstract states that a fixed smoothing coefficient may broaden sharp peaks and split broad peaks or tails into several separate peaks.
- p.2: Describes adjusting the smoothing coefficient so that the penalty is roughly uniform.
- p.5: Feedback implementation of the uniform penalty.

## Limits of use

- This agent uses a single global smoothing factor and does not implement UPEN; cite this paper only to flag the risk of artifacts, and do not state that the tool adopts this method.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.
