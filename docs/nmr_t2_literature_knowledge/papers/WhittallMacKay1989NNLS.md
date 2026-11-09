---
citation_key: WhittallMacKay1989NNLS
category: 01_core_theory_inversion
tags: [component_assignment, core_theory_inversion, ill_posed, inverse_laplace, nnls, nonuniqueness, peak_count, regularized_inversion]
pages: 19
doi: 10.1016/0022-2364(89)90011-5
---

# WhittallMacKay1989NNLS

- **Title**: Quantitative interpretation of NMR relaxation data
- **Suggested citation format**: `[@WhittallMacKay1989NNLS]`
- **AGU reference**: Whittall, K. P., & MacKay, A. L. (1989). Quantitative interpretation of NMR relaxation data. Journal of Magnetic Resonance, 84, 134–152. https://doi.org/10.1016/0022-2364(89)90011-5
- **Rationale for inclusion**: Classic method paper that interprets relaxation data as a relaxation-time spectrum using least squares/linear programming, and states explicitly that the solution is non-unique.
- **Role in the T2 agent**: Citation for inversion methods: NNLS-type relaxation-spectrum inversion, non-uniqueness and minimum-structure solutions.

## Conclusions usable by the agent

### Non-uniqueness of the inverted spectrum
- **When to use**: When the user asks whether the spectrum is a unique solution, whether the number of peaks is trustworthy, or when the same data give discrete peaks or a continuous spectrum under different settings.
- **Physical/mathematical mechanism**: A finite set of noisy measurements can be fitted equally well by many discrete or continuous spectra; a full interpretation needs to examine the range of acceptable solutions instead of relying on the single spectrum returned by one algorithm.
- **Citable sentence for reports**: The same decay data can be fitted equally well by discrete peaks or a continuous distribution, so the number and shape of peaks in a T2 spectrum should be read together with the regularization settings rather than treated as a unique solution [@WhittallMacKay1989NNLS].
- **Evidence location**: See the evidence anchors below. Check against the original publication before citing.

### Minimum-structure solution
- **When to use**: When the agent must explain why smoothness/non-negativity constraints are added to the inversion and why the spectrum with the least structure is preferred.
- **Physical/mathematical mechanism**: The paper constructs a minimum-structure model that avoids spurious features the data do not require, which raises confidence in the structure that is retained.
- **Citable sentence for reports**: Non-negativity and smoothness constraints are added so that only the spectral structure actually required by the data is kept, avoiding noise-induced spurious peaks [@WhittallMacKay1989NNLS].
- **Evidence location**: See the evidence anchors below. Check against the original publication before citing.

## Retrieval keywords

`component_assignment`, `core_theory_inversion`, `ill_posed`, `inverse_laplace`, `nnls`, `nonuniqueness`, `peak_count`, `regularized_inversion`

## Evidence anchors

- p.1: The abstract explains that finite and imprecise measurements lead to non-uniqueness, so many discrete and continuous spectra fit the data equally well.
- p.7 and p.8: A figure legend and the discussion illustrate the non-uniqueness.
- Conclusions section: the minimum-structure model prevents the generation of spurious features that the data do not require.

## Usage limits

- The paper's data come from biological tissue and generic relaxation data, not from rock or soil samples; use it only for arguments at the level of inversion methodology.
- This is a different paper from Whittall1991NNLS (analysis of non-ideal CPMG data); cite each according to its purpose.
- When the same phenomenon can arise from several mechanisms, prefer hedged wording ("may", "suggests", "supports") over absolute statements.
