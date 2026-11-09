---
citation_key: LucasOliveira2018RestrictedDiffusion
category: 02_pore_scale_simulation_random_walk
tags: [eigenmodes, forward_simulation, geometry, monte_carlo, pore_scale, pore_scale_simulation_random_walk, pore_shape, pore_size, random_walk, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 9
---

# LucasOliveira2018RestrictedDiffusion

- **Title**: Computational approach to integrate 3D X-ray microtomography and NMR data
- **Suggested citation format**: `[@LucasOliveira2018RestrictedDiffusion]`
- **Rationale for inclusion**: Pore-scale random-walk/restricted-diffusion simulation; useful when comparing inverted spectra with real pore structure.
- **Role in the T2 agent**: Citation for pore-scale random-walk/Monte Carlo forward modelling; useful for explaining the mechanism chain from simulation to decay curve and T2 spectrum.
- **Extraction note**: Parsing warnings were raised during text extraction; check page numbers against the original publication before using this in a formal paper.

## Conclusions usable by the agent

### Random-walk/Monte Carlo forward simulation
- **When to use**: When the agent must explain why a random walk can simulate NMR decay, validate inversion results, or compare pore structure with the inverted T2 spectrum.
- **Physical/mathematical mechanism**: A random walk discretizes molecular diffusion into many particle trajectories and accumulates phase and decay through surface relaxation at the boundary, bulk relaxation and field inhomogeneity, producing an echo decay that can be inverted.
- **Citable sentence for reports**: Random-walk forward modelling provides a mechanistic bridge from pore geometry and physical parameters to the decay curve and T2 spectrum. [@LucasOliveira2018RestrictedDiffusion]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to use**: When a geometry change shifts or broadens T2 peaks, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal-decay problem governed by boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information produced by the combined action of pore-domain diffusion and boundary relaxation, not just the geometric pore size. [@LucasOliveira2018RestrictedDiffusion]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Surface relaxation, pore size and short T2
- **When to use**: When the short-T2 area is large, the main peak shifts toward short T2, small-pore or high-surface-area models decay faster, or the relation between T2 and pore size needs explaining.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-area-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-area-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@LucasOliveira2018RestrictedDiffusion]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

## Retrieval keywords

`eigenmodes`, `forward_simulation`, `geometry`, `monte_carlo`, `pore_scale`, `pore_scale_simulation_random_walk`, `pore_shape`, `pore_size`, `random_walk`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and retrieval tags; check the original publication for verbatim wording or page numbers.
- Main evidence topics: random-walk/Monte Carlo forward simulation; restricted diffusion, geometry and eigenmodes; surface relaxation, pore size and short T2.

## Usage limits

- Do not treat this reference as the sole basis for interpreting every sample; a report should also account for the user's data quality, T2 range, regularization, simulated geometry and parameter settings.
- When the same phenomenon can arise from several mechanisms, prefer hedged wording ("may", "suggests", "supports") over absolute statements.