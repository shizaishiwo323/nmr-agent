"""AI-facing skill descriptions for the T2 tool package."""

from __future__ import annotations


T2_AGENT_SKILLS = [
    {
        "name": "inspect_workbook_schema",
        "purpose": "Read workbook shape, preview rows, column labels, numeric profiles, and monotonicity before choosing any processing path.",
        "when_to_use": "Always use first after upload, especially when user data may have swapped columns, headers, blank rows, multiple signal columns, or nonstandard layout.",
    },
    {
        "name": "validate_workbook",
        "purpose": "Infer time/T2 column, signal columns, data kind, time unit scale, and layout warnings.",
        "when_to_use": "Use after schema inspection to decide whether the uploaded data can be normalized for inversion or spectrum decomposition.",
    },
    {
        "name": "repair_workbook",
        "purpose": "Normalize detected layout into time_ms plus signal columns without changing the original file.",
        "when_to_use": "Use after validation succeeds and data_kind is decay, before any T2 inversion tool. Do not use for an existing T2 spectrum.",
    },
    {
        "name": "run_lcurve",
        "purpose": "Run L-curve T2 inversion and automatically select the smoothing/regularization factor.",
        "when_to_use": "Default for decay data when users do not know which smoothing factor to choose. Do not use when validate_workbook says data_kind is spectrum.",
    },
    {
        "name": "run_fixed_nnls",
        "purpose": "Run fixed-regularization NNLS inversion.",
        "when_to_use": "Use only for decay data when the user explicitly specifies a smoothing/regularization factor. Do not use for existing T2 spectra.",
    },
    {
        "name": "run_gaussian_peaks",
        "purpose": "Decompose a T2 spectrum into Gaussian peaks.",
        "when_to_use": "Use after inversion produces a spectrum, or directly after validate_workbook identifies an uploaded workbook as a T2 spectrum and the user wants peak interpretation.",
    },
    {
        "name": "generate_report",
        "purpose": "Write a Markdown report from data diagnostics, parameters, tool outputs, figures, and caveats in the requested user-facing language.",
        "when_to_use": "Use at the end of an analysis workflow.",
    },
    {
        "name": "process_uploaded_files_batch",
        "purpose": "Run the complete T2 workflow for every uploaded workbook and keep each file's outputs in a separate folder.",
        "when_to_use": "Use when multiple files are uploaded and the user asks to process all files or run batch analysis in one conversation.",
    },
    {
        "name": "interpret_results",
        "purpose": "Read generated summaries/spectra/peak tables and explain what the result means for the sample, with literature findings and AGU citations (soil water-state classes, two water populations, coupling and capacity checks, S/V check for CT).",
        "when_to_use": "Use when the user asks what the result means, whether the result is good, how to interpret peaks, or what to do next.",
    },
]


def render_skill_prompt() -> str:
    """Render skills into compact instructions for the LLM system prompt."""

    lines = ["Available T2 skills/tools:"]
    for skill in T2_AGENT_SKILLS:
        lines.append(f"- {skill['name']}: {skill['purpose']} Use when: {skill['when_to_use']}")
    return "\n".join(lines)
