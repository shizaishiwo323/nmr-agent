---
citation_key: Gonzalez2020FieldInhomogeneities
category: 02_pore_scale_simulation_random_walk
tags: [dephasing, echo_spacing, eigenmodes, field_inhomogeneity, forward_simulation, geometry, internal_gradient, monte_carlo, pore_scale, pore_scale_simulation_random_walk, pore_shape, random_walk, restricted_diffusion]
pages: 15
---

# Gonzalez2020FieldInhomogeneities

- **Title**: Simulations of NMR Relaxation in a Real Porous Structure: Pre-asymptotic Behavior to the Localization Regime
- **Suggested citation format**: `[@Gonzalez2020FieldInhomogeneities]`
- **Reason for inclusion**: Effect of non-uniform fields/internal gradients on the NMR response; can explain the source of discrepancies between simulation and inversion.
- **Role in the T2 agent**: Pore-scale random-walk/Monte Carlo forward-simulation reference; suited to explaining the mechanism chain from simulation to decay curve/T2 spectrum.

## Conclusions usable by the agent

### Internal gradients/field inhomogeneity
- **When to invoke**: When the simulated decay is faster than a pure surface-relaxation model, when the long-T2 end is suppressed, when changing the echo spacing alters the spectral shape, or when susceptibility contrast causes extra decay.
- **Physical/mathematical mechanism**: Internal magnetic-field gradients combined with diffusion cause additional dephasing; this term depends on the diffusion coefficient, gradient strength, echo spacing and pore size.
- **Citable sentence for reports**: A shortened T2 does not necessarily come only from small pores or a high surface relaxivity; it may also come from diffusion dephasing induced by internal gradients. [@Gonzalez2020FieldInhomogeneities]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Random-walk/Monte Carlo forward simulation
- **When to invoke**: When it is necessary to explain why a random walk can simulate NMR decay, to validate inversion results, or to compare the pore structure with the inverted T2 spectrum.
- **Physical/mathematical mechanism**: A random walk discretizes molecular diffusion into many particle trajectories and accumulates phase/decay under boundary (surface) relaxation, bulk relaxation and field inhomogeneity, producing an echo decay that can be inverted.
- **Citable sentence for reports**: Random-walk forward simulation provides a mechanistic bridge from pore geometry and physical parameters to the decay curve/T2 spectrum. [@Gonzalez2020FieldInhomogeneities]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to invoke**: When a change of geometry shifts or broadens the T2 peak, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal decay problem controlled by the boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information resulting from diffusion within the pore domain combined with boundary relaxation, not just the geometric pore size itself. [@Gonzalez2020FieldInhomogeneities]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

## Search keywords

`dephasing`, `echo_spacing`, `eigenmodes`, `field_inhomogeneity`, `forward_simulation`, `geometry`, `internal_gradient`, `monte_carlo`, `pore_scale`, `pore_scale_simulation_random_walk`, `pore_shape`, `random_walk`, `restricted_diffusion`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and search tags; consult the original publication for exact wording or page numbers.
- Main evidence topics: internal gradients/field inhomogeneity; random-walk/Monte Carlo forward simulation; restricted diffusion, geometry and eigenmodes.

## Limits of use

- Do not treat this reference as the sole basis for interpreting every sample; reports should take into account the user's data quality, T2 range, regularization, simulation geometry and parameter settings.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.