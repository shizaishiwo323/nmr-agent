---
citation_key: Guyer2000LBMDiffusion
category: 03_numerical_methods_fem_lbm_matrix
tags: [eigenmodes, geometry, lattice_boltzmann, lbm, numerical_methods_fem_lbm_matrix, pore_network, pore_shape, restricted_diffusion]
pages: 15
---

# Guyer2000LBMDiffusion

- **Suggested citation format**: `[@Guyer2000LBMDiffusion]`
- **Reason for inclusion**: Foundations of the lattice Boltzmann method, supporting the explanation of LBM simulation.
- **Role in the T2 agent**: Numerical-methods reference; suited to explaining FEM/FVM/LBM/matrix methods, boundary conditions, internal gradients or eigenmodes.

## Conclusions usable by the agent

### LBM diffusion/relaxation simulation
- **When to invoke**: When it is necessary to explain why the lattice Boltzmann method is suited to pore-scale diffusion, complex boundaries and forward modelling of connected pore spaces.
- **Physical/mathematical mechanism**: LBM advances distribution functions on a lattice, can handle diffusion in complex boundaries and connected pore structures, and can be combined with a surface-relaxation boundary.
- **Citable sentence for reports**: LBM is a pore-scale numerical method linking digital pore structures to the NMR decay response. [@Guyer2000LBMDiffusion]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to invoke**: When a change of geometry shifts or broadens the T2 peak, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal decay problem controlled by the boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information resulting from diffusion within the pore domain combined with boundary relaxation, not just the geometric pore size itself. [@Guyer2000LBMDiffusion]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

## Search keywords

`eigenmodes`, `geometry`, `lattice_boltzmann`, `lbm`, `numerical_methods_fem_lbm_matrix`, `pore_network`, `pore_shape`, `restricted_diffusion`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and search tags; consult the original publication for exact wording or page numbers.
- Main evidence topics: LBM diffusion/relaxation simulation; restricted diffusion, geometry and eigenmodes.

## Limits of use

- Do not treat this reference as the sole basis for interpreting every sample; reports should take into account the user's data quality, T2 range, regularization, simulation geometry and parameter settings.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.