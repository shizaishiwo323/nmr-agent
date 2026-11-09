---
citation_key: Grunewald2009PoreCoupling
category: 04_pore_coupling_t2t2_interpretation
tags: [component_assignment, diffusive_coupling, exchange, gaussian_decomposition, overfitting, peak_count, peak_merging, pore_coupling, pore_coupling_t2t2_interpretation, pore_size, short_t2, surface_relaxation, surface_relaxivity]
pages: 7
---

# Grunewald2009PoreCoupling

- **Title**: A laboratory study of NMR relaxation times and pore coupling in heterogeneous media
- **Suggested citation format**: `[@Grunewald2009PoreCoupling]`
- **Reason for inclusion**: Combines experiments and interpretation, with the emphasis on pore coupling; useful for interpreting simulated spectral shapes.
- **Role in the T2 agent**: Pore-coupling/multidimensional NMR interpretation reference; suited to explaining peak merging, exchange and the non-uniqueness of 1D T2 interpretation.

## Conclusions usable by the agent

### Diffusive coupling and inter-pore exchange
- **When to invoke**: When several expected pore populations merge into one broad peak in the inversion, when peak positions fall between the geometric predictions, when a connected-pore model gives a smoother spectrum than an isolated-pore model, or when 1D T2 cannot separate pore populations.
- **Physical/mathematical mechanism**: Spins that diffuse between pores of different sizes average several local relaxation environments; when coupling is strong, the T2 distribution no longer equals the independent response of each pore-size population.
- **Citable sentence for reports**: Peak merging or spectral broadening does not necessarily mean that only one pore population is present; it may result from inter-pore diffusive coupling that mixes several relaxation environments. [@Grunewald2009PoreCoupling]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Surface relaxation, pore size and short T2
- **When to invoke**: When the short-T2 area is large, when the main peak shifts to shorter T2, when small-pore/high-surface-area models decay faster, or when the relation between T2 and pore size needs to be explained.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@Grunewald2009PoreCoupling]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Limits on peak/component interpretation (not a source for the Gaussian method)
- **When to invoke**: When the user asks to split a T2 spectrum into 2-3 peaks and interpret peak areas and positions, or when a change in the number of peaks changes the interpretation.
- **Physical/mathematical mechanism**: Gaussian peak splitting is an empirical approximation of the spectral shape on the log T2 axis; Whittall, Coates and similar works mainly support the point that inverted spectra and component interpretation require caution, and they should not be cited as the source of the Gaussian method.
- **Citable sentence for reports**: Peak-splitting results should serve as an interpretive aid and not as the sole evidence that the sample contains exactly the same number of physical pore populations. [@Grunewald2009PoreCoupling]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

## Search keywords

`component_assignment`, `diffusive_coupling`, `exchange`, `gaussian_decomposition`, `overfitting`, `peak_count`, `peak_merging`, `pore_coupling`, `pore_coupling_t2t2_interpretation`, `pore_size`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and search tags; consult the original publication for exact wording or page numbers.
- Main evidence topics: diffusive coupling and inter-pore exchange; surface relaxation, pore size and short T2; limits on peak/component interpretation (not a source for the Gaussian method).

## Limits of use

- Do not treat this reference as the sole basis for interpreting every sample; reports should take into account the user's data quality, T2 range, regularization, simulation geometry and parameter settings.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.