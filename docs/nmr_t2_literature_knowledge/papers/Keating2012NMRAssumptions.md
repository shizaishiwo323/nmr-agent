---
citation_key: Keating2012NMRAssumptions
category: 01_core_theory_inversion
tags: [core_theory_inversion, dephasing, diffusive_coupling, echo_spacing, eigenmodes, exchange, field_inhomogeneity, geometry, internal_gradient, peak_merging, pore_coupling, pore_shape, pore_size, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 13
---

# Keating2012NMRAssumptions

- **Suggested citation format**: `[@Keating2012NMRAssumptions]`
- **Reason for inclusion**: Theoretical background on interpreting the NMR response in terms of hydrological/porous-media parameters.
- **Role in the T2 agent**: Background reference for basic theory and inversion; invoke only the specific mechanisms listed on this card and do not generalize to the whole topic.

## Conclusions usable by the agent

### Surface relaxation, pore size and short T2
- **When to invoke**: When the short-T2 area is large, when the main peak shifts to shorter T2, when small-pore/high-surface-area models decay faster, or when the relation between T2 and pore size needs to be explained.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@Keating2012NMRAssumptions]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Diffusive coupling and inter-pore exchange
- **When to invoke**: When several expected pore populations merge into one broad peak in the inversion, when peak positions fall between the geometric predictions, when a connected-pore model gives a smoother spectrum than an isolated-pore model, or when 1D T2 cannot separate pore populations.
- **Physical/mathematical mechanism**: Spins that diffuse between pores of different sizes average several local relaxation environments; when coupling is strong, the T2 distribution no longer equals the independent response of each pore-size population.
- **Citable sentence for reports**: Peak merging or spectral broadening does not necessarily mean that only one pore population is present; it may result from inter-pore diffusive coupling that mixes several relaxation environments. [@Keating2012NMRAssumptions]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to invoke**: When a change of geometry shifts or broadens the T2 peak, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal decay problem controlled by the boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information resulting from diffusion within the pore domain combined with boundary relaxation, not just the geometric pore size itself. [@Keating2012NMRAssumptions]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Internal gradients/field inhomogeneity
- **When to invoke**: When the simulated decay is faster than a pure surface-relaxation model, when the long-T2 end is suppressed, when changing the echo spacing alters the spectral shape, or when susceptibility contrast causes extra decay.
- **Physical/mathematical mechanism**: Internal magnetic-field gradients combined with diffusion cause additional dephasing; this term depends on the diffusion coefficient, gradient strength, echo spacing and pore size.
- **Citable sentence for reports**: A shortened T2 does not necessarily come only from small pores or a high surface relaxivity; it may also come from diffusion dephasing induced by internal gradients. [@Keating2012NMRAssumptions]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

## Search keywords

`core_theory_inversion`, `dephasing`, `diffusive_coupling`, `echo_spacing`, `eigenmodes`, `exchange`, `field_inhomogeneity`, `geometry`, `internal_gradient`, `peak_merging`, `pore_coupling`, `pore_shape`, `pore_size`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and search tags; consult the original publication for exact wording or page numbers.
- Main evidence topics: surface relaxation, pore size and short T2; diffusive coupling and inter-pore exchange; restricted diffusion, geometry and eigenmodes; internal gradients/field inhomogeneity.

## Limits of use

- Do not treat this reference as the sole basis for interpreting every sample; reports should take into account the user's data quality, T2 range, regularization, simulation geometry and parameter settings.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.