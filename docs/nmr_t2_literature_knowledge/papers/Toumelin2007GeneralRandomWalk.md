---
citation_key: Toumelin2007GeneralRandomWalk
category: 02_pore_scale_simulation_random_walk
tags: [cpmg, dephasing, echo_spacing, echo_train, eigenmodes, field_inhomogeneity, forward_simulation, geometry, internal_gradient, monte_carlo, pore_scale, pore_scale_simulation_random_walk, pore_shape, pore_size, pulse_sequence, random_walk, restricted_diffusion, sampling, short_t2, surface_relaxation, surface_relaxivity]
pages: 14
---

# Toumelin2007GeneralRandomWalk

- **Suggested citation format**: `[@Toumelin2007GeneralRandomWalk]`
- **Rationale for inclusion**: Random-walk pore-scale NMR forward-simulation method; directly supports the interpretation of simulated decays and T2 distributions.
- **Role in the T2 agent**: Citation for pore-scale random-walk/Monte Carlo forward modelling; useful for explaining the mechanism chain from simulation to decay curve and T2 spectrum.

## Conclusions usable by the agent

### Random-walk/Monte Carlo forward simulation
- **When to use**: When the agent must explain why a random walk can simulate NMR decay, validate inversion results, or compare pore structure with the inverted T2 spectrum.
- **Physical/mathematical mechanism**: A random walk discretizes molecular diffusion into many particle trajectories and accumulates phase and decay through surface relaxation at the boundary, bulk relaxation and field inhomogeneity, producing an echo decay that can be inverted.
- **Citable sentence for reports**: Random-walk forward modelling provides a mechanistic bridge from pore geometry and physical parameters to the decay curve and T2 spectrum. [@Toumelin2007GeneralRandomWalk]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Surface relaxation, pore size and short T2
- **When to use**: When the short-T2 area is large, the main peak shifts toward short T2, small-pore or high-surface-area models decay faster, or the relation between T2 and pore size needs explaining.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-area-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-area-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@Toumelin2007GeneralRandomWalk]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Restricted diffusion, geometry and eigenmodes
- **When to use**: When a geometry change shifts or broadens T2 peaks, or when results for circular, triangular or complex connected pores cannot be explained by a single pore size.
- **Physical/mathematical mechanism**: Diffusion-relaxation in a finite pore domain can be treated as a modal-decay problem governed by boundary conditions; pore shape, connectivity and boundary surface relaxation change the eigenmodes and the effective relaxation times.
- **Citable sentence for reports**: The T2 response carries effective modal information produced by the combined action of pore-domain diffusion and boundary relaxation, not just the geometric pore size. [@Toumelin2007GeneralRandomWalk]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Internal gradients and field inhomogeneity
- **When to use**: When the simulated decay is faster than a pure surface-relaxation model, the long-T2 end is suppressed, changing the echo spacing alters the spectral shape, or susceptibility contrast causes additional decay.
- **Physical/mathematical mechanism**: Internal magnetic-field gradients coupled with diffusion cause additional dephasing; this term depends on the diffusion coefficient, gradient strength, echo spacing and pore scale.
- **Citable sentence for reports**: A shortened T2 does not necessarily come only from small pores or high surface relaxivity; it may also come from diffusion dephasing induced by internal gradients. [@Toumelin2007GeneralRandomWalk]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### CPMG/echo-train sampling effects
- **When to use**: When the agent must explain how raw decay sampling, echo spacing, missing early points, trim-from-peak or the simulated echo train affect the inversion result.
- **Physical/mathematical mechanism**: The CPMG echo train is the input to the inversion; the sampling interval, early-signal quality, pulse errors and noise affect the recoverable T2 range and the spectral stability.
- **Citable sentence for reports**: The quality of a T2 inversion is limited first of all by the echo-train data quality and the time-sampling window. [@Toumelin2007GeneralRandomWalk]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

## Retrieval keywords

`cpmg`, `dephasing`, `echo_spacing`, `echo_train`, `eigenmodes`, `field_inhomogeneity`, `forward_simulation`, `geometry`, `internal_gradient`, `monte_carlo`, `pore_scale`, `pore_scale_simulation_random_walk`, `pore_shape`, `pore_size`, `pulse_sequence`, `random_walk`, `restricted_diffusion`, `sampling`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and retrieval tags; check the original publication for verbatim wording or page numbers.
- Main evidence topics: random-walk/Monte Carlo forward simulation; surface relaxation, pore size and short T2; restricted diffusion, geometry and eigenmodes; internal gradients and field inhomogeneity; CPMG/echo-train sampling effects.

## Usage limits

- Do not treat this reference as the sole basis for interpreting every sample; a report should also account for the user's data quality, T2 range, regularization, simulated geometry and parameter settings.
- When the same phenomenon can arise from several mechanisms, prefer hedged wording ("may", "suggests", "supports") over absolute statements.