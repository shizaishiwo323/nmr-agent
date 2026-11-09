---
citation_key: Hurlimann1998EffectiveGradients
category: 05_relaxation_mechanism_mineralogy
tags: [cpmg, diffusion, echo_spacing, internal_gradient, long_t2_suppressed, susceptibility_contrast]
pages: 9
doi: 10.1006/jmre.1998.1364
---

# Hurlimann1998EffectiveGradients

- **Title**: Effective Gradients in Porous Media Due to Susceptibility Differences
- **Suggested citation format**: `[@Hurlimann1998EffectiveGradients]`
- **AGU reference**: Hürlimann, M. D. (1998). Effective gradients in porous media due to susceptibility differences. Journal of Magnetic Resonance, 131, 232–240. https://doi.org/10.1006/jmre.1998.1364
- **Reason for inclusion**: Uses the effective-gradient concept to analyse diffusive decay in internal gradients caused by susceptibility differences: only the decay of large pores increases markedly with echo spacing, and the effective gradient has an upper bound.
- **Role in the T2 agent**: Mechanism reference: internal gradients, echo-spacing dependence, and the large-pore/small-pore classification.

## Conclusions usable by the agent

### Echo-spacing dependence and internal gradients
- **When to invoke**: When the user compares data acquired with different echo spacings, when the long-T2 component weakens as the echo spacing increases, or when the sample has large susceptibility contrasts.
- **Physical/mathematical mechanism**: Pores are classed as large or small by comparing the pore size with a characteristic length; only the decay rate of large pores increases markedly with the echo spacing tE, and this can be approximated by an effective-gradient distribution; the effective gradient has an upper limit gmax that depends only on the diffusion coefficient, the Larmor frequency and the susceptibility difference. A low field and the shortest echo spacing reduce this effect.
- **Citable sentence for reports**: If the long-T2 component shortens as the echo spacing increases, the influence of internal-gradient diffusion should be considered first; this effect acts mainly on larger pores [@Hurlimann1998EffectiveGradients].
- **Evidence location**: See the evidence anchors below. Check against the original publication before citing.

## Search keywords

`cpmg`, `diffusion`, `echo_spacing`, `internal_gradient`, `long_t2_suppressed`, `susceptibility_contrast`

## Evidence anchors

- p.1: The abstract states that the effective gradient has a maximum value and recommends a low field and the shortest echo spacing.
- p.3: Echo-spacing dependence in the free-diffusion regime (large pores).
- p.8: The conclusions state that only the large-pore contribution increases significantly with tE.

## Limits of use

- The agent's forward model does not include internal gradients; this card is used only to interpret experimental data, not simulation results.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.
