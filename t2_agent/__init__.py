"""Streamlit-ready T2 inversion agent package."""

from .guidance import build_parameter_guidance, infer_requested_plan
from .tools import (
    generate_report,
    inspect_workbook_schema,
    interpret_results,
    repair_workbook,
    run_fixed_nnls,
    run_gaussian_peaks,
    run_lcurve,
    validate_workbook,
)

__all__ = [
    "build_parameter_guidance",
    "generate_report",
    "infer_requested_plan",
    "inspect_workbook_schema",
    "interpret_results",
    "repair_workbook",
    "run_fixed_nnls",
    "run_gaussian_peaks",
    "run_lcurve",
    "validate_workbook",
]
