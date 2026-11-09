---
citation_key: Tandon2018FiniteVolumeInternalGradients
category: 03_numerical_methods_fem_lbm_matrix
tags: [dephasing, echo_spacing, eigenmodes, field_inhomogeneity, finite_element, finite_volume, geometry, internal_gradient, mesh, numerical_methods_fem_lbm_matrix, pde_solver, pore_shape, restricted_diffusion]
pages: 18
---

# Tandon2018FiniteVolumeInternalGradients

- **Suggested citation format**: `[@Tandon2018FiniteVolumeInternalGradients]`
- **Rationale for inclusion**: Finite-volume method and internal-gradient effects; useful for explaining the influence of boundary conditions and gradients in numerical models.
- **Role in the T2 agent**: Citation for numerical methods; useful for explaining FEM/FVM/LBM/matrix methods, boundary conditions, internal gradients or eigenmodes.

## Conclusions usable by the agent

### FEM/FVM numerical solution
- **When to use**: When a simulation uses a mesh, finite elements/finite volumes, COMSOL or an internal-gradient model, and the effect of boundary conditions, mesh and numerical solution on the decay must be explained.
- **Physical/mathematical mechanism**: FEM/FVM solve the diffusion-relaxation partial differential equation to compute magnetization evolution in the pore domain; boundary conditions encode surface relaxation, and internal-gradient or field terms introduce additional dephasing.
- **Citable sentence for reports**: Mesh-based numerical simulation can include complex pore geometry, boundary relaxation and internal gradients explicitly in the NMR forward model. [@Tandon2018FiniteVolumeInternalGradients]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Internal gradients and field inhomogeneity
- **When to use**: When the simulated decay is faster than a pure surface-relaxation model, the long-T2 end is suppressed, changing the echo spacing alters the spectral shape, or susceptibility contrast causes additional decay.
- **Physical/mathematical mechanism**: Internal magnetic-field gradients coupled with diffusion cause additional dephasing; this term depends on the diffusion coefficient, gradient strength, echo spacing and pore scale.
- **Citable sentence for reports**: A shortened T2 does not necessarily come only from small pores or high surface relaxivity; it may also come from diffusion dephasing induced by internal gradients. [@Tandon2018FiniteVolumeInternalGradients]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to use**: When a geometry change shifts or broadens T2 peaks, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal-decay problem governed by boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information produced by the combined action of pore-domain diffusion and boundary relaxation, not just the geometric pore size. [@Tandon2018FiniteVolumeInternalGradients]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

## Retrieval keywords

`dephasing`, `echo_spacing`, `eigenmodes`, `field_inhomogeneity`, `finite_element`, `finite_volume`, `geometry`, `internal_gradient`, `mesh`, `numerical_methods_fem_lbm_matrix`, `pde_solver`, `pore_shape`, `restricted_diffusion`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and retrieval tags; check the original publication for verbatim wording or page numbers.
- Main evidence topics: FEM/FVM numerical solution; internal gradients and field inhomogeneity; restricted diffusion, geometry and eigenmodes.

## Usage limits

- Do not treat this reference as the sole basis for interpreting every sample; a report should also account for the user's data quality, T2 range, regularization, simulated geometry and parameter settings.
- When the same phenomenon can arise from several mechanisms, prefer hedged wording ("may", "suggests", "supports") over absolute statements.