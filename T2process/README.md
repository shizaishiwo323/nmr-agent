# nmr_t2 standard package

This directory has been standardized as a Python package for NMR T2 processing.

## Features

- **NNLS inversion** with MATLAB-compatible core behavior
- **L-curve regularization selection** with reciprocal-slope criterion
- **Paired plotting** for raw decay and T2 spectrum
- **Gaussian peak decomposition** for spectrum interpretation

## Package structure

- `nmr_t2/config.py`: typed configuration objects
- `nmr_t2/io_utils.py`: robust Excel parsing and standardized exports
- `nmr_t2/nnls.py`: fixed-regularization inversion
- `nmr_t2/lcurve.py`: L-curve inversion
- `nmr_t2/plotting.py`: figure generation
- `nmr_t2/gaussian.py`: Gaussian decomposition
- `nmr_t2/pipelines.py`: high-level workflows

## Standard output naming

All high-level pipelines export files under this convention:

`<dataset_name>__<artifact_name>.<ext>`

Examples:

- `SimulationDecay__nnls_spectrum.xlsx`
- `SimulationDecay__nnls_fit.xlsx`
- `SimulationDecay__nnls_summary.csv`
- `SimulationDecay__lcurve_metrics.xlsx`
- `SimulationDecay__lcurve_fit.xlsx`
- `SimulationDecay__gaussian_summary.xlsx`

The NNLS and L-curve fit workbooks place the inversion-sampled decay,
fitted amplitude, and residual noise in adjacent columns. The
`noise_amplitude` column is the signed pointwise residual
`decay_amplitude - fit_amplitude`; `residual` is retained as a compatibility
alias.

## Backward compatibility

The legacy modules are preserved as compatibility layers:

- `inversion_functions.py`
- `gaussian_decomposition_functions.py`
- `run_nnls.py`
- `run_nnls_lcurve.py`
- `plot_nmr_t2.py`

They now delegate to the standardized package implementation.

## Quick start

You can run the complete workflow demo from `main.ipynb`.
