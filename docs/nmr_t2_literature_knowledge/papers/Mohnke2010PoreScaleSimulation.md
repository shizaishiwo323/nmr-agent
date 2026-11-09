---
citation_key: Mohnke2010PoreScaleSimulation
category: 03_numerical_methods_fem_lbm_matrix
tags: [dephasing, echo_spacing, eigenmodes, field_inhomogeneity, finite_element, finite_volume, geometry, internal_gradient, mesh, numerical_methods_fem_lbm_matrix, pde_solver, pore_shape, pore_size, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 12
---

# Mohnke2010PoreScaleSimulation

- **Title**: Microscale Simulations of NMR Relaxation in Porous Media Considering Internal Field Gradients
- **Suggested citation format**: `[@Mohnke2010PoreScaleSimulation]`
- **Rationale for inclusion**: Background on pore-scale numerical simulation, internal gradients and surface relaxation.
- **Role in the T2 agent**: Citation for pore-scale FEM and internal gradients: surface relaxation, internal gradients and pore-scale finite-element simulation.
- **Extraction note**: Parsing warnings were raised during text extraction; check page numbers against the original publication before using this in a formal paper.

## Conclusions usable by the agent

### FEM/FVM numerical solution
- **When to use**: When a simulation uses a mesh, finite elements/finite volumes, COMSOL or an internal-gradient model, and the effect of boundary conditions, mesh and numerical solution on the decay must be explained.
- **Physical/mathematical mechanism**: FEM/FVM solve the diffusion-relaxation partial differential equation to compute magnetization evolution in the pore domain; boundary conditions encode surface relaxation, and internal-gradient or field terms introduce additional dephasing.
- **Citable sentence for reports**: Mesh-based numerical simulation can include complex pore geometry, boundary relaxation and internal gradients explicitly in the NMR forward model. [@Mohnke2010PoreScaleSimulation]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Internal gradients and field inhomogeneity
- **When to use**: When the simulated decay is faster than a pure surface-relaxation model, the long-T2 end is suppressed, changing the echo spacing alters the spectral shape, or susceptibility contrast causes additional decay.
- **Physical/mathematical mechanism**: Internal magnetic-field gradients coupled with diffusion cause additional dephasing; this term depends on the diffusion coefficient, gradient strength, echo spacing and pore scale.
- **Citable sentence for reports**: A shortened T2 does not necessarily come only from small pores or high surface relaxivity; it may also come from diffusion dephasing induced by internal gradients. [@Mohnke2010PoreScaleSimulation]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Surface relaxation, pore size and short T2
- **When to use**: When the short-T2 area is large, the main peak shifts toward short T2, small-pore or high-surface-area models decay faster, or the relation between T2 and pore size needs explaining.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-area-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-area-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@Mohnke2010PoreScaleSimulation]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to use**: When a geometry change shifts or broadens T2 peaks, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal-decay problem governed by boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information produced by the combined action of pore-domain diffusion and boundary relaxation, not just the geometric pore size. [@Mohnke2010PoreScaleSimulation]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

## Retrieval keywords

`dephasing`, `echo_spacing`, `eigenmodes`, `field_inhomogeneity`, `finite_element`, `finite_volume`, `geometry`, `internal_gradient`, `mesh`, `numerical_methods_fem_lbm_matrix`, `pde_solver`, `pore_shape`, `pore_size`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- p.2: The text states that FEM is used to simulate NMR processes at the pore scale.
- p.3: The text defines surface relaxivity and uses it as the parameter for surface-relaxation strength.
- p.3: The text states that internal gradients can be caused by the susceptibility contrast between pore fluid and matrix, and are not part of surface relaxation.
- Main evidence topics: FEM/FVM numerical solution; internal gradients and field inhomogeneity; surface relaxation, pore size and short T2; restricted diffusion, geometry and eigenmodes.

## Usage limits

- Do not treat this reference as the sole basis for interpreting every sample; a report should also account for the user's data quality, T2 range, regularization, simulated geometry and parameter settings.
- When the same phenomenon can arise from several mechanisms, prefer hedged wording ("may", "suggests", "supports") over absolute statements.