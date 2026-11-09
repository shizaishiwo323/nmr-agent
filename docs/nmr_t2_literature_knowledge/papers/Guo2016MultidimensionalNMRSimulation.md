---
citation_key: Guo2016MultidimensionalNMRSimulation
category: 02_pore_scale_simulation_random_walk
tags: [cpmg, echo_spacing, echo_train, eigenmodes, exchange, forward_simulation, geometry, monte_carlo, multidimensional_nmr, pore_scale, pore_scale_simulation_random_walk, pore_shape, pulse_sequence, random_walk, restricted_diffusion, sampling, t1_t2, t2_t2]
pages: 10
---

# Guo2016MultidimensionalNMRSimulation

- **Suggested citation format**: `[@Guo2016MultidimensionalNMRSimulation]`
- **Reason for inclusion**: Numerical simulation of multidimensional NMR responses; usable as background for T2/T1-T2/T2-T2 simulation.
- **Role in the T2 agent**: Pore-scale random-walk/Monte Carlo forward-simulation reference; suited to explaining the mechanism chain from simulation to decay curve/T2 spectrum.
- **Extraction note**: Check page numbers against the original publication before citing.

## Conclusions usable by the agent

### Random-walk/Monte Carlo forward simulation
- **When to invoke**: When it is necessary to explain why a random walk can simulate NMR decay, to validate inversion results, or to compare the pore structure with the inverted T2 spectrum.
- **Physical/mathematical mechanism**: A random walk discretizes molecular diffusion into many particle trajectories and accumulates phase/decay under boundary (surface) relaxation, bulk relaxation and field inhomogeneity, producing an echo decay that can be inverted.
- **Citable sentence for reports**: Random-walk forward simulation provides a mechanistic bridge from pore geometry and physical parameters to the decay curve/T2 spectrum. [@Guo2016MultidimensionalNMRSimulation]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### T2-T2/T1-T2 multidimensional NMR and exchange
- **When to invoke**: When a 1D T2 spectrum cannot distinguish coupling/exchange, fluid components or complex pore environments, and it must be stated that 2D NMR can provide stronger constraints.
- **Physical/mathematical mechanism**: Two-dimensional correlation experiments encode relaxation correlations across different waiting/mixing periods into a 2D spectrum, which can reveal exchange, coupling and links between different fluid/pore environments.
- **Citable sentence for reports**: In complex samples, 1D T2 peaks cannot always be assigned uniquely to physical pore populations; multidimensional NMR can serve as validation and an additional constraint. [@Guo2016MultidimensionalNMRSimulation]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### CPMG/echo-train sampling effects
- **When to invoke**: When it is necessary to explain the effect on the inversion of raw-decay sampling, echo spacing, missing early points, trim-from-peak, or the simulated echo train.
- **Physical/mathematical mechanism**: The CPMG echo train is the input to the inversion; the sampling interval, early-signal quality, pulse errors and noise affect the recoverable T2 range and the stability of the spectrum.
- **Citable sentence for reports**: The quality of a T2 inversion is limited first of all by the quality of the echo-train data and by the time-sampling window. [@Guo2016MultidimensionalNMRSimulation]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to invoke**: When a change of geometry shifts or broadens the T2 peak, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal decay problem controlled by the boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information resulting from diffusion within the pore domain combined with boundary relaxation, not just the geometric pore size itself. [@Guo2016MultidimensionalNMRSimulation]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

## Search keywords

`cpmg`, `echo_spacing`, `echo_train`, `eigenmodes`, `exchange`, `forward_simulation`, `geometry`, `monte_carlo`, `multidimensional_nmr`, `pore_scale`, `pore_scale_simulation_random_walk`, `pore_shape`, `pulse_sequence`, `random_walk`, `restricted_diffusion`, `sampling`, `t1_t2`, `t2_t2`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and search tags; consult the original publication for exact wording or page numbers.
- Main evidence topics: random-walk/Monte Carlo forward simulation; T2-T2/T1-T2 multidimensional NMR and exchange; CPMG/echo-train sampling effects; restricted diffusion, geometry and eigenmodes.

## Limits of use

- Do not treat this reference as the sole basis for interpreting every sample; reports should take into account the user's data quality, T2 range, regularization, simulation geometry and parameter settings.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.