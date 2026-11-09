---
citation_key: Tan2012T2T1Simulation
category: 03_numerical_methods_fem_lbm_matrix
tags: [cpmg, echo_spacing, echo_train, exchange, forward_simulation, monte_carlo, multidimensional_nmr, numerical_methods_fem_lbm_matrix, pore_scale, pulse_sequence, random_walk, sampling, t1_t2, t2_t2]
pages: 13
---

# Tan2012T2T1Simulation

- **Suggested citation format**: `[@Tan2012T2T1Simulation]`
- **Rationale for inclusion**: Numerical simulation of 2D NMR and fluid identification; suited for extension to multidimensional response interpretation.
- **Role in the T2 agent**: Citation for numerical methods; useful for explaining FEM/FVM/LBM/matrix methods, boundary conditions, internal gradients or eigenmodes.
- **Extraction note**: Parsing warnings were raised during text extraction; check page numbers against the original publication before using this in a formal paper.

## Conclusions usable by the agent

### T2-T2/T1-T2 multidimensional NMR and exchange
- **When to use**: When a 1D T2 spectrum cannot distinguish coupling/exchange, fluid components or complex pore environments, and it is necessary to explain that 2D NMR provides stronger constraints.
- **Physical/mathematical mechanism**: Two-dimensional correlation experiments encode relaxation correlations across different waiting/mixing periods into a 2D spectrum, which can reveal exchange, coupling and links between different fluid or pore environments.
- **Citable sentence for reports**: In complex samples, 1D T2 peaks cannot always be uniquely assigned to physical pore populations, and multidimensional NMR can serve as a check and an additional constraint. [@Tan2012T2T1Simulation]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### CPMG/echo-train sampling effects
- **When to use**: When the agent must explain how raw decay sampling, echo spacing, missing early points, trim-from-peak or the simulated echo train affect the inversion result.
- **Physical/mathematical mechanism**: The CPMG echo train is the input to the inversion; the sampling interval, early-signal quality, pulse errors and noise affect the recoverable T2 range and the spectral stability.
- **Citable sentence for reports**: The quality of a T2 inversion is limited first of all by the echo-train data quality and the time-sampling window. [@Tan2012T2T1Simulation]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Random-walk/Monte Carlo forward simulation
- **When to use**: When the agent must explain why a random walk can simulate NMR decay, validate inversion results, or compare pore structure with the inverted T2 spectrum.
- **Physical/mathematical mechanism**: A random walk discretizes molecular diffusion into many particle trajectories and accumulates phase and decay through surface relaxation at the boundary, bulk relaxation and field inhomogeneity, producing an echo decay that can be inverted.
- **Citable sentence for reports**: Random-walk forward modelling provides a mechanistic bridge from pore geometry and physical parameters to the decay curve and T2 spectrum. [@Tan2012T2T1Simulation]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

## Retrieval keywords

`cpmg`, `echo_spacing`, `echo_train`, `exchange`, `forward_simulation`, `monte_carlo`, `multidimensional_nmr`, `numerical_methods_fem_lbm_matrix`, `pore_scale`, `pulse_sequence`, `random_walk`, `sampling`, `t1_t2`, `t2_t2`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and retrieval tags; check the original publication for verbatim wording or page numbers.
- Main evidence topics: T2-T2/T1-T2 multidimensional NMR and exchange; CPMG/echo-train sampling effects; random-walk/Monte Carlo forward simulation.

## Usage limits

- Do not treat this reference as the sole basis for interpreting every sample; a report should also account for the user's data quality, T2 range, regularization, simulated geometry and parameter settings.
- When the same phenomenon can arise from several mechanisms, prefer hedged wording ("may", "suggests", "supports") over absolute statements.