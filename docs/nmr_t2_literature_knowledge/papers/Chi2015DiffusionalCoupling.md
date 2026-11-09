---
citation_key: Chi2015DiffusionalCoupling
category: 02_pore_scale_simulation_random_walk
tags: [diffusive_coupling, eigenmodes, exchange, forward_simulation, geometry, monte_carlo, peak_merging, pore_coupling, pore_scale, pore_scale_simulation_random_walk, pore_shape, pore_size, random_walk, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 12
---

# Chi2015DiffusionalCoupling

- **Suggested citation format**: `[@Chi2015DiffusionalCoupling]`
- **Reason for inclusion**: Diffusive coupling mixes the signals of different pore populations, which is an important basis for explaining merged peaks or changes in spectral shape.
- **Role in the T2 agent**: Pore-scale random-walk/Monte Carlo forward-simulation reference; suited to explaining the mechanism chain from simulation to decay curve/T2 spectrum.
- **Extraction note**: Check page numbers against the original publication before citing.

## Conclusions usable by the agent

### Diffusive coupling and inter-pore exchange
- **When to invoke**: When several expected pore populations merge into one broad peak in the inversion, when peak positions fall between the geometric predictions, when a connected-pore model gives a smoother spectrum than an isolated-pore model, or when 1D T2 cannot separate pore populations.
- **Physical/mathematical mechanism**: Spins that diffuse between pores of different sizes average several local relaxation environments; when coupling is strong, the T2 distribution no longer equals the independent response of each pore-size population.
- **Citable sentence for reports**: Peak merging or spectral broadening does not necessarily mean that only one pore population is present; it may result from inter-pore diffusive coupling that mixes several relaxation environments. [@Chi2015DiffusionalCoupling]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Random-walk/Monte Carlo forward simulation
- **When to invoke**: When it is necessary to explain why a random walk can simulate NMR decay, to validate inversion results, or to compare the pore structure with the inverted T2 spectrum.
- **Physical/mathematical mechanism**: A random walk discretizes molecular diffusion into many particle trajectories and accumulates phase/decay under boundary (surface) relaxation, bulk relaxation and field inhomogeneity, producing an echo decay that can be inverted.
- **Citable sentence for reports**: Random-walk forward simulation provides a mechanistic bridge from pore geometry and physical parameters to the decay curve/T2 spectrum. [@Chi2015DiffusionalCoupling]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Surface relaxation, pore size and short T2
- **When to invoke**: When the short-T2 area is large, when the main peak shifts to shorter T2, when small-pore/high-surface-area models decay faster, or when the relation between T2 and pore size needs to be explained.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@Chi2015DiffusionalCoupling]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to invoke**: When a change of geometry shifts or broadens the T2 peak, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal decay problem controlled by the boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information resulting from diffusion within the pore domain combined with boundary relaxation, not just the geometric pore size itself. [@Chi2015DiffusionalCoupling]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

## Search keywords

`diffusive_coupling`, `eigenmodes`, `exchange`, `forward_simulation`, `geometry`, `monte_carlo`, `peak_merging`, `pore_coupling`, `pore_scale`, `pore_scale_simulation_random_walk`, `pore_shape`, `pore_size`, `random_walk`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and search tags; consult the original publication for exact wording or page numbers.
- Main evidence topics: diffusive coupling and inter-pore exchange; random-walk/Monte Carlo forward simulation; surface relaxation, pore size and short T2; restricted diffusion, geometry and eigenmodes.

## Limits of use

- Do not treat this reference as the sole basis for interpreting every sample; reports should take into account the user's data quality, T2 range, regularization, simulation geometry and parameter settings.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.