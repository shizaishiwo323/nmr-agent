---
citation_key: Chang2001DrainageSaturationHistory
category: 03_numerical_methods_fem_lbm_matrix
tags: [analytical_forward_model, eigenmodes, eigenvalues, geometry, matrix_diagonalization, numerical_methods_fem_lbm_matrix, pore_shape, pore_size, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 11
---

# Chang2001DrainageSaturationHistory

- **Suggested citation format**: `[@Chang2001DrainageSaturationHistory]`
- **Reason for inclusion**: Simulation background on matrix methods and on the effect of saturation/drainage conditions on the NMR response.
- **Role in the T2 agent**: Numerical-methods reference; suited to explaining FEM/FVM/LBM/matrix methods, boundary conditions, internal gradients or eigenmodes.
- **Extraction note**: Check page numbers against the original publication before citing.

## Conclusions usable by the agent

### Matrix diagonalization/eigenmode methods
- **When to invoke**: When it is necessary to explain why a complex decay can be represented as a superposition of eigenmodes, or to compare random-walk/FEM and eigenvalue forward methods.
- **Physical/mathematical mechanism**: After discretization, the diffusion-relaxation operator can be expressed through eigenvalues/eigenvectors, and the decay curve is composed of contributions from several modes; boundary conditions and the pore state change the eigenspectrum.
- **Citable sentence for reports**: A multi-exponential decay can be understood as a superposition of several eigenmodes of a diffusion-relaxation system, and not merely as a simple sum over isolated pore populations. [@Chang2001DrainageSaturationHistory]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Surface relaxation, pore size and short T2
- **When to invoke**: When the short-T2 area is large, when the main peak shifts to shorter T2, when small-pore/high-surface-area models decay faster, or when the relation between T2 and pore size needs to be explained.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@Chang2001DrainageSaturationHistory]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to invoke**: When a change of geometry shifts or broadens the T2 peak, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal decay problem controlled by the boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information resulting from diffusion within the pore domain combined with boundary relaxation, not just the geometric pore size itself. [@Chang2001DrainageSaturationHistory]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

## Search keywords

`analytical_forward_model`, `eigenmodes`, `eigenvalues`, `geometry`, `matrix_diagonalization`, `numerical_methods_fem_lbm_matrix`, `pore_shape`, `pore_size`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and search tags; consult the original publication for exact wording or page numbers.
- Main evidence topics: matrix diagonalization/eigenmode methods; surface relaxation, pore size and short T2; restricted diffusion, geometry and eigenmodes.

## Limits of use

- Do not treat this reference as the sole basis for interpreting every sample; reports should take into account the user's data quality, T2 range, regularization, simulation geometry and parameter settings.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.