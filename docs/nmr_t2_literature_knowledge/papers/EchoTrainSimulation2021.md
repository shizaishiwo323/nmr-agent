---
citation_key: EchoTrainSimulation2021
category: 03_numerical_methods_fem_lbm_matrix
tags: [cpmg, echo_spacing, echo_train, numerical_methods_fem_lbm_matrix, pulse_sequence, sampling]
pages: 11
---

# EchoTrainSimulation2021

- **Title**: Numerical investigating the low field NMR response of representative pores at different pulse sequence parameters
- **Suggested citation format**: `[@EchoTrainSimulation2021]`
- **Reason for inclusion**: Background on numerical simulation of the echo-train/CPMG response; useful for decay-curve generation and pre-inversion processing.
- **Role in the T2 agent**: Sampling and pulse-sequence reference: effects of the CPMG echo train, pulse sequence and numerical echo-train simulation; not a primary reference for L-curve/regularization theory.

## Conclusions usable by the agent

### CPMG/echo-train sampling effects
- **When to invoke**: When it is necessary to explain the effect on the inversion of raw-decay sampling, echo spacing, missing early points, trim-from-peak, or the simulated echo train.
- **Physical/mathematical mechanism**: The CPMG echo train is the input to the inversion; the sampling interval, early-signal quality, pulse errors and noise affect the recoverable T2 range and the stability of the spectrum.
- **Citable sentence for reports**: The quality of a T2 inversion is limited first of all by the quality of the echo-train data and by the time-sampling window. [@EchoTrainSimulation2021]
- **Evidence location**: See the evidence anchors below; where no page anchor is given, the topic is assigned from the title, the reason for inclusion and keywords. Check against the original publication before citing.

## Search keywords

`cpmg`, `echo_spacing`, `echo_train`, `numerical_methods_fem_lbm_matrix`, `pulse_sequence`, `sampling`

## Evidence anchors

- p.1: The abstract keywords include low-field NMR response, Bloch equation, CPMG pulse sequence and magnetization evolution.
- p.1: States that the NMR response of porous media is simulated numerically from the CPMG pulse sequence and the Bloch equation.
- p.1: Notes that pulse imperfections in the CPMG echo train can introduce artifacts.
- Main evidence topics: CPMG/echo-train sampling effects.

## Limits of use

- Do not treat this reference as the sole basis for interpreting every sample; reports should take into account the user's data quality, T2 range, regularization, simulation geometry and parameter settings.
- When the same phenomenon can be caused by several mechanisms, prefer wording such as "may", "suggests" or "supports" over absolute statements.