---
citation_key: Mohnke2014LBMNMR
category: 03_numerical_methods_fem_lbm_matrix
tags: [diffusive_coupling, eigenmodes, exchange, geometry, lattice_boltzmann, lbm, numerical_methods_fem_lbm_matrix, peak_merging, pore_coupling, pore_network, pore_shape, pore_size, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 16
---

# Mohnke2014LBMNMR

- **Suggested citation format**: `[@Mohnke2014LBMNMR]`
- **Rationale for inclusion**: Background on LBM/pore-scale NMR simulation; suited for comparison with random-walk and FEM approaches.
- **Role in the T2 agent**: Citation for numerical methods; useful for explaining FEM/FVM/LBM/matrix methods, boundary conditions, internal gradients or eigenmodes.

## Conclusions usable by the agent

### LBM diffusion/relaxation simulation
- **When to use**: When the agent must explain why the lattice Boltzmann method suits pore-scale diffusion, complex boundaries and forward modelling of connected pore spaces.
- **Physical/mathematical mechanism**: LBM advances distribution functions on a lattice, can handle diffusion in complex boundaries and connected pore structures, and can be combined with surface-relaxation boundaries.
- **Citable sentence for reports**: LBM is a pore-scale numerical method that links digital pore structure to the NMR decay response. [@Mohnke2014LBMNMR]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Surface relaxation, pore size and short T2
- **When to use**: When the short-T2 area is large, the main peak shifts toward short T2, small-pore or high-surface-area models decay faster, or the relation between T2 and pore size needs explaining.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-area-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-area-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@Mohnke2014LBMNMR]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Diffusive coupling and inter-pore exchange
- **When to use**: When several expected pore populations merge into one broad peak in the inversion, the peak position falls between geometric predictions, the connected-pore model is smoother than the isolated-pore model, or 1D T2 cannot separate pore populations.
- **Physical/mathematical mechanism**: Spins that diffuse between pores of different sizes average over several local relaxation environments; when coupling is strong, the T2 distribution no longer equals the independent responses of the individual pore-size groups.
- **Citable sentence for reports**: Peak merging or spectral broadening does not necessarily mean that only one pore population exists; it can also result from inter-pore diffusive coupling that mixes several relaxation environments. [@Mohnke2014LBMNMR]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to use**: When a geometry change shifts or broadens T2 peaks, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal-decay problem governed by boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information produced by the combined action of pore-domain diffusion and boundary relaxation, not just the geometric pore size. [@Mohnke2014LBMNMR]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

## Retrieval keywords

`diffusive_coupling`, `eigenmodes`, `exchange`, `geometry`, `lattice_boltzmann`, `lbm`, `numerical_methods_fem_lbm_matrix`, `peak_merging`, `pore_coupling`, `pore_network`, `pore_shape`, `pore_size`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and retrieval tags; check the original publication for verbatim wording or page numbers.
- Main evidence topics: LBM diffusion/relaxation simulation; surface relaxation, pore size and short T2; diffusive coupling and inter-pore exchange; restricted diffusion, geometry and eigenmodes.

## Usage limits

- Do not treat this reference as the sole basis for interpreting every sample; a report should also account for the user's data quality, T2 range, regularization, simulated geometry and parameter settings.
- When the same phenomenon can arise from several mechanisms, prefer hedged wording ("may", "suggests", "supports") over absolute statements.