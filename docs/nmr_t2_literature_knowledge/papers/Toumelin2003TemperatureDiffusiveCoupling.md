---
citation_key: Toumelin2003TemperatureDiffusiveCoupling
category: 02_pore_scale_simulation_random_walk
tags: [cpmg, diffusive_coupling, echo_spacing, echo_train, exchange, peak_merging, pore_coupling, pore_scale_simulation_random_walk, pore_size, pulse_sequence, sampling, short_t2, surface_relaxation, surface_relaxivity]
pages: 17
---

# Toumelin2003TemperatureDiffusiveCoupling

- **Suggested citation format**: `[@Toumelin2003TemperatureDiffusiveCoupling]`
- **Rationale for inclusion**: Effect of temperature and diffusive coupling on the NMR response; useful for explaining peak broadening and peak shifts.
- **Role in the T2 agent**: Citation for pore-scale random-walk/Monte Carlo forward modelling; useful for explaining the mechanism chain from simulation to decay curve and T2 spectrum.
- **Extraction note**: Parsing warnings were raised during text extraction; check page numbers against the original publication before using this in a formal paper.

## Conclusions usable by the agent

### Diffusive coupling and inter-pore exchange
- **When to use**: When several expected pore populations merge into one broad peak in the inversion, the peak position falls between geometric predictions, the connected-pore model is smoother than the isolated-pore model, or 1D T2 cannot separate pore populations.
- **Physical/mathematical mechanism**: Spins that diffuse between pores of different sizes average over several local relaxation environments; when coupling is strong, the T2 distribution no longer equals the independent responses of the individual pore-size groups.
- **Citable sentence for reports**: Peak merging or spectral broadening does not necessarily mean that only one pore population exists; it can also result from inter-pore diffusive coupling that mixes several relaxation environments. [@Toumelin2003TemperatureDiffusiveCoupling]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Surface relaxation, pore size and short T2
- **When to use**: When the short-T2 area is large, the main peak shifts toward short T2, small-pore or high-surface-area models decay faster, or the relation between T2 and pore size needs explaining.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-area-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-area-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@Toumelin2003TemperatureDiffusiveCoupling]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### CPMG/echo-train sampling effects
- **When to use**: When the agent must explain how raw decay sampling, echo spacing, missing early points, trim-from-peak or the simulated echo train affect the inversion result.
- **Physical/mathematical mechanism**: The CPMG echo train is the input to the inversion; the sampling interval, early-signal quality, pulse errors and noise affect the recoverable T2 range and the spectral stability.
- **Citable sentence for reports**: The quality of a T2 inversion is limited first of all by the echo-train data quality and the time-sampling window. [@Toumelin2003TemperatureDiffusiveCoupling]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

## Retrieval keywords

`cpmg`, `diffusive_coupling`, `echo_spacing`, `echo_train`, `exchange`, `peak_merging`, `pore_coupling`, `pore_scale_simulation_random_walk`, `pore_size`, `pulse_sequence`, `sampling`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- This card keeps only mechanism-level paraphrases and retrieval tags; check the original publication for verbatim wording or page numbers.
- Main evidence topics: diffusive coupling and inter-pore exchange; surface relaxation, pore size and short T2; CPMG/echo-train sampling effects.

## Usage limits

- Do not treat this reference as the sole basis for interpreting every sample; a report should also account for the user's data quality, T2 range, regularization, simulated geometry and parameter settings.
- When the same phenomenon can arise from several mechanisms, prefer hedged wording ("may", "suggests", "supports") over absolute statements.