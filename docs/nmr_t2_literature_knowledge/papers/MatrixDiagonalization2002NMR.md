---
citation_key: MatrixDiagonalization2002NMR
category: 03_numerical_methods_fem_lbm_matrix
tags: [analytical_forward_model, eigenmodes, eigenvalues, geometry, matrix_diagonalization, numerical_methods_fem_lbm_matrix, pore_shape, restricted_diffusion]
pages: 12
---

# MatrixDiagonalization2002NMR

- **Title**: Magnetization Evolution in Network Models of Porous Rock under Conditions of Drainage and Imbibition
- **Suggested citation format**: `[@MatrixDiagonalization2002NMR]`
- **Rationale for inclusion**: Paper related to matrix diagonalization methods; adds eigenvalue/mode-based interpretation.
- **Role in the T2 agent**: Citation for numerical methods; useful for explaining FEM/FVM/LBM/matrix methods, boundary conditions, internal gradients or eigenmodes.

## Conclusions usable by the agent

### Matrix diagonalization and eigenmode methods
- **When to use**: When the agent must explain why a complex decay can be represented as a superposition of several eigenmodes, or compare random-walk/FEM with eigenvalue-based forward methods.
- **Physical/mathematical mechanism**: After discretization the diffusion-relaxation operator can be expressed through eigenvalues and eigenvectors, and the decay curve is composed of contributions from several modes; boundary conditions and pore state change the eigenspectrum.
- **Citable sentence for reports**: Multi-exponential decay can be understood as a superposition of several eigenmodes of the diffusion-relaxation system, not merely a simple sum over isolated pore populations. [@MatrixDiagonalization2002NMR]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to use**: When a geometry change shifts or broadens T2 peaks, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal-decay problem governed by boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information produced by the combined action of pore-domain diffusion and boundary relaxation, not just the geometric pore size. [@MatrixDiagonalization2002NMR]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

## Retrieval keywords

`analytical_forward_model`, `eigenmodes`, `eigenvalues`, `geometry`, `matrix_diagonalization`, `numerical_methods_fem_lbm_matrix`, `pore_shape`, `restricted_diffusion`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and retrieval tags; check the original publication for verbatim wording or page numbers.
- Main evidence topics: matrix diagonalization and eigenmode methods; restricted diffusion, geometry and eigenmodes.

## Usage limits

- Do not treat this reference as the sole basis for interpreting every sample; a report should also account for the user's data quality, T2 range, regularization, simulated geometry and parameter settings.
- When the same phenomenon can arise from several mechanisms, prefer hedged wording ("may", "suggests", "supports") over absolute statements.