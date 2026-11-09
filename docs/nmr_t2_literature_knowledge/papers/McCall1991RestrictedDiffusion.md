---
citation_key: McCall1991RestrictedDiffusion
category: 02_pore_scale_simulation_random_walk
tags: [analytical_forward_model, eigenmodes, eigenvalues, geometry, matrix_diagonalization, pore_scale_simulation_random_walk, pore_shape, pore_size, restricted_diffusion, short_t2, surface_relaxation, surface_relaxivity]
pages: 14
---

# McCall1991RestrictedDiffusion

- **Title**: Magnetization evolution in connected pore systems
- **Suggested citation format**: `[@McCall1991RestrictedDiffusion]`
- **Rationale for inclusion**: Classic simulation reference for NMR/diffusion theory in restricted geometries.
- **Role in the T2 agent**: Citation for pore-scale random-walk/Monte Carlo forward modelling; useful for explaining the mechanism chain from simulation to decay curve and T2 spectrum.

## Conclusions usable by the agent

### Restricted diffusion, geometry and eigenmodes
- **When to use**: When a geometry change shifts or broadens T2 peaks, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal-decay problem governed by boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information produced by the combined action of pore-domain diffusion and boundary relaxation, not just the geometric pore size. [@McCall1991RestrictedDiffusion]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Matrix diagonalization and eigenmode methods
- **When to use**: When the agent must explain why a complex decay can be represented as a superposition of several eigenmodes, or compare random-walk/FEM with eigenvalue-based forward methods.
- **Physical/mathematical mechanism**: After discretization the diffusion-relaxation operator can be expressed through eigenvalues and eigenvectors, and the decay curve is composed of contributions from several modes; boundary conditions and pore state change the eigenspectrum.
- **Citable sentence for reports**: Multi-exponential decay can be understood as a superposition of several eigenmodes of the diffusion-relaxation system, not merely a simple sum over isolated pore populations. [@McCall1991RestrictedDiffusion]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Surface relaxation, pore size and short T2
- **When to use**: When the short-T2 area is large, the main peak shifts toward short T2, small-pore or high-surface-area models decay faster, or the relation between T2 and pore size needs explaining.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-area-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-area-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@McCall1991RestrictedDiffusion]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

## Retrieval keywords

`analytical_forward_model`, `eigenmodes`, `eigenvalues`, `geometry`, `matrix_diagonalization`, `pore_scale_simulation_random_walk`, `pore_shape`, `pore_size`, `restricted_diffusion`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and retrieval tags; check the original publication for verbatim wording or page numbers.
- Main evidence topics: restricted diffusion, geometry and eigenmodes; matrix diagonalization and eigenmode methods; surface relaxation, pore size and short T2.

## Usage limits

- Do not treat this reference as the sole basis for interpreting every sample; a report should also account for the user's data quality, T2 range, regularization, simulated geometry and parameter settings.
- When the same phenomenon can arise from several mechanisms, prefer hedged wording ("may", "suggests", "supports") over absolute statements.