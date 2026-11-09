---
citation_key: Coates1999NMRLogging
category: 01_core_theory_inversion
tags: [component_assignment, core_theory_inversion, cpmg, echo_spacing, echo_train, gaussian_decomposition, ill_posed, inverse_laplace, nnls, overfitting, peak_count, pore_size, pulse_sequence, regularization, regularized_inversion, sampling, short_t2, surface_relaxation, surface_relaxivity]
pages: 253
---

# Coates1999NMRLogging

- **Title**: NMR Logging Principles and Applications
- **Suggested citation format**: `[@Coates1999NMRLogging]`
- **Reason for inclusion**: Classic background book on NMR petrophysics, suitable for looking up basic concepts, T2-distribution interpretation and application context.
- **Role in the T2 agent**: NMR logging/inversion background reference: textbook-level source for T2 distributions, regularization, CPMG and pore-fluid interpretation.

## Conclusions usable by the agent

### Surface relaxation, pore size and short T2
- **When to invoke**: When the short-T2 area is large, when the main peak shifts to shorter T2, when small-pore/high-surface-area models decay faster, or when the relation between T2 and pore size needs to be explained.
- **Physical/mathematical mechanism**: Effective transverse relaxation is usually controlled jointly by bulk relaxation, surface relaxation and diffusion-related terms; under the fast-diffusion approximation, small pores or pores with a high surface-to-volume ratio show shorter T2.
- **Citable sentence for reports**: A short-T2 component generally supports an interpretation of stronger surface relaxation, smaller pores or a higher surface-to-volume ratio, but this must be judged together with the surface relaxivity and the diffusion regime. [@Coates1999NMRLogging]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Ill-posedness and regularization of the inversion
- **When to invoke**: When the inverted T2 spectrum shows noise oscillations or spurious peaks, when changing the regularization factor markedly alters the number or width of peaks, or when it is necessary to explain why NNLS/smoothness constraints are needed.
- **Physical/mathematical mechanism**: Going from a CPMG decay to a T2 distribution is a multi-exponential/inverse-Laplace-type inverse problem in which noise and the sampling range are amplified; non-negativity constraints and smoothness regularization trade off the fit residual against spectral smoothness.
- **Citable sentence for reports**: A T2 spectrum is not a unique direct readout of the decay curve but an inversion result shaped by noise, the sampling window and the regularization constraints. [@Coates1999NMRLogging]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### CPMG/echo-train sampling effects
- **When to invoke**: When it is necessary to explain the effect on the inversion of raw-decay sampling, echo spacing, missing early points, trim-from-peak, or the simulated echo train.
- **Physical/mathematical mechanism**: The CPMG echo train is the input to the inversion; the sampling interval, early-signal quality, pulse errors and noise affect the recoverable T2 range and the stability of the spectrum.
- **Citable sentence for reports**: The quality of a T2 inversion is limited first of all by the quality of the echo-train data and by the time-sampling window. [@Coates1999NMRLogging]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

### Limits on peak/component interpretation (not a source for the Gaussian method)
- **When to invoke**: When the user asks to split a T2 spectrum into 2-3 peaks and interpret peak areas and positions, or when a change in the number of peaks changes the interpretation.
- **Physical/mathematical mechanism**: Gaussian peak splitting is an empirical approximation of the spectral shape on the log T2 axis; Whittall, Coates and similar works mainly support the point that inverted spectra and component interpretation require caution, and they should not be cited as the source of the Gaussian method.
- **Citable sentence for reports**: Peak-splitting results should serve as an interpretive aid and not as the sole evidence that the sample contains exactly the same number of physical pore populations. [@Coates1999NMRLogging]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

## Search keywords

`component_assignment`, `core_theory_inversion`, `cpmg`, `echo_spacing`, `echo_train`, `gaussian_decomposition`, `ill_posed`, `inverse_laplace`, `nnls`, `overfitting`, `peak_count`, `pore_size`, `pulse_sequence`, `regularization`, `regularized_inversion`, `sampling`, `short_t2`, `surface_relaxation`, `surface_relaxivity`

## Evidence anchors

- p.72: States that multi-exponential fitting is unstable, so the inversion needs regularization to stabilize the solution.
- p.51: Lists CPMG pulse sequences as a basic concept for T2 measurement.
- p.5: The table of contents includes chapters on the NMR T2 distribution, porosity and pore size.
- Main evidence topics: surface relaxation, pore size and short T2; ill-posedness and regularization of the inversion; CPMG/echo-train sampling effects; limits on peak/component interpretation (not a source for the Gaussian method).

## Limits of use

- Do not treat this reference as the sole basis for interpreting every sample; reports should take into account the user's data quality, T2 range, regularization, simulation geometry and parameter settings.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.