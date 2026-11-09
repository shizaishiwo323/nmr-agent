"""Top-level package for standardized NMR T2 inversion workflows.

The public API stays small and stable, but heavy numerical/plotting modules
are loaded lazily so web apps can start even when optional science packages
are unavailable in a constrained deployment environment.
"""

from importlib import import_module

from .config import GaussianConfig, LCurveConfig, NnlsConfig, PlotConfig
from .models import GaussianDecompositionResult, LCurveInversionResult, NnlsInversionResult, TrimmedSignal

__all__ = [
    "GaussianConfig",
    "LCurveConfig",
    "NnlsConfig",
    "PlotConfig",
    "TrimmedSignal",
    "NnlsInversionResult",
    "LCurveInversionResult",
    "GaussianDecompositionResult",
    "invert_single_signal_nnls",
    "invert_single_signal_lcurve",
    "decompose_spectrum_as_gaussians",
    "run_nnls_workbook",
    "run_lcurve_workbook",
    "run_plotting_workbook_pair",
    "run_gaussian_decomposition_on_spectrum_workbook",
]


def __getattr__(name):
    if name == "invert_single_signal_nnls":
        return import_module(".nnls", __name__).invert_single_signal_nnls
    if name == "invert_single_signal_lcurve":
        return import_module(".lcurve", __name__).invert_single_signal_lcurve
    if name == "decompose_spectrum_as_gaussians":
        return import_module(".gaussian", __name__).decompose_spectrum_as_gaussians
    if name in {
        "run_nnls_workbook",
        "run_lcurve_workbook",
        "run_plotting_workbook_pair",
        "run_gaussian_decomposition_on_spectrum_workbook",
    }:
        return getattr(import_module(".pipelines", __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
