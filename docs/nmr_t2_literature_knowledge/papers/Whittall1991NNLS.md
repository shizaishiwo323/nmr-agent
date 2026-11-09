---
citation_key: Whittall1991NNLS
category: 01_core_theory_inversion
tags: [component_assignment, core_theory_inversion, cpmg, echo_spacing, echo_train, gaussian_decomposition, ill_posed, inverse_laplace, nnls, overfitting, peak_count, pulse_sequence, regularization, regularized_inversion, sampling]
pages: 14
---

# Whittall1991NNLS

- **Suggested citation format**: `[@Whittall1991NNLS]`
- **Rationale for inclusion**: Key background on inversion of multi-exponential decay/CPMG data and non-negative least-squares-type methods; supports the explanation that the inversion is ill-posed and needs constraints/regularization.
- **Role in the T2 agent**: Citation for inversion methods: NNLS, non-ideal CPMG data, and the limits of interpreting components of an inverted spectrum.

## Conclusions usable by the agent

### Ill-posedness of the inversion and regularization
- **When to use**: When the inverted T2 spectrum shows noise oscillations or spurious peaks, when changing the regularization factor clearly changes the number or width of peaks, or when the need for NNLS/smoothness constraints must be explained.
- **Physical/mathematical mechanism**: Recovering a T2 distribution from a CPMG decay is a multi-exponential, inverse-Laplace-type problem in which noise and the sampling range are amplified; non-negativity and smoothness regularization trade off the fit residual against spectral smoothness.
- **Citable sentence for reports**: The T2 spectrum is not a unique direct reading of the decay curve but an inversion result shaped by noise, the sampling window and regularization constraints. [@Whittall1991NNLS]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### Limits on peak/component interpretation (not a source for the Gaussian method)
- **When to use**: When the user asks to split a T2 spectrum into 2-3 peaks and interpret peak areas and positions, or when a change in the number of peaks changes the interpretation.
- **Physical/mathematical mechanism**: Gaussian peak decomposition is an empirical approximation of the spectral shape on the log T2 axis; Whittall, Coates and related papers mainly support the point that inverted spectra and component interpretations need care, and they should not be cited as the source of the Gaussian method.
- **Citable sentence for reports**: A peak decomposition should serve as an interpretive aid, not as the sole proof that the sample contains exactly that many physical pore populations. [@Whittall1991NNLS]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

### CPMG/echo-train sampling effects
- **When to use**: When the agent must explain how raw decay sampling, echo spacing, missing early points, trim-from-peak or the simulated echo train affect the inversion result.
- **Physical/mathematical mechanism**: The CPMG echo train is the input to the inversion; the sampling interval, early-signal quality, pulse errors and noise affect the recoverable T2 range and the spectral stability.
- **Citable sentence for reports**: The quality of a T2 inversion is limited first of all by the echo-train data quality and the time-sampling window. [@Whittall1991NNLS]
- **Evidence location**: See the evidence anchors below. Where no page anchor is given, the card is classified from the title, rationale for inclusion and text keywords. Check against the original publication before citing.

## Retrieval keywords

`component_assignment`, `core_theory_inversion`, `cpmg`, `echo_spacing`, `echo_train`, `gaussian_decomposition`, `ill_posed`, `inverse_laplace`, `nnls`, `overfitting`, `peak_count`, `pulse_sequence`, `regularization`, `regularized_inversion`, `sampling`

## Evidence anchors

- p.1: The paper discusses how to obtain robust information from complex relaxation spectra when the data are non-ideal.
- p.3: The text explicitly uses nonnegative least-squares (NNLS) to compute relaxation spectra.
- p.2: The text discusses baseline offsets, non-ideal 180-degree pulses and RF ringdown in CPMG sequences.
- Main evidence topics: ill-posedness of the inversion and regularization; limits on peak/component interpretation (not a source for the Gaussian method); CPMG/echo-train sampling effects.

## Usage limits

- Do not treat this reference as the sole basis for interpreting every sample; a report should also account for the user's data quality, T2 range, regularization, simulated geometry and parameter settings.
- When the same phenomenon can arise from several mechanisms, prefer hedged wording ("may", "suggests", "supports") over absolute statements.