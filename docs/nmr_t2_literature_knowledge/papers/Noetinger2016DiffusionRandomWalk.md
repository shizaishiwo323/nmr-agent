---
citation_key: Noetinger2016DiffusionRandomWalk
category: 02_pore_scale_simulation_random_walk
tags: [eigenmodes, forward_simulation, geometry, monte_carlo, pore_scale, pore_scale_simulation_random_walk, pore_shape, random_walk, restricted_diffusion]
pages: 45
---

# Noetinger2016DiffusionRandomWalk

- **Suggested citation format**: `[@Noetinger2016DiffusionRandomWalk]`
- **Rationale for inclusion**: Strong theoretical background on diffusion and random walks; suited as an in-depth theory supplement.
- **Role in the T2 agent**: Citation for pore-scale random-walk/Monte Carlo forward modelling; useful for explaining the mechanism chain from simulation to decay curve and T2 spectrum.

## Conclusions usable by the agent

### Random-walk/Monte Carlo forward simulation
- **When to use**: When the agent must explain why a random walk can simulate NMR decay, validate inversion results, or compare pore structure with the inverted T2 spectrum.
- **Physical/mathematical mechanism**: A random walk discretizes molecular diffusion into many particle trajectories and accumulates phase and decay through surface relaxation at the boundary, bulk relaxation and field inhomogeneity, producing an echo decay that can be inverted.
- **Citable sentence for reports**: Random-walk forward modelling provides a mechanistic bridge from pore geometry and physical parameters to the decay curve and T2 spectrum. [@Noetinger2016DiffusionRandomWalk]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to use**: When a geometry change shifts or broadens T2 peaks, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal-decay problem governed by boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information produced by the combined action of pore-domain diffusion and boundary relaxation, not just the geometric pore size. [@Noetinger2016DiffusionRandomWalk]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

## Retrieval keywords

`eigenmodes`, `forward_simulation`, `geometry`, `monte_carlo`, `pore_scale`, `pore_scale_simulation_random_walk`, `pore_shape`, `random_walk`, `restricted_diffusion`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and retrieval tags; check the original publication for verbatim wording or page numbers.
- Main evidence topics: random-walk/Monte Carlo forward simulation; restricted diffusion, geometry and eigenmodes.

## Usage limits

- Do not treat this reference as the sole basis for interpreting every sample; a report should also account for the user's data quality, T2 range, regularization, simulated geometry and parameter settings.
- When the same phenomenon can arise from several mechanisms, prefer hedged wording ("may", "suggests", "supports") over absolute statements.