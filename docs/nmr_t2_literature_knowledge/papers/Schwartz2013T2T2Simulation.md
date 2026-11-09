---
citation_key: Schwartz2013T2T2Simulation
category: 03_numerical_methods_fem_lbm_matrix
tags: [diffusive_coupling, exchange, ill_posed, inverse_laplace, multidimensional_nmr, nnls, numerical_methods_fem_lbm_matrix, peak_merging, pore_coupling, regularization, regularized_inversion, t1_t2, t2_t2]
pages: 13
---

# Schwartz2013T2T2Simulation

- **Suggested citation format**: `[@Schwartz2013T2T2Simulation]`
- **Rationale for inclusion**: Simulation/inversion interpretation of T2-T2 and related 2D NMR; supports the interpretation of pore coupling and spectral shape.
- **Role in the T2 agent**: Citation for numerical methods; useful for explaining FEM/FVM/LBM/matrix methods, boundary conditions, internal gradients or eigenmodes.

## Conclusions usable by the agent

### T2-T2/T1-T2 multidimensional NMR and exchange
- **When to use**: When a 1D T2 spectrum cannot distinguish coupling/exchange, fluid components or complex pore environments, and it is necessary to explain that 2D NMR provides stronger constraints.
- **Physical/mathematical mechanism**: Two-dimensional correlation experiments encode relaxation correlations across different waiting/mixing periods into a 2D spectrum, which can reveal exchange, coupling and links between different fluid or pore environments.
- **Citable sentence for reports**: In complex samples, 1D T2 peaks cannot always be uniquely assigned to physical pore populations, and multidimensional NMR can serve as a check and an additional constraint. [@Schwartz2013T2T2Simulation]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Diffusive coupling and inter-pore exchange
- **When to use**: When several expected pore populations merge into one broad peak in the inversion, the peak position falls between geometric predictions, the connected-pore model is smoother than the isolated-pore model, or 1D T2 cannot separate pore populations.
- **Physical/mathematical mechanism**: Spins that diffuse between pores of different sizes average over several local relaxation environments; when coupling is strong, the T2 distribution no longer equals the independent responses of the individual pore-size groups.
- **Citable sentence for reports**: Peak merging or spectral broadening does not necessarily mean that only one pore population exists; it can also result from inter-pore diffusive coupling that mixes several relaxation environments. [@Schwartz2013T2T2Simulation]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Ill-posedness of the inversion and regularization
- **When to use**: When the inverted T2 spectrum shows noise oscillations or spurious peaks, when changing the regularization factor clearly changes the number or width of peaks, or when the need for NNLS/smoothness constraints must be explained.
- **Physical/mathematical mechanism**: Recovering a T2 distribution from a CPMG decay is a multi-exponential, inverse-Laplace-type problem in which noise and the sampling range are amplified; non-negativity and smoothness regularization trade off the fit residual against spectral smoothness.
- **Citable sentence for reports**: The T2 spectrum is not a unique direct reading of the decay curve but an inversion result shaped by noise, the sampling window and regularization constraints. [@Schwartz2013T2T2Simulation]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

## Retrieval keywords

`diffusive_coupling`, `exchange`, `ill_posed`, `inverse_laplace`, `multidimensional_nmr`, `nnls`, `numerical_methods_fem_lbm_matrix`, `peak_merging`, `pore_coupling`, `regularization`, `regularized_inversion`, `t1_t2`, `t2_t2`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and retrieval tags; check the original publication for verbatim wording or page numbers.
- Main evidence topics: T2-T2/T1-T2 multidimensional NMR and exchange; diffusive coupling and inter-pore exchange; ill-posedness of the inversion and regularization.

## Usage limits

- Do not treat this reference as the sole basis for interpreting every sample; a report should also account for the user's data quality, T2 range, regularization, simulated geometry and parameter settings.
- When the same phenomenon can arise from several mechanisms, prefer hedged wording ("may", "suggests", "supports") over absolute statements.