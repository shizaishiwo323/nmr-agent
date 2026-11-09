---
citation_key: Hagslatt2002RestrictiveGeometries
category: 03_numerical_methods_fem_lbm_matrix
tags: [eigenmodes, geometry, numerical_methods_fem_lbm_matrix, pore_shape, pore_size, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 10
---

# Hagslatt2002RestrictiveGeometries

- **Suggested citation format**: `[@Hagslatt2002RestrictiveGeometries]`
- **Reason for inclusion**: Simulation of diffusion and relaxation in restrictive geometries, suited to explaining idealized-pore simulation results.
- **Role in the T2 agent**: Numerical-methods reference; suited to explaining FEM/FVM/LBM/matrix methods, boundary conditions, internal gradients or eigenmodes.

## Conclusions usable by the agent

### Restricted diffusion, geometry and eigenmodes
- **When to invoke**: When a change of geometry shifts or broadens the T2 peak, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal decay problem controlled by the boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information resulting from diffusion within the pore domain combined with boundary relaxation, not just the geometric pore size itself. [@Hagslatt2002RestrictiveGeometries]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Surface relaxation, pore size and short T2
- **When to invoke**: When the short-T2 area is large, when the main peak shifts to shorter T2, when small-pore/high-surface-area models decay faster, or when the relation between T2 and pore size needs to be explained.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@Hagslatt2002RestrictiveGeometries]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

## Search keywords

`eigenmodes`, `geometry`, `numerical_methods_fem_lbm_matrix`, `pore_shape`, `pore_size`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and search tags; consult the original publication for exact wording or page numbers.
- Main evidence topics: restricted diffusion, geometry and eigenmodes; surface relaxation, pore size and short T2.

## Limits of use

- Do not treat this reference as the sole basis for interpreting every sample; reports should take into account the user's data quality, T2 range, regularization, simulation geometry and parameter settings.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.