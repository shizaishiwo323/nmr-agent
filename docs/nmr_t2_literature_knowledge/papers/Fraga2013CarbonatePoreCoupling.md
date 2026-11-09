---
citation_key: Fraga2013CarbonatePoreCoupling
category: 02_pore_scale_simulation_random_walk
tags: [diffusive_coupling, exchange, forward_simulation, monte_carlo, peak_merging, pore_coupling, pore_scale, pore_scale_simulation_random_walk, pore_size, random_walk, short_t2, surface_relaxation, surface_relaxivity]
pages: 4
---

# Fraga2013CarbonatePoreCoupling

- **Suggested citation format**: `[@Fraga2013CarbonatePoreCoupling]`
- **Reason for inclusion**: Random-walk simulation of pore coupling in carbonates, suited to supporting T2-spectrum interpretation in complex pore structures.
- **Role in the T2 agent**: Pore-scale random-walk/Monte Carlo forward-simulation reference; suited to explaining the mechanism chain from simulation to decay curve/T2 spectrum.

## Conclusions usable by the agent

### Diffusive coupling and inter-pore exchange
- **When to invoke**: When several expected pore populations merge into one broad peak in the inversion, when peak positions fall between the geometric predictions, when a connected-pore model gives a smoother spectrum than an isolated-pore model, or when 1D T2 cannot separate pore populations.
- **Physical/mathematical mechanism**: Spins that diffuse between pores of different sizes average several local relaxation environments; when coupling is strong, the T2 distribution no longer equals the independent response of each pore-size population.
- **Citable sentence for reports**: Peak merging or spectral broadening does not necessarily mean that only one pore population is present; it may result from inter-pore diffusive coupling that mixes several relaxation environments. [@Fraga2013CarbonatePoreCoupling]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Random-walk/Monte Carlo forward simulation
- **When to invoke**: When it is necessary to explain why a random walk can simulate NMR decay, to validate inversion results, or to compare the pore structure with the inverted T2 spectrum.
- **Physical/mathematical mechanism**: A random walk discretizes molecular diffusion into many particle trajectories and accumulates phase/decay under boundary (surface) relaxation, bulk relaxation and field inhomogeneity, producing an echo decay that can be inverted.
- **Citable sentence for reports**: Random-walk forward simulation provides a mechanistic bridge from pore geometry and physical parameters to the decay curve/T2 spectrum. [@Fraga2013CarbonatePoreCoupling]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Surface relaxation, pore size and short T2
- **When to invoke**: When the short-T2 area is large, when the main peak shifts to shorter T2, when small-pore/high-surface-area models decay faster, or when the relation between T2 and pore size needs to be explained.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@Fraga2013CarbonatePoreCoupling]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

## Search keywords

`diffusive_coupling`, `exchange`, `forward_simulation`, `monte_carlo`, `peak_merging`, `pore_coupling`, `pore_scale`, `pore_scale_simulation_random_walk`, `pore_size`, `random_walk`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and search tags; consult the original publication for exact wording or page numbers.
- Main evidence topics: diffusive coupling and inter-pore exchange; random-walk/Monte Carlo forward simulation; surface relaxation, pore size and short T2.

## Limits of use

- Do not treat this reference as the sole basis for interpreting every sample; reports should take into account the user's data quality, T2 range, regularization, simulation geometry and parameter settings.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.