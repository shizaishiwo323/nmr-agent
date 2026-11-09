---
citation_key: Dunn2002PorousMediaNMR
category: 01_core_theory_inversion
tags: [core_theory_inversion, cpmg, dephasing, echo_spacing, echo_train, eigenmodes, field_inhomogeneity, geometry, internal_gradient, pore_shape, pore_size, pulse_sequence, restricted_diffusion, sampling, short_t2, surface_relaxation, surface_relaxivity]
pages: 57
---

# Dunn2002PorousMediaNMR

- **Suggested citation format**: `[@Dunn2002PorousMediaNMR]`
- **Reason for inclusion**: Background material from a chapter of the Dunn book on surface relaxation, multi-exponential decay and the mechanisms of NMR in porous media.
- **Role in the T2 agent**: Background reference for basic theory and inversion; invoke only the specific mechanisms listed on this card and do not generalize to the whole topic.

## Conclusions usable by the agent

### Surface relaxation, pore size and short T2
- **When to invoke**: When the short-T2 area is large, when the main peak shifts to shorter T2, when small-pore/high-surface-area models decay faster, or when the relation between T2 and pore size needs to be explained.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@Dunn2002PorousMediaNMR]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to invoke**: When a change of geometry shifts or broadens the T2 peak, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal decay problem controlled by the boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information resulting from diffusion within the pore domain combined with boundary relaxation, not just the geometric pore size itself. [@Dunn2002PorousMediaNMR]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Internal gradients/field inhomogeneity
- **When to invoke**: When the simulated decay is faster than a pure surface-relaxation model, when the long-T2 end is suppressed, when changing the echo spacing alters the spectral shape, or when susceptibility contrast causes extra decay.
- **Physical/mathematical mechanism**: Internal magnetic-field gradients combined with diffusion cause additional dephasing; this term depends on the diffusion coefficient, gradient strength, echo spacing and pore size.
- **Citable sentence for reports**: A shortened T2 does not necessarily come only from small pores or a high surface relaxivity; it may also come from diffusion dephasing induced by internal gradients. [@Dunn2002PorousMediaNMR]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### CPMG/echo-train sampling effects
- **When to invoke**: When it is necessary to explain the effect on the inversion of raw-decay sampling, echo spacing, missing early points, trim-from-peak, or the simulated echo train.
- **Physical/mathematical mechanism**: The CPMG echo train is the input to the inversion; the sampling interval, early-signal quality, pulse errors and noise affect the recoverable T2 range and the stability of the spectrum.
- **Citable sentence for reports**: The quality of a T2 inversion is limited first of all by the quality of the echo-train data and by the time-sampling window. [@Dunn2002PorousMediaNMR]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

## Search keywords

`core_theory_inversion`, `cpmg`, `dephasing`, `echo_spacing`, `echo_train`, `eigenmodes`, `field_inhomogeneity`, `geometry`, `internal_gradient`, `pore_shape`, `pore_size`, `pulse_sequence`, `restricted_diffusion`, `sampling`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and search tags; consult the original publication for exact wording or page numbers.
- Main evidence topics: surface relaxation, pore size and short T2; restricted diffusion, geometry and eigenmodes; internal gradients/field inhomogeneity; CPMG/echo-train sampling effects.

## Limits of use

- Do not treat this reference as the sole basis for interpreting every sample; reports should take into account the user's data quality, T2 range, regularization, simulation geometry and parameter settings.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.