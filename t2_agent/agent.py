"""DeepSeek function-calling agent loop for T2 workflows."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from .deepseek import DEEPSEEK_BASE_URL
from .guidance import build_parameter_guidance, infer_requested_plan
from .models import AgentToolResult
from .skills import render_skill_prompt
from .ct_workflow import inspect_ct_phase_image, is_ct_upload, request_ct_run
from .ideal_workflow import request_ideal_run
from .tools import (
    generate_report,
    inspect_2d_geometry_input,
    inspect_workbook_schema,
    interpret_results,
    plot_decay_spectrum,
    repair_workbook,
    run_2d_mesh_and_decay,
    run_fixed_nnls,
    run_gaussian_peaks,
    run_local_nmr_triangle_t2_t2,
    run_lcurve,
    run_reduced_t2_t2,
    png_physical_scale_error,
    png_physical_scale_provided,
    timestamped_name,
    validate_workbook,
    write_standard_decay_workbook,
)


@dataclass
class AgentRuntimeContext:
    """Mutable per-session state used by whitelisted tools."""

    workspace: Path
    uploaded_path: Path | None = None
    uploaded_paths: list[Path] = field(default_factory=list)
    validation: AgentToolResult | None = None
    repaired_path: Path | None = None
    simulation_decay_path: Path | None = None
    spectrum_path: Path | None = None
    results: list[AgentToolResult] = field(default_factory=list)
    tool_history: list[AgentToolResult] = field(default_factory=list)
    report: AgentToolResult | None = None
    last_user_goal: str = ""
    ct_state: dict[str, Any] = field(default_factory=dict)
    ideal_state: dict[str, Any] = field(default_factory=dict)
    stage_callback: Callable[[AgentToolResult], None] | None = None


@dataclass
class AgentTurnResult:
    """Result of one chat turn, including tools the model chose to run."""

    assistant_message: str
    messages: list[dict[str, Any]]
    tool_results: list[AgentToolResult]
    trace: list[dict[str, Any]] = field(default_factory=list)


def build_tool_specs() -> list[dict[str, Any]]:
    """Return OpenAI-compatible tool schemas for DeepSeek."""

    return [
        {
            "type": "function",
            "function": {
                "name": "inspect_ct_phase_image",
                "description": "Inspect an uploaded segmented CT label image (TIF/TIFF, one integer label per phase such as 0/102/153/255). Counts pixel values, decides whether the background question is needed, makes the AI first guess of solid/water/air/background, and opens the user's draggable phase-marker preview. Call this first for any TIF upload that should be simulated.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "has_background": {"type": "boolean", "description": "Only pass when the user explicitly stated whether the image contains background (outside-the-sample) pixels, in this or an earlier message. Never guess."},
                        "phase_labels": {
                            "type": "object",
                            "description": "Only when the user explicitly stated label values, e.g. {\"solid\": 255, \"water\": 102, \"air\": 153, \"background\": 0}.",
                            "properties": {
                                "solid": {"type": "integer"},
                                "water": {"type": "integer"},
                                "air": {"type": "integer"},
                                "background": {"type": "integer"},
                            },
                            "additionalProperties": False,
                        },
                        "pixel_size_um": {"type": "number", "description": "CT resolution in micrometers per pixel, only if the user stated it."},
                        "run_lcurve": {"type": "boolean", "description": "Only if the user stated whether to use L-curve."},
                        "regularization": {"type": "number", "description": "Fixed smoothing factor, only if the user stated one."},
                        "run_gaussian": {"type": "boolean", "description": "Only if the user stated whether to run Gaussian peak decomposition."},
                        "peak_count": {"type": "integer", "minimum": 1, "maximum": 8},
                        "diffusion_um2_per_ms": {"type": "number"},
                        "bulk_t2_ms": {"type": "number"},
                        "rho_solid_um_per_ms": {"type": "number"},
                        "rho_gas_um_per_ms": {"type": "number"},
                        "defaults_accepted": {"type": "boolean", "description": "True only when the user said the remaining parameters may use defaults."},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_ct_simulation_workflow",
                "description": "Run the segmented-CT workflow after the user confirmed the phase markers: phase-mapped geometry and crop, pyGIMLi triangular mesh, NMR decay solve, T2 inversion (L-curve or fixed smoothing factor), optional Gaussian decomposition, and interpretation. Returns needs_confirmation while the background answer, phase confirmation, or parameter dialog is still pending.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pixel_size_um": {"type": "number"},
                        "run_lcurve": {"type": "boolean"},
                        "regularization": {"type": "number"},
                        "run_gaussian": {"type": "boolean"},
                        "peak_count": {"type": "integer", "minimum": 1, "maximum": 8},
                        "diffusion_um2_per_ms": {"type": "number"},
                        "bulk_t2_ms": {"type": "number"},
                        "rho_solid_um_per_ms": {"type": "number"},
                        "rho_gas_um_per_ms": {"type": "number"},
                        "t_max_ms": {"type": "number"},
                        "dt_ms": {"type": "number"},
                        "lcurve_criterion": {"type": "string", "enum": ["ratio", "curvature"], "description": "L-curve selection rule; see run_lcurve."},
                        "relaxing_edges": {"type": "boolean", "description": "Background and image-edge faces relax with rho_solid (default true); false makes them no-flux."},
                        "defaults_accepted": {"type": "boolean"},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "inspect_workbook_schema",
                "description": "Read the uploaded spreadsheet/table structure (Excel, CSV, or text), preview rows, column labels, numeric ranges, and monotonicity so the agent can reason about nonstandard layouts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "preview_rows": {"type": "integer", "description": "Number of preview rows. Default: 8."}
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "validate_workbook",
                "description": "Validate the uploaded spreadsheet/table format (Excel, CSV, or text) and decide whether it can be used for T2 inversion or peak decomposition.",
                "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "repair_workbook",
                "description": "Normalize the uploaded spreadsheet/table into the standard time_ms + signal columns Excel format.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_to_ms_scale": {
                            "type": "number",
                            "description": "Multiplier that converts raw time to ms. Use 1000 for seconds and 1 when the data is already in ms.",
                        }
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "inspect_2d_geometry_input",
                "description": "Inspect a 2D NMR simulation geometry input. Use this for red/yellow/white PNG phase maps or rule-based 2D geometry before meshing.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "geometry_mode": {"type": "string", "enum": ["png", "rule"], "description": "Use png only for uploaded red/yellow/white phase maps. Use rule for the upstream ideal triangular-pore simulation input."},
                        "normalize_phase_colors": {"type": "boolean", "description": "For PNG phase maps, map near-red, near-yellow, and near-white antialiasing pixels to exact supported phase colors before cropping and meshing."},
                        "coupled": {"type": "boolean", "description": "For ideal triangle input, whether the large and small triangular pores are connected by a throat."},
                        "large_side_um": {"type": "number", "description": "Large ideal triangle side length in micrometers. Default: 20."},
                        "small_side_um": {"type": "number", "description": "Small ideal triangle side length in micrometers. Default: 8."},
                        "large_depth_um": {"type": "number", "description": "Large triangle out-of-plane depth used for volume weighting. Default: 20."},
                        "small_depth_um": {"type": "number", "description": "Small triangle out-of-plane depth used for volume weighting. Default: 8."},
                        "throat_length_um": {"type": "number", "description": "Coupling throat length in micrometers. Default: 5."},
                        "throat_width_um": {"type": "number", "description": "Coupling throat width in micrometers. Default: 1."},
                        "large_air_area_um2": {"type": "number", "description": "Optional gas/bubble area inside the large triangle. Default: 0 for full water."},
                        "small_air_area_um2": {"type": "number", "description": "Optional gas/bubble area inside the small triangle. Default: 0 for full water."},
                        "ideal_mesh_area_um2": {"type": "number", "description": "pyGIMLi target triangle area for ideal triangle mesh. Default: 0.05."},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_2d_mesh_and_decay",
                "description": "Run first-version 2D NMR simulation through pyGIMLi triangular meshing and T2 decay solving. Produces mesh, quality, decay, and standard decay workbook artifacts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "geometry_mode": {"type": "string", "enum": ["png", "rule"], "description": "Use png only for uploaded red/yellow/white phase maps. Use rule for the upstream ideal triangular-pore simulation input."},
                        "pixel_size_um": {"type": "number", "description": "Pixel size in micrometers when x and y pixel sizes are equal. Default: 1."},
                        "pixel_size_x_um": {"type": "number", "description": "Horizontal pixel size in micrometers."},
                        "pixel_size_y_um": {"type": "number", "description": "Vertical pixel size in micrometers."},
                        "physical_size_x_um": {"type": "number", "description": "Physical width of the cropped PNG sample region in micrometers. Applied after automatic white-border cropping."},
                        "physical_size_y_um": {"type": "number", "description": "Physical height of the cropped PNG sample region in micrometers. Applied after automatic white-border cropping."},
                        "normalize_phase_colors": {"type": "boolean", "description": "For PNG phase maps, map near-red, near-yellow, and near-white antialiasing pixels to exact supported phase colors before cropping and meshing."},
                        "diffusion_um2_per_ms": {"type": "number", "description": "Diffusion coefficient in um^2/ms. Default: 2."},
                        "bulk_t2_ms": {"type": "number", "description": "Bulk T2 in ms. Default: 3000."},
                        "rho_solid_um_per_ms": {"type": "number", "description": "Solid-liquid surface relaxivity in um/ms. Default: 0.005."},
                        "rho_gas_um_per_ms": {"type": "number", "description": "Gas-liquid/outside relaxivity in um/ms. Default: 0."},
                        "dt_ms": {"type": "number", "description": "Simulation time step in ms. Default: 5."},
                        "t_max_ms": {"type": "number", "description": "Maximum simulated time in ms. Default: 1500."},
                        "mesh_bulk_size_um": {"type": "number", "description": "Target interior mesh spacing. Larger is coarser. Default: 8."},
                        "mesh_boundary_size_um": {"type": "number", "description": "Target boundary mesh spacing. Default: 2."},
                        "mesh_max_points": {"type": "integer", "description": "Safety limit for mesh node count. Default: 25000."},
                        "coupled": {"type": "boolean", "description": "For ideal triangle input, whether the large and small triangular pores are connected by a throat."},
                        "large_side_um": {"type": "number", "description": "Large ideal triangle side length in micrometers. Default: 20."},
                        "small_side_um": {"type": "number", "description": "Small ideal triangle side length in micrometers. Default: 8."},
                        "large_depth_um": {"type": "number", "description": "Large triangle out-of-plane depth used for volume weighting. Default: 20."},
                        "small_depth_um": {"type": "number", "description": "Small triangle out-of-plane depth used for volume weighting. Default: 8."},
                        "throat_length_um": {"type": "number", "description": "Coupling throat length in micrometers. Default: 5."},
                        "throat_width_um": {"type": "number", "description": "Coupling throat width in micrometers. Default: 1."},
                        "large_air_area_um2": {"type": "number", "description": "Optional gas/bubble area inside the large triangle. Default: 0 for full water."},
                        "small_air_area_um2": {"type": "number", "description": "Optional gas/bubble area inside the small triangle. Default: 0 for full water."},
                        "ideal_mesh_area_um2": {"type": "number", "description": "pyGIMLi target triangle area for ideal triangle mesh. Default: 0.05."},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_2d_simulation_full_workflow",
                "description": "Run the first-version 2D NMR workflow: geometry input, optional PNG color normalization and white-border crop, pyGIMLi mesh, T2 decay solve, T2 inversion, optional reduced T2-T2 map, and optional Gaussian decomposition. Does not run D-T2. With geometry_mode='rule' (ideal triangle pair) it returns needs_confirmation until the user confirms shape, sizes, coupling, saturation, physics and inversion in the parameter dialog; the confirmed run writes a run-specific folder.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "geometry_mode": {"type": "string", "enum": ["png", "rule"]},
                        "normalize_phase_colors": {"type": "boolean", "description": "For PNG phase maps, map near-red, near-yellow, and near-white antialiasing pixels to exact supported phase colors before cropping and meshing."},
                        "physical_size_x_um": {"type": "number", "description": "Physical width of the cropped PNG sample region in micrometers. Applied after automatic white-border cropping."},
                        "physical_size_y_um": {"type": "number", "description": "Physical height of the cropped PNG sample region in micrometers. Applied after automatic white-border cropping."},
                        "regularization": {"type": "number", "description": "Optional fixed regularization factor. Omit to use L-curve."},
                        "t2_min_ms": {"type": "number"},
                        "t2_max_ms": {"type": "number"},
                        "num_bins": {"type": "integer"},
                        "alpha_min": {"type": "number"},
                        "alpha_max": {"type": "number"},
                        "alpha_count": {"type": "integer"},
                        "run_t2_t2": {"type": "boolean", "description": "Generate a reduced T2-T2 map after the 1D T2 spectrum is available."},
                        "t2_t2_alpha": {"type": "number", "description": "Regularization factor for the reduced T2-T2 NNLS map. Default: 0.05."},
                        "t2_t2_t1_points": {"type": "integer", "description": "Number of synthetic first-encoding time points. Default: 18."},
                        "t2_t2_t2_points": {"type": "integer", "description": "Number of synthetic second-encoding time points. Default: 24."},
                        "t2_t2_bin_points": {"type": "integer", "description": "Number of T2 bins per axis in the reduced T2-T2 map. Default: 28."},
                        "run_gaussian": {"type": "boolean"},
                        "peak_count": {"type": "integer", "minimum": 1, "maximum": 8},
                        "pixel_size_um": {"type": "number"},
                        "pixel_size_x_um": {"type": "number"},
                        "pixel_size_y_um": {"type": "number"},
                        "diffusion_um2_per_ms": {"type": "number"},
                        "bulk_t2_ms": {"type": "number"},
                        "rho_solid_um_per_ms": {"type": "number"},
                        "rho_gas_um_per_ms": {"type": "number"},
                        "dt_ms": {"type": "number"},
                        "t_max_ms": {"type": "number"},
                        "mesh_bulk_size_um": {"type": "number"},
                        "mesh_boundary_size_um": {"type": "number"},
                        "mesh_max_points": {"type": "integer"},
                        "coupled": {"type": "boolean"},
                        "large_side_um": {"type": "number"},
                        "small_side_um": {"type": "number"},
                        "large_depth_um": {"type": "number"},
                        "small_depth_um": {"type": "number"},
                        "throat_length_um": {"type": "number"},
                        "throat_width_um": {"type": "number"},
                        "large_air_area_um2": {"type": "number"},
                        "small_air_area_um2": {"type": "number"},
                        "ideal_mesh_area_um2": {"type": "number"},
                        "large_water_saturation": {"type": "number", "minimum": 0, "maximum": 1, "description": "Ideal structure: water saturation of the large pore (1 = fully water-filled). Only when the user stated it."},
                        "small_water_saturation": {"type": "number", "minimum": 0, "maximum": 1, "description": "Ideal structure: water saturation of the small pore. Only when the user stated it."},
                        "run_lcurve": {"type": "boolean", "description": "Ideal structure: choose the smoothing factor with the L-curve. Only when the user stated it."},
                        "lcurve_criterion": {"type": "string", "enum": ["ratio", "curvature"], "description": "L-curve selection rule; see run_lcurve."},
                        "defaults_accepted": {"type": "boolean", "description": "True only when the user explicitly said default physical parameters are fine."},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_local_nmr_triangle_demo",
                "description": "Run the repository-bundled NMR ideal-triangle demonstration: pyGIMLi triangular mesh and T2 decay, then send the simulated decay into the existing mature fixed NNLS T2 inversion workflow. This does not require any external NMR subproject.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "regularization": {"type": "number", "description": "Fixed smoothing/regularization factor for the existing T2 inversion pipeline. Default: 1.0."},
                        "t2_min_ms": {"type": "number", "description": "Lower bound for the existing T2 inversion search range. Default: 1 ms."},
                        "t2_max_ms": {"type": "number", "description": "Upper bound for the existing T2 inversion search range. Default: 10000 ms."},
                        "num_bins": {"type": "integer", "description": "Number of T2 bins for the existing T2 inversion pipeline. Default: 200."},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_lcurve",
                "description": "Run L-curve T2 inversion on standardized decay data and select the smoothing factor automatically.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "t2_min_ms": {"type": "number", "description": "Lower bound for the T2 search range. Default: 0.01 ms."},
                        "t2_max_ms": {"type": "number", "description": "Upper bound for the T2 search range. Default: 100000 ms."},
                        "num_bins": {"type": "integer", "description": "Number of T2 bins. Default: 200."},
                        "alpha_min": {"type": "number", "description": "Minimum smoothing factor tested by L-curve. Default: 0.001."},
                        "alpha_max": {"type": "number", "description": "Maximum smoothing factor tested by L-curve. Default: 10000."},
                        "alpha_count": {"type": "integer", "description": "Number of smoothing factors tested by L-curve. Default: 300."},
                        "criterion": {
                            "type": "string",
                            "enum": ["ratio", "curvature"],
                            "description": "Selection rule. 'ratio' (default): trimmed, noise-weighted fit with the slope-reciprocal ratio, for measured data. 'curvature': untrimmed normalised fit with maximum L-curve curvature, matching the image-slice reference; use for noise-free simulated decays or when the user asks for it.",
                        },
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_fixed_nnls",
                "description": "Run fixed-regularization NNLS T2 inversion when the user explicitly specifies a smoothing factor.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "regularization": {"type": "number", "description": "Fixed smoothing/regularization factor."},
                        "t2_min_ms": {"type": "number", "description": "Lower bound for the T2 search range. Default: 1 ms."},
                        "t2_max_ms": {"type": "number", "description": "Upper bound for the T2 search range. Default: 10000 ms."},
                        "num_bins": {"type": "integer", "description": "Number of T2 bins. Default: 200."},
                    },
                    "required": ["regularization"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "plot_decay_spectrum",
                "description": "Generate paired decay-curve and T2-spectrum figures.",
                "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_gaussian_peaks",
                "description": "Run Gaussian peak decomposition on the current T2 spectrum.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "peak_count": {"type": "integer", "description": "Number of peaks, for example 2 or 3.", "minimum": 1, "maximum": 8}
                    },
                    "required": ["peak_count"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generate_report",
                "description": "Generate a Markdown report in the requested user-facing language from the current tool results.",
                "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "interpret_results",
                "description": "Read generated summaries, T2 spectra, and Gaussian peak tables, then explain what the results mean.",
                "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "process_uploaded_files_batch",
                "description": "Process every uploaded data file in one batch workflow. For each file, inspect/validate, standardize, run T2 inversion, optionally run Gaussian peaks, interpret results, and generate a report in a separate output folder.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "run_gaussian": {
                            "type": "boolean",
                            "description": "Whether to run Gaussian peak decomposition after inversion. Default: false unless the user asks for peaks.",
                        },
                        "peak_count": {"type": "integer", "description": "Number of Gaussian peaks when run_gaussian is true. Default: 2.", "minimum": 1, "maximum": 8},
                        "regularization": {
                            "type": "number",
                            "description": "Optional fixed smoothing/regularization factor. Omit this to use L-curve automatically for every file.",
                        },
                        "t2_min_ms": {"type": "number", "description": "Lower bound for the T2 search range. Default: 0.01 ms for L-curve."},
                        "t2_max_ms": {"type": "number", "description": "Upper bound for the T2 search range. Default: 100000 ms for L-curve."},
                        "num_bins": {"type": "integer", "description": "Number of T2 bins. Default: 200."},
                        "alpha_min": {"type": "number", "description": "Minimum L-curve smoothing factor. Default: 0.001."},
                        "alpha_max": {"type": "number", "description": "Maximum L-curve smoothing factor. Default: 10000."},
                        "alpha_count": {"type": "integer", "description": "Number of L-curve smoothing factors. Default: 300."},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
    ]


def _result_payload(result: AgentToolResult) -> str:
    return json.dumps(
        {
            "status": result.status,
            "message": result.message,
            "artifacts": result.artifacts,
            "summary": result.summary,
            "error": result.error,
        },
        ensure_ascii=False,
        default=str,
    )


def _is_english(language: str) -> bool:
    return language.lower().startswith("english")


def _language_name(language: str) -> str:
    return "English" if _is_english(language) else "Chinese"


def _explicit_t2_t2_requested(user_goal: str) -> bool:
    text = (user_goal or "").lower()
    normalized = (
        text.replace("－", "-")
        .replace("—", "-")
        .replace("–", "-")
        .replace("×", "x")
        .replace("，", ",")
    )
    compact = re.sub(r"\s+", "", normalized)
    if re.search(r"t2\s*[-_/x]\s*t2", normalized) or "t2t2" in compact or "t2_t2" in normalized:
        return True
    explicit_map_terms = ("交换谱", "关联谱", "二维谱", "二维t2谱", "t2二维谱", "t2-t2图", "t2-t2 map")
    if any(term in normalized for term in explicit_map_terms):
        return True
    if ("2d" in normalized or "二维" in normalized) and "t2" in normalized and ("spectrum" in normalized or "map" in normalized or "谱" in normalized):
        return True
    return False


def _safe_batch_folder(path: Path) -> str:
    token = re.sub(r"[^A-Za-z0-9_.-]+", "_", path.name).strip("._")
    return token or "uploaded_file"


def _uploaded_paths(context: AgentRuntimeContext) -> list[Path]:
    paths = list(context.uploaded_paths)
    if context.uploaded_path is not None and context.uploaded_path not in paths:
        paths.insert(0, context.uploaded_path)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = str(Path(path))
        if resolved not in seen:
            seen.add(resolved)
            unique.append(Path(path))
    return unique


def _active_upload_context_prompt(context: AgentRuntimeContext) -> str:
    active = context.uploaded_path
    uploads = _uploaded_paths(context)
    if active is None and not uploads:
        return (
            "Active uploaded file: none. If the user asks to process an uploaded file, ask them to upload/select one first."
        )

    lines = ["Active uploaded file context:"]
    if active is not None:
        active_path = Path(active)
        suffix = active_path.suffix.lower()
        kind = (
            "PNG phase map"
            if suffix == ".png"
            else "segmented CT label image (TIF)"
            if suffix in {".tif", ".tiff"}
            else "spreadsheet/table or spectrum data"
        )
        lines.append(f"- active uploaded file: {active_path.name}")
        lines.append(f"- active upload kind: {kind}")
        lines.append(f"- active upload suffix: {suffix or '(none)'}")
        lines.append(f"- active upload path for tools: {active_path}")
        if suffix == ".png":
            lines.append(
                "- If the user asks for PNG phase-map geometry, do not say no PNG is uploaded; inspect the PNG with geometry_mode='png'."
            )
            lines.append(
                "- If the user asks for PNG meshing or full 2D NMR simulation, first make sure they supplied the cropped sample width and height or explicit pixel size. If not, ask for that scale instead of starting simulation with defaults."
            )
        if suffix in {".tif", ".tiff"}:
            lines.append("- This TIF is a segmented CT label image. Use inspect_ct_phase_image / run_ct_simulation_workflow, never spreadsheet or PNG tools.")
            state = context.ct_state or {}
            if state and state.get("image_path") == str(active_path):
                lines.append(
                    "- CT workflow state: "
                    + json.dumps(
                        {
                            "step": state.get("step"),
                            "values": state.get("values"),
                            "has_background": state.get("has_background"),
                            "assignment": state.get("assignment"),
                            "phase_confirmed": state.get("phase_confirmed"),
                            "params_confirmed": state.get("params_confirmed"),
                            "params_prefill": state.get("prefill"),
                            "missing_fields": state.get("missing_fields"),
                        },
                        ensure_ascii=False,
                        default=str,
                    )
                )
    if uploads:
        names = ", ".join(Path(path).name for path in uploads[:10])
        lines.append(f"- uploaded file count: {len(uploads)}")
        lines.append(f"- uploaded file names: {names}")
    return "\n".join(lines)


def _require_upload(context: AgentRuntimeContext, response_language: str = "中文") -> AgentToolResult | None:
    if context.uploaded_path is None:
        message = "No data file has been uploaded yet. Please upload an Excel, CSV, or supported text table before asking me to inspect or run it." if _is_english(response_language) else "还没有上传数据文件。请先上传 Excel、CSV 或支持的文本表格，再让我检查或运行。"
        return AgentToolResult("failed", message, error="missing_upload")
    return None


def _is_gaussian_only_goal(context: AgentRuntimeContext) -> bool:
    return infer_requested_plan(context.last_user_goal).workflow == "gaussian_only"


def _gaussian_only_requires_spectrum_error(response_language: str) -> AgentToolResult:
    message = (
        "You asked for peak decomposition only, so I will not run T2 inversion automatically. Please upload an existing T2 spectrum, or explicitly confirm that you want me to run inversion first and then decompose peaks."
        if _is_english(response_language)
        else "你要求只做分峰，所以我不会自动先做 T2 反演。请上传已有 T2 谱表，或明确确认要我先反演再分峰。"
    )
    return AgentToolResult("failed", message, error="gaussian_only_requires_spectrum")


def process_uploaded_files_batch(args: dict[str, Any], context: AgentRuntimeContext, response_language: str = "中文") -> AgentToolResult:
    """Run a complete conservative workflow for every uploaded workbook."""

    uploaded_paths = _uploaded_paths(context)
    if not uploaded_paths:
        message = "No data files have been uploaded yet." if _is_english(response_language) else "还没有上传数据文件。"
        return AgentToolResult("failed", message, error="missing_upload")

    run_gaussian = bool(args.get("run_gaussian", False))
    peak_count = int(args.get("peak_count", 2))
    fixed_regularization = args.get("regularization")
    batch_root = context.workspace / "batch_results"
    batch_root.mkdir(parents=True, exist_ok=True)

    artifacts: list[str] = []
    rows: list[dict[str, Any]] = []
    successful_files = 0

    for uploaded_path in uploaded_paths:
        file_dir = batch_root / _safe_batch_folder(uploaded_path)
        file_dir.mkdir(parents=True, exist_ok=True)
        file_results: list[AgentToolResult] = []
        row: dict[str, Any] = {
            "file": Path(uploaded_path).name,
            "folder": str(file_dir),
            "status": "failed",
            "steps": [],
            "artifacts": [],
        }

        validation = validate_workbook(uploaded_path, language=response_language)
        row["steps"].append({"name": "validate_workbook", "status": validation.status, "message": validation.message, "error": validation.error})
        if validation.status != "success":
            rows.append(row)
            continue

        scale = validation.summary.get("recommended_time_to_ms_scale", 1.0)
        repaired = repair_workbook(uploaded_path, file_dir / "standardized", float(scale or 1.0), language=response_language)
        file_results.append(repaired)
        row["steps"].append({"name": "repair_workbook", "status": repaired.status, "message": repaired.message, "error": repaired.error})
        artifacts.extend(repaired.artifacts)
        row["artifacts"].extend(repaired.artifacts)
        if repaired.status != "success" or not repaired.artifacts:
            rows.append(row)
            continue

        if fixed_regularization is not None:
            inversion_params = {
                "time_to_ms_scale": 1.0,
                "regularization": float(fixed_regularization),
                "t2_min_ms": float(args.get("t2_min_ms", 1.0)),
                "t2_max_ms": float(args.get("t2_max_ms", 1e4)),
                "num_bins": int(args.get("num_bins", 200)),
            }
            inversion = run_fixed_nnls(Path(repaired.artifacts[0]), file_dir / "nnls", inversion_params, language=response_language)
            step_name = "run_fixed_nnls"
        else:
            inversion_params = {
                "time_to_ms_scale": 1.0,
                "t2_min_ms": float(args.get("t2_min_ms", 1e-2)),
                "t2_max_ms": float(args.get("t2_max_ms", 1e5)),
                "num_bins": int(args.get("num_bins", 200)),
                "alpha_min": float(args.get("alpha_min", 1e-3)),
                "alpha_max": float(args.get("alpha_max", 1e4)),
                "alpha_count": int(args.get("alpha_count", 300)),
            }
            inversion = run_lcurve(Path(repaired.artifacts[0]), file_dir / "lcurve", inversion_params, language=response_language)
            step_name = "run_lcurve"

        file_results.append(inversion)
        row["steps"].append({"name": step_name, "status": inversion.status, "message": inversion.message, "error": inversion.error})
        artifacts.extend(inversion.artifacts)
        row["artifacts"].extend(inversion.artifacts)
        if inversion.status != "success":
            rows.append(row)
            continue

        spectrum_path = inversion.summary.get("spectrum_xlsx")
        if run_gaussian and spectrum_path:
            gaussian = run_gaussian_peaks(Path(spectrum_path), file_dir / "gaussian", {"peak_count": peak_count}, language=response_language)
            file_results.append(gaussian)
            row["steps"].append({"name": "run_gaussian_peaks", "status": gaussian.status, "message": gaussian.message, "error": gaussian.error})
            artifacts.extend(gaussian.artifacts)
            row["artifacts"].extend(gaussian.artifacts)

        interpretation = interpret_results(file_results, file_dir / "interpretation", language=response_language)
        file_results.append(interpretation)
        row["steps"].append({"name": "interpret_results", "status": interpretation.status, "message": interpretation.message, "error": interpretation.error})
        artifacts.extend(interpretation.artifacts)
        row["artifacts"].extend(interpretation.artifacts)

        plan = infer_requested_plan(context.last_user_goal)
        plan.needs_gaussian = run_gaussian
        plan.peak_count = peak_count
        report = generate_report(
            file_dir / "report",
            user_goal=context.last_user_goal or ("Batch T2 processing" if _is_english(response_language) else "批量 T2 数据处理"),
            validation=validation,
            workflow_results=file_results,
            parameter_notes=build_parameter_guidance(plan, language=response_language),
            language=response_language,
        )
        row["steps"].append({"name": "generate_report", "status": report.status, "message": report.message, "error": report.error})
        artifacts.extend(report.artifacts)
        row["artifacts"].extend(report.artifacts)
        row["status"] = "success" if report.status == "success" else "partial"
        successful_files += 1 if row["status"] in {"success", "partial"} else 0
        rows.append(row)

    summary_path = batch_root / timestamped_name("batch_summary", "md")
    if _is_english(response_language):
        lines = ["# Batch T2 Processing Summary", ""]
        for row in rows:
            lines.extend([f"## {row['file']}", f"- Status: {row['status']}", f"- Output folder: `{row['folder']}`"])
            for step in row["steps"]:
                lines.append(f"- {step['name']}: {step['status']} - {step['message']}")
            lines.append("")
        message = f"Batch processing completed for {successful_files}/{len(uploaded_paths)} file(s). Results are grouped by file folder in the download zip."
    else:
        lines = ["# 批量 T2 处理摘要", ""]
        for row in rows:
            lines.extend([f"## {row['file']}", f"- 状态：{row['status']}", f"- 输出文件夹：`{row['folder']}`"])
            for step in row["steps"]:
                lines.append(f"- {step['name']}：{step['status']} - {step['message']}")
            lines.append("")
        message = f"批量处理完成：{successful_files}/{len(uploaded_paths)} 个文件已生成结果。下载 zip 会按文件夹分组保存每个文件的产物。"

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    artifacts.append(str(summary_path))

    status = "success" if successful_files == len(uploaded_paths) else ("failed" if successful_files == 0 else "success")
    return AgentToolResult(
        status,
        message,
        artifacts=artifacts,
        summary={
            "file_count": len(uploaded_paths),
            "successful_file_count": successful_files,
            "batch_root": str(batch_root),
            "files": rows,
        },
        error=None if successful_files else "batch_failed",
    )


def execute_agent_tool(name: str, args: dict[str, Any], context: AgentRuntimeContext, response_language: str = "中文") -> AgentToolResult:
    """Execute one whitelisted tool and update runtime context."""

    if name == "process_uploaded_files_batch":
        result = process_uploaded_files_batch(args, context, response_language=response_language)
        context.results.append(result)
        return result

    if name == "inspect_ct_phase_image":
        result = inspect_ct_phase_image(context, args, language=response_language)
        context.results.append(result)
        return result

    if name == "run_ct_simulation_workflow":
        if not is_ct_upload(context.uploaded_path):
            message = "Upload a segmented CT TIF first." if _is_english(response_language) else "请先上传分割好的 CT TIF 图像。"
            return AgentToolResult("failed", message, error="not_ct_tif")
        return request_ct_run(context, args, language=response_language, on_stage=context.stage_callback)

    if name == "inspect_2d_geometry_input":
        result = inspect_2d_geometry_input(
            context.uploaded_path,
            context.workspace / "simulation_2d",
            args,
            language=response_language,
        )
        context.results.append(result)
        return result

    if name in {"run_2d_mesh_and_decay", "run_2d_simulation_full_workflow"} and str(args.get("geometry_mode", "png")).lower() == "rule":
        # Ideal structures go through the parameter-confirmation dialog first.
        return request_ideal_run(context, args, language=response_language, on_stage=context.stage_callback)

    if name == "run_2d_mesh_and_decay":
        result = run_2d_mesh_and_decay(
            context.uploaded_path,
            context.workspace / "simulation_2d",
            args,
            language=response_language,
        )
        context.results.append(result)
        standard_decay = result.summary.get("standard_decay_xlsx")
        if result.status == "success" and standard_decay:
            context.simulation_decay_path = Path(standard_decay)
            context.repaired_path = Path(standard_decay)
        return result

    if name == "run_local_nmr_triangle_demo":
        demo_root = context.workspace / "local_nmr_triangle_demo"
        try:
            simulation = run_local_nmr_triangle_t2_t2(demo_root / "simulation", args)
        except Exception as exc:
            simulation_result = AgentToolResult(
                "failed",
                "本地 NMR 理想三角演示无法运行。"
                if not _is_english(response_language)
                else "Local NMR ideal-triangle demo could not run.",
                summary={"stage": "local_nmr_triangle_demo"},
                error=str(exc),
            )
            context.results.append(simulation_result)
            return simulation_result
        simulation_artifacts = list(simulation.get("artifacts", []))
        simulation_result = AgentToolResult(
            "success" if simulation.get("status") == "success" else "failed",
            "本地 NMR 理想三角网格、T2 衰减和 T2-T2 演示模拟完成。"
            if not _is_english(response_language)
            else "Local NMR ideal-triangle mesh, T2 decay, and T2-T2 demo simulation completed.",
            artifacts=simulation_artifacts,
            summary=simulation,
            error=simulation.get("error"),
        )
        context.results.append(simulation_result)
        if simulation_result.status != "success":
            return simulation_result

        decay_csv = simulation.get("standard_decay_source_csv")
        if not decay_csv:
            return AgentToolResult(
                "failed",
                "本地 NMR 模拟没有生成可用于 T2 反演的衰减 CSV。"
                if not _is_english(response_language)
                else "Local NMR simulation did not produce a decay CSV for T2 inversion.",
                error="missing_simulation_decay_csv",
            )
        decay_frame = pd.read_csv(Path(decay_csv))
        if "time_ms" not in decay_frame.columns:
            return AgentToolResult(
                "failed",
                "本地 NMR 衰减 CSV 缺少 time_ms 列。"
                if not _is_english(response_language)
                else "Local NMR decay CSV is missing the time_ms column.",
                error="missing_time_column",
            )
        signal_column = next(
            (
                column
                for column in [
                    "coupled_signal_normalized",
                    "normalized_signal",
                    "total_signal",
                    "uncoupled_signal_normalized",
                ]
                if column in decay_frame.columns
            ),
            None,
        )
        if signal_column is None:
            return AgentToolResult(
                "failed",
                "本地 NMR 衰减 CSV 缺少可用于 T2 反演的信号列。"
                if not _is_english(response_language)
                else "Local NMR decay CSV is missing a signal column for T2 inversion.",
                error="missing_signal_column",
            )
        standard_decay = write_standard_decay_workbook(
            demo_root / "decay" / timestamped_name("local_nmr_triangle_coupled__standard_decay", "xlsx"),
            decay_frame["time_ms"].to_numpy(dtype=float),
            decay_frame[signal_column].to_numpy(dtype=float),
        )
        context.simulation_decay_path = standard_decay
        context.repaired_path = standard_decay

        inversion_params = {
            "time_to_ms_scale": 1.0,
            "regularization": float(args.get("regularization", 1.0)),
            "t2_min_ms": float(args.get("t2_min_ms", 1.0)),
            "t2_max_ms": float(args.get("t2_max_ms", 1e4)),
            "num_bins": int(args.get("num_bins", 200)),
        }
        inversion = run_fixed_nnls(
            standard_decay,
            demo_root / "nnls",
            inversion_params,
            language=response_language,
        )
        context.results.append(inversion)
        if inversion.status == "success" and "spectrum_xlsx" in inversion.summary:
            context.spectrum_path = Path(inversion.summary["spectrum_xlsx"])

        simulation_stages = dict(simulation.get("simulation_stages", {}))
        simulation_stages["decay"] = [*simulation_stages.get("decay", []), str(standard_decay)]
        simulation_stages["inversion"] = list(inversion.artifacts)
        return AgentToolResult(
            "success" if inversion.status == "success" else "failed",
            "本地 NMR 理想三角演示已完成；T2 反演已使用当前成熟 fixed NNLS 流程。"
            if not _is_english(response_language)
            else "Local NMR ideal-triangle demo completed; T2 inversion used the current mature fixed NNLS workflow.",
            artifacts=[*simulation_artifacts, str(standard_decay), *inversion.artifacts],
            summary={
                "stage": "local_nmr_triangle_demo",
                "simulation_decay_xlsx": str(standard_decay),
                "spectrum_xlsx": str(context.spectrum_path) if context.spectrum_path else None,
                "t2_inversion_source": "existing_t2process_fixed_nnls",
                "regularization": inversion_params["regularization"],
                "simulation_stages": simulation_stages,
                "local_nmr_simulation": simulation,
                "t2_inversion": inversion.summary,
            },
            error=inversion.error,
        )

    if name == "run_2d_simulation_full_workflow":
        if str(args.get("geometry_mode", "png")).lower() == "png" and not png_physical_scale_provided(args):
            return png_physical_scale_error(response_language)
        mesh = run_2d_mesh_and_decay(
            context.uploaded_path,
            context.workspace / "simulation_2d",
            args,
            language=response_language,
        )
        context.results.append(mesh)
        if mesh.status != "success":
            return mesh
        standard_decay = mesh.summary.get("standard_decay_xlsx")
        if not standard_decay:
            return AgentToolResult(
                "failed",
                "2D simulation did not produce a standard decay workbook.",
                error="missing_simulation_decay",
            )
        context.simulation_decay_path = Path(standard_decay)
        context.repaired_path = Path(standard_decay)

        if args.get("regularization") is not None:
            inversion = run_fixed_nnls(
                context.repaired_path,
                context.workspace / "simulation_2d" / "nnls",
                {
                    "time_to_ms_scale": 1.0,
                    "regularization": float(args["regularization"]),
                    "t2_min_ms": float(args.get("t2_min_ms", 1.0)),
                    "t2_max_ms": float(args.get("t2_max_ms", 1e4)),
                    "num_bins": int(args.get("num_bins", 200)),
                },
                language=response_language,
            )
        else:
            inversion = run_lcurve(
                context.repaired_path,
                context.workspace / "simulation_2d" / "lcurve",
                {
                    "time_to_ms_scale": 1.0,
                    "t2_min_ms": float(args.get("t2_min_ms", 1e-2)),
                    "t2_max_ms": float(args.get("t2_max_ms", 1e5)),
                    "num_bins": int(args.get("num_bins", 200)),
                    "alpha_min": float(args.get("alpha_min", 1e-6)),
                    "alpha_max": float(args.get("alpha_max", 1e2)),
                    "alpha_count": int(args.get("alpha_count", 60)),
                },
                language=response_language,
            )
        context.results.append(inversion)
        if inversion.status == "success" and "spectrum_xlsx" in inversion.summary:
            context.spectrum_path = Path(inversion.summary["spectrum_xlsx"])

        run_t2_t2_requested = bool(args.get("run_t2_t2", False)) and _explicit_t2_t2_requested(context.last_user_goal)
        if run_t2_t2_requested and context.spectrum_path is not None:
            t2_t2 = run_reduced_t2_t2(
                context.spectrum_path,
                context.workspace / "simulation_2d" / "t2_t2",
                {
                    "t2_t2_alpha": float(args.get("t2_t2_alpha", 0.05)),
                    "t2_t2_t1_points": int(args.get("t2_t2_t1_points", 18)),
                    "t2_t2_t2_points": int(args.get("t2_t2_t2_points", 24)),
                    "t2_t2_bin_points": int(args.get("t2_t2_bin_points", 28)),
                },
                language=response_language,
            )
            context.results.append(t2_t2)
        else:
            t2_t2 = None

        if bool(args.get("run_gaussian", False)) and context.spectrum_path is not None:
            gaussian = run_gaussian_peaks(
                context.spectrum_path,
                context.workspace / "simulation_2d" / "gaussian",
                {"peak_count": int(args.get("peak_count", 2))},
                language=response_language,
            )
            context.results.append(gaussian)
        else:
            gaussian = None

        workflow_results = [mesh, inversion]
        if t2_t2 is not None:
            workflow_results.append(t2_t2)
        if gaussian is not None:
            workflow_results.append(gaussian)

        simulation_stages: dict[str, list[str]] = {}
        for item in workflow_results:
            for stage_name, stage_artifacts in item.summary.get("simulation_stages", {}).items():
                simulation_stages.setdefault(stage_name, []).extend([str(path) for path in stage_artifacts])
        simulation_stages.setdefault("inversion", []).extend(list(inversion.artifacts))
        if gaussian is not None:
            simulation_stages.setdefault("gaussian", []).extend(list(gaussian.artifacts))

        final_status = "success"
        final_error = None
        for item in workflow_results:
            if item.status != "success":
                final_status = "failed"
                final_error = item.error
                break

        return AgentToolResult(
            final_status,
            "2D NMR 模拟、T2 反演和可选 T2-T2 流程完成。"
            if not _is_english(response_language)
            else "2D NMR simulation, T2 inversion, and optional T2-T2 workflow completed.",
            artifacts=[artifact for result in workflow_results for artifact in result.artifacts],
            summary={
                **inversion.summary,
                "stage": "full_workflow",
                "simulation_decay_xlsx": str(context.repaired_path),
                "spectrum_xlsx": str(context.spectrum_path) if context.spectrum_path else None,
                "run_t2_t2": run_t2_t2_requested,
                "t2_t2_requested_by_tool": bool(args.get("run_t2_t2", False)),
                "t2_t2_explicitly_requested_by_user": _explicit_t2_t2_requested(context.last_user_goal),
                "t2_t2_enabled": bool(t2_t2 is not None and t2_t2.status == "success"),
                "simulation_stages": simulation_stages,
                "mesh_and_decay": mesh.summary,
                "t2_t2": t2_t2.summary if t2_t2 is not None else None,
                "gaussian": gaussian.summary if gaussian is not None else None,
            },
            error=final_error or inversion.error,
        )

    if name in {"inspect_workbook_schema", "validate_workbook", "repair_workbook"}:
        missing = _require_upload(context, response_language)
        if missing:
            return missing

    if name in {"repair_workbook", "run_lcurve", "run_fixed_nnls"} and _is_gaussian_only_goal(context):
        if context.validation is None or context.validation.summary.get("data_kind") != "spectrum":
            return _gaussian_only_requires_spectrum_error(response_language)

    if name in {"run_lcurve", "run_fixed_nnls"} and context.validation is not None and context.validation.summary.get("data_kind") == "spectrum":
        message = "The uploaded workbook looks like an existing T2 spectrum, so I will not run inversion on it. Use run_gaussian_peaks directly if the user wants peak decomposition." if _is_english(response_language) else "上传的工作簿看起来是已有 T2 谱表，因此不会再做反演。如果用户要分峰，请直接调用 run_gaussian_peaks。"
        return AgentToolResult("failed", message, error="spectrum_input_not_decay")

    if name in {"run_lcurve", "run_fixed_nnls"} and context.repaired_path is None:
        message = "Before inversion, repair_workbook must generate a standardized Excel file." if _is_english(response_language) else "反演前需要先调用 repair_workbook 生成标准化 Excel。"
        return AgentToolResult("failed", message, error="missing_repaired_workbook")

    if name == "inspect_workbook_schema":
        return inspect_workbook_schema(context.uploaded_path, int(args.get("preview_rows", 8)), language=response_language)  # type: ignore[arg-type]

    if name == "validate_workbook":
        result = validate_workbook(context.uploaded_path, language=response_language)  # type: ignore[arg-type]
        context.validation = result
        if result.status == "success" and result.summary.get("data_kind") == "spectrum":
            context.spectrum_path = Path(context.uploaded_path)  # type: ignore[arg-type]
            context.repaired_path = None
        return result

    if name == "repair_workbook":
        if context.validation is not None and context.validation.summary.get("data_kind") == "spectrum":
            message = "The uploaded workbook already looks like a T2 spectrum, so it should not be standardized as raw decay data. Continue with run_gaussian_peaks if the user wants peak decomposition." if _is_english(response_language) else "上传的工作簿已经像是 T2 谱表，不应标准化成原始衰减数据。如果用户要分峰，请继续调用 run_gaussian_peaks。"
            return AgentToolResult("failed", message, error="spectrum_input_not_decay")
        scale = args.get("time_to_ms_scale")
        if scale is None and context.validation is not None:
            scale = context.validation.summary.get("recommended_time_to_ms_scale", 1.0)
        result = repair_workbook(context.uploaded_path, context.workspace / "standardized", float(scale or 1.0), language=response_language)  # type: ignore[arg-type]
        if result.status == "success" and result.artifacts:
            context.repaired_path = Path(result.artifacts[0])
        return result

    if name == "run_lcurve":
        params = {
            "time_to_ms_scale": 1.0,
            "t2_min_ms": float(args.get("t2_min_ms", 1e-2)),
            "t2_max_ms": float(args.get("t2_max_ms", 1e5)),
            "num_bins": int(args.get("num_bins", 200)),
            "alpha_min": float(args.get("alpha_min", 1e-3)),
            "alpha_max": float(args.get("alpha_max", 1e4)),
            "alpha_count": int(args.get("alpha_count", 300)),
            "criterion": str(args.get("criterion", "ratio")),
        }
        result = run_lcurve(context.repaired_path, context.workspace / "lcurve", params, language=response_language)  # type: ignore[arg-type]
        context.results.append(result)
        if result.status == "success" and "spectrum_xlsx" in result.summary:
            context.spectrum_path = Path(result.summary["spectrum_xlsx"])
        return result

    if name == "run_fixed_nnls":
        params = {
            "time_to_ms_scale": 1.0,
            "regularization": float(args["regularization"]),
            "t2_min_ms": float(args.get("t2_min_ms", 1.0)),
            "t2_max_ms": float(args.get("t2_max_ms", 1e4)),
            "num_bins": int(args.get("num_bins", 200)),
        }
        result = run_fixed_nnls(context.repaired_path, context.workspace / "nnls", params, language=response_language)  # type: ignore[arg-type]
        context.results.append(result)
        if result.status == "success" and "spectrum_xlsx" in result.summary:
            context.spectrum_path = Path(result.summary["spectrum_xlsx"])
        return result

    if name == "plot_decay_spectrum":
        if context.repaired_path is None or context.spectrum_path is None:
            message = "Plotting requires both a standardized decay file and a T2 spectrum file." if _is_english(response_language) else "画图前需要已有标准化 decay 文件和 T2 spectrum 文件。"
            return AgentToolResult("failed", message, error="missing_plot_inputs")
        result = plot_decay_spectrum(context.repaired_path, context.spectrum_path, context.workspace / "plots", {"time_to_ms_scale": 1.0}, language=response_language)
        context.results.append(result)
        return result

    if name == "run_gaussian_peaks":
        if context.spectrum_path is None:
            message = "Peak decomposition requires a completed T2 inversion or an uploaded T2 spectrum." if _is_english(response_language) else "分峰前需要先完成 T2 反演或上传 T2 spectrum。"
            return AgentToolResult("failed", message, error="missing_spectrum")
        result = run_gaussian_peaks(context.spectrum_path, context.workspace / "gaussian", {"peak_count": int(args["peak_count"])}, language=response_language)
        context.results.append(result)
        return result

    if name == "generate_report":
        goal = context.last_user_goal or ("The user wants the agent to complete T2 data processing automatically." if _is_english(response_language) else "用户希望由 Agent 自动完成 T2 数据处理。")
        plan = infer_requested_plan(goal)
        result = generate_report(
            context.workspace / "report",
            user_goal=goal,
            validation=context.validation
            or AgentToolResult(
                "failed",
                "Data diagnosis has not been completed yet." if _is_english(response_language) else "尚未完成数据诊断。",
                error="missing_validation",
            ),
            workflow_results=context.results,
            parameter_notes=build_parameter_guidance(plan, language=response_language),
            language=response_language,
        )
        context.report = result
        return result

    if name == "interpret_results":
        result = interpret_results(context.results, context.workspace / "interpretation", language=response_language)
        context.results.append(result)
        return result

    message = f"Unknown tool: {name}" if _is_english(response_language) else f"未知工具：{name}"
    return AgentToolResult("failed", message, error="unknown_tool")


def _assistant_to_dict(message: Any) -> dict[str, Any]:
    if hasattr(message, "model_dump"):
        data = message.model_dump()
    else:
        data = {
            "role": "assistant",
            "content": getattr(message, "content", None),
            "tool_calls": getattr(message, "tool_calls", None),
        }
    data["role"] = "assistant"
    return {key: value for key, value in data.items() if value is not None}


def _local_demo_completion_message(result: AgentToolResult, response_language: str) -> str:
    artifact_count = len(result.artifacts)
    if _is_english(response_language):
        return (
            "The local NMR ideal-triangle demo has completed. "
            "The repository-bundled simulator produced the mesh and T2 decay artifacts, "
            "and the simulated decay was sent through the existing fixed NNLS T2 inversion workflow. "
            f"{artifact_count} artifact(s) are available in the result panel."
        )
    return (
        "本地 NMR 理想三角演示已完成。仓库内置模拟流程已经生成网格和 T2 衰减产物，"
        "模拟衰减也已接入当前成熟的 fixed NNLS T2 反演流程。"
        f"右侧结果栏已同步 {artifact_count} 个产物。"
    )


def run_deepseek_agent_turn(
    *,
    api_key: str,
    model: str,
    thinking_enabled: bool,
    user_message: str,
    context: AgentRuntimeContext,
    prior_messages: list[dict[str, Any]],
    client: Any | None = None,
    max_tool_rounds: int = 6,
    on_trace: Callable[[dict[str, Any]], None] | None = None,
    on_tool_result: Callable[[AgentToolResult], None] | None = None,
    response_language: str = "中文",
) -> AgentTurnResult:
    """Run one DeepSeek chat turn with real function calling."""

    if client is None:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)

    context.last_user_goal = user_message
    messages = list(prior_messages)
    user_language = _language_name(response_language)
    active_upload_context = _active_upload_context_prompt(context)
    language_instruction = (
        "User-facing language: English. Reply in English. Any visible summaries, explanations, tool-result interpretation, and generated reports must be in English unless the user explicitly asks for another language."
        if _is_english(response_language)
        else "用户可见语言：中文。请用中文回复。所有面向用户的摘要、解释、工具结果解读和生成报告都必须使用中文，除非用户明确要求其他语言。"
    )
    system_content = (
        "You are an NMR 2D simulation and T2 inversion agent that can call real tools. "
        "For 2D simulation requests, use the simulation tools instead of spreadsheet validation tools. "
        "Segmented CT TIF route: if the active upload is a .tif/.tiff label image, call inspect_ct_phase_image first (not spreadsheet or PNG tools). "
        "Pass has_background only if the user explicitly said whether outside/background pixels exist; never infer it from file names. Pass phase_labels only for label values the user explicitly stated, and pixel_size_um / run_lcurve / regularization / run_gaussian / peak_count only when stated. "
        "If inspect_ct_phase_image returns error needs_background_answer, ask the user one short question: does the image contain background (outside-sample) pixels? Explain that the extra pixel value could be air or background. Do not run anything else that turn. "
        "If it returns needs_phase_confirmation, briefly explain the AI first guess (value -> phase, reasoning and confidence), compare it with any labels the user stated, and tell the user to check the draggable markers in the CT phase preview window and press confirm; meshing waits for that confirmation. The app continues automatically after the confirm button (parameter dialog or run), so do not ask the user to type a confirmation in chat. "
        "After phase confirmation the app opens a parameter confirmation dialog when resolution, simulation core parameters, smoothing/L-curve choice or Gaussian choice were not all given; defaults are 1 um/pixel, L-curve on, Gaussian decomposition on. "
        "Call run_ct_simulation_workflow when the user asks to run; if it returns needs_confirmation, tell the user which confirmation is pending instead of claiming results. Never invent CT results. "
        "When explaining CT results, relate mesh quality, decay length, the selected smoothing factor, T2 peaks and, if air is present, the reduced water saturation; warn that a 2D slice is not a 3D pore network. "
        "For pore-size statements use the reported decay.surface_to_volume_per_um and bulk_t2_ms (1/T2 = 1/T2_bulk + rho*S/V); do not back-calculate pore radius from T2 while ignoring bulk relaxation. "
        "If the user uploads a PNG or asks for red/yellow phase-map simulation, call inspect_2d_geometry_input and then run_2d_mesh_and_decay or run_2d_simulation_full_workflow with geometry_mode='png'. "
        "For PNG phase maps with white margins, keep the original upload, enable normalize_phase_colors when edge or antialiasing colors may be present, and rely on the PNG workflow to crop the white border before meshing. "
        "For PNG simulation or full PNG simulation-to-inversion, physical scale is required before meshing. If the user has not provided physical_size_x_um/physical_size_y_um or explicit pixel_size values, ask for the cropped sample width and height instead of guessing default dimensions. "
        "If the user gives physical dimensions such as 300 by 300 micrometers for a PNG, pass physical_size_x_um and physical_size_y_um; these dimensions apply to the cropped sample region, not the screenshot canvas. "
        "Do not ask for nonessential inversion parameters such as regularization, T2 bins, or L-curve range when defaults are acceptable; only ask for information required to make the simulation physically scaled. "
        "Do not set run_t2_t2 for ordinary simulation-and-inversion requests; the default full workflow is T2 only. "
        "Set run_t2_t2=true only when the user explicitly asks for T2-T2, a T2-T2 map, exchange spectrum, or correlation spectrum, and explain that the current output is a reduced T2-T2 map derived from the 1D T2 spectrum. "
        "If the user asks for the built-in ideal triangle simulation and has not uploaded a PNG, call run_2d_simulation_full_workflow with geometry_mode='rule'; do not create a PNG phase map as an intermediate input. "
        "Ideal-structure route: the only supported shape is one large equilateral triangular pore plus one inverted small equilateral triangular pore, optionally joined by a throat (coupled). If the user asks for circles, slits, rectangles or other shapes, say they are not supported yet and offer the triangle pair. "
        "Pass only the values the user stated: large_side_um, small_side_um, coupled, throat_length_um, throat_width_um, large_water_saturation, small_water_saturation (0-1), diffusion_um2_per_ms, bulk_t2_ms, rho_solid_um_per_ms, run_lcurve, regularization, run_gaussian, peak_count. Never fill in defaults yourself. "
        "If run_2d_simulation_full_workflow returns needs_ideal_parameter_confirmation, tell the user in two or three sentences which choices are pending (shape, pore sizes, coupling, water saturation, physics, inversion) and that a confirmation dialog with a geometry preview has opened; the app runs the workflow after the user presses confirm, so do not ask them to type parameters in chat and do not claim results. "
        "When explaining ideal-structure results, compare the inverted T2 peaks with summary.estimated_t2_ms (fast-diffusion estimate per pore), state whether the pores were coupled, and note that water below Sw≈0.395 sits only in the triangle corners. "
        "For the first version, only 2D simulation is supported, and mesh generation must use pyGIMLi triangular meshing. "
        "For the ordinary first-version ideal-triangle simulation, run only the 1D T2 workflow. "
        "If the user explicitly asks for the local NMR simulator or ideal triangle mesh demonstration, call run_local_nmr_triangle_demo; it uses the repository-bundled simulator and still sends the simulated decay into the existing fixed NNLS T2 inversion pipeline. "
        "Do not attempt D-T2 unless a future tool explicitly supports it. "
        "When the user asks for the whole local T2 simulation flow, call run_2d_simulation_full_workflow so mesh, decay, T2 inversion, and optional Gaussian decomposition are connected. "
        "When the user only asks for T2 inversion, keep using the existing T2 workbook tools and do not force simulation. "
        "When the user has uploaded data and asks to inspect, run, or interpret it, first call inspect_workbook_schema, then call validate_workbook. "
        "If the user only asks about capabilities, parameter meanings, boundaries, expected data format, workflow, or usage advice, do not call tools; answer clearly. "
        "Do not assume the first column is time. Infer the time/T2 column from labels, monotonicity, numeric ranges, and preview rows. "
        "If the user asks to only run peak decomposition, do not call repair_workbook, run_lcurve, or run_fixed_nnls; use an existing/uploaded T2 spectrum, or ask the user to confirm inversion first. "
        "After validate_workbook, check summary.data_kind. If it is spectrum, do not call repair_workbook, run_lcurve, or run_fixed_nnls; ask whether the user wants Gaussian peak decomposition, or call run_gaussian_peaks directly when the user already asked for peaks. "
        "Only run T2 inversion when summary.data_kind is decay. "
        "If Time is in the second column and Peak is in the first column, this is usually a column-order mismatch with the older tool expectation; do not call it swapped labels. "
        "Only say labels may be wrong when labels and numeric shapes contradict each other. "
        "If the column order, header position, multi-signal layout, or workbook layout is nonstandard, tell the user and call repair_workbook to standardize it. "
        "When the user does not understand parameters and the uploaded data is decay data, prefer repair_workbook + run_lcurve. "
        "When the user asks to set the L-curve smoothing-factor/alpha search range, call run_lcurve with alpha_min and alpha_max. "
        "When multiple files are uploaded and the user asks to process all files, batch process files, analyze multiple files, or generate results for all uploads, call process_uploaded_files_batch instead of running single-file tools repeatedly. "
        "When the user explicitly specifies a smoothing/regularization factor, use run_fixed_nnls. "
        "When the user asks for peak decomposition, call run_gaussian_peaks after a spectrum exists. "
        "When the user asks to interpret results, asks what the result means, asks whether the result is good, or asks for next steps, call interpret_results instead of only pointing to the right-side tool results. "
        "When a tool result contains summary.literature_findings and summary.literature_references, build the physical explanation on those findings, keep their AGU in-text citations such as (Kleinberg et al., 1994) next to the statements they support, and end the reply with a short 参考文献/References list copied exactly from literature_references. Never cite a paper that is not in literature_references and never invent DOIs. "
        "Do not claim that a tool has run unless this turn includes the corresponding tool result. "
        "Write for beginners and explain the role of the smoothing factor, L-curve, T2 range, and peak count when relevant. "
        f"{language_instruction} "
        f"Requested user-facing language label: {user_language}."
        f"\n\n{active_upload_context}"
        f"\n\n{render_skill_prompt()}"
    )
    system_index = next((idx for idx, message in enumerate(messages) if message.get("role") == "system"), None)
    if system_index is None:
        messages.insert(
            0,
            {
                "role": "system",
                "content": system_content,
            },
        )
    else:
        messages[system_index] = {**messages[system_index], "content": system_content}

    messages.append({"role": "user", "content": user_message})
    tool_results: list[AgentToolResult] = []
    trace: list[dict[str, Any]] = [
        {
            "kind": "plan",
            "message": "This turn first lets the model decide whether tools are needed; if tools are requested, only whitelisted NMR simulation and T2 tools are executed."
            if _is_english(response_language)
            else "本轮先让模型判断是否需要调用工具；若模型请求工具，只执行白名单 NMR 模拟和 T2 tools。",
        }
    ]
    if on_trace:
        on_trace(trace[0])
    tools = build_tool_specs()

    for _ in range(max_tool_rounds):
        kwargs = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.2,
            "extra_body": {"thinking": {"type": "enabled" if thinking_enabled else "disabled"}},
        }
        response = client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None) or []
        messages.append(_assistant_to_dict(message))

        if not tool_calls:
            return AgentTurnResult(message.content or "", messages, tool_results, trace)

        for tool_call in tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            trace.append(
                {
                    "kind": "tool_call",
                    "tool_name": name,
                    "arguments": args,
                    "message": f"AI requested tool `{name}`." if _is_english(response_language) else f"AI 请求调用工具 `{name}`。",
                }
            )
            if on_trace:
                on_trace(trace[-1])
            result = execute_agent_tool(name, args, context, response_language=response_language)
            tool_results.append(result)
            context.tool_history.append(result)
            if on_tool_result:
                on_tool_result(result)
            trace.append(
                {
                    "kind": "tool_result",
                    "tool_name": name,
                    "status": result.status,
                    "message": result.message,
                    "error": result.error,
                    "summary_keys": sorted(result.summary.keys()),
                    "artifact_count": len(result.artifacts),
                }
            )
            if on_trace:
                on_trace(trace[-1])
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": _result_payload(result)})
            if name == "run_local_nmr_triangle_demo" and result.status == "success":
                completion = _local_demo_completion_message(result, response_language)
                messages.append({"role": "assistant", "content": completion})
                return AgentTurnResult(completion, messages, tool_results, trace)

    fallback = (
        "I called several rounds of tools but did not receive a final assistant reply yet. Please check the tool results on the right, or ask me to continue the analysis."
        if _is_english(response_language)
        else "我已经调用了多轮工具，但还没有得到最终回复。请查看右侧工具结果，或让我继续分析。"
    )
    return AgentTurnResult(fallback, messages, tool_results, trace)
