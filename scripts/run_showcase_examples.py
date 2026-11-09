"""Run every supported agent usage once, headless, and file the outputs by stage.

Usage (project conda environment):
    python scripts/run_showcase_examples.py [--out outputs/showcase] [--skip-ct]

Three usages are covered, each through the same whitelisted tools the web agent
calls (no language model involved):

1. measured decay  -> inspection, repair, L-curve inversion, plots, Gaussian
                      peaks, interpretation and report;
2. ideal structure -> four confirmed cases (coupled / uncoupled, full and partial
                      water saturation) through the parameter-confirmation route;
3. segmented CT    -> a four-phase slice with background, AI phase guess
                      confirmed, L-curve inversion and Gaussian peaks.

A manifest.json at the top of the output folder lists every file with its usage,
case and stage category.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from t2_agent.agent import AgentRuntimeContext, execute_agent_tool  # noqa: E402
from t2_agent.ct_workflow import confirm_phase_assignment, confirm_run_parameters  # noqa: E402
from t2_agent.ideal_workflow import confirm_ideal_parameters  # noqa: E402

IDEAL_CASES = {
    "A_coupled_full": {"coupled": True, "large_water_saturation": 1.0, "small_water_saturation": 1.0},
    "B_uncoupled_full": {"coupled": False, "large_water_saturation": 1.0, "small_water_saturation": 1.0},
    "C_coupled_bubble_Sw0p70": {"coupled": True, "large_water_saturation": 0.70, "small_water_saturation": 0.70},
    "D_uncoupled_corner_Sw0p30": {"coupled": False, "large_water_saturation": 0.30, "small_water_saturation": 0.30},
    # Partly drained large pore with the same water volume per wetted wall as the saturated small pore.
    "E_uncoupled_large_Sw0p40": {"coupled": False, "large_water_saturation": 0.40, "small_water_saturation": 1.0},
}

# Ordered rules on the file name; the first match wins.
CATEGORIES = [
    ("interpretation", "Interpretation report and overview figures", lambda n: n.startswith(("interpretation", "inversion_report", "simulation_report"))),
    ("report", "Summary report", lambda n: n.startswith("report")),
    ("gaussian", "Gaussian peaks", lambda n: "gaussian" in n),
    ("lcurve", "L-curve diagnostics", lambda n: "lcurve_metri" in n or "lcurve_summa" in n or n.startswith("alpha_") or "__lcurve__alpha" in n),
    ("t2_inversion", "T2 inversion spectra and fits", lambda n: any(k in n for k in ("lcurve_spect", "lcurve_fit", "lcurve_trimm", "nnls", "decay_t2", "t2_components", "t2_dashboard"))),
    ("inspection", "Data inspection and standardization", lambda n: n.startswith("experimentaldecay__standardized__2") or "repaired" in n),
    ("mesh", "Mesh and mesh quality", lambda n: "mesh" in n),
    ("decay", "NMR decay", lambda n: "decay" in n),
    ("geometry", "Geometry, phases and parameter records", lambda n: any(k in n for k in ("phase", "geometry", "preview", "run_config", "mapping", "labels"))),
    ("run_record", "Run records", lambda n: "summary" in n and n.endswith(".json")),
]
CATEGORY_LABELS = {key: label for key, label, _ in CATEGORIES} | {"other": "Other"}


def classify(path: Path) -> str:
    name = path.name.lower()
    for key, _label, rule in CATEGORIES:
        if rule(name):
            return key
    return "other"


def log(case: str, result) -> None:
    print(f"[{case}] {result.status}: {result.message.splitlines()[0][:160]}" + (f"  ({result.error})" if result.error else ""), flush=True)


def run_measured(out: Path) -> dict:
    data = ROOT / "testData" / "ExperimentalDecay.xlsx"
    context = AgentRuntimeContext(workspace=out, uploaded_path=data, uploaded_paths=[data])
    context.last_user_goal = "This is NMR experimental decay data from biomass-bearing soil from Vienna. Run the T2 inversion with the L-curve choosing the smoothing factor automatically, then fit a two-peak Gaussian decomposition and interpret the result"
    steps = [
        ("inspect_workbook_schema", {}),
        ("validate_workbook", {}),
        ("repair_workbook", {}),
        ("run_lcurve", {}),
        ("plot_decay_spectrum", {}),
        ("run_gaussian_peaks", {"peak_count": 2}),
        ("interpret_results", {}),
        ("generate_report", {"user_goal": context.last_user_goal}),
    ]
    status = []
    for name, args in steps:
        result = execute_agent_tool(name, args, context)
        log(f"measured:{name}", result)
        status.append({"tool": name, "status": result.status, "message": result.message.splitlines()[0] if result.message else ""})
    return {"input": str(data), "steps": status}


def run_ideal(out: Path) -> dict:
    records = {}
    for case, params in IDEAL_CASES.items():
        context = AgentRuntimeContext(workspace=out / case)
        context.last_user_goal = "This is NMR experimental decay data from biomass-bearing soil from Vienna. Run the T2 inversion with the L-curve choosing the smoothing factor automatically, then fit a two-peak Gaussian decomposition and interpret the result"
        waiting = execute_agent_tool("run_2d_simulation_full_workflow", {"geometry_mode": "rule"}, context)
        log(f"ideal:{case}:request", waiting)
        confirm_ideal_parameters(context, dict(params))
        started = time.time()
        result = execute_agent_tool("run_2d_simulation_full_workflow", {"geometry_mode": "rule"}, context)
        log(f"ideal:{case}", result)
        records[case] = {
            "confirmation_status": waiting.status,
            "missing_fields": waiting.summary.get("missing_fields"),
            "status": result.status,
            "seconds": round(time.time() - started, 1),
            "run_dir": result.summary.get("run_dir"),
            "estimated_t2_ms": result.summary.get("estimated_t2_ms"),
            "water_configuration": result.summary.get("water_configuration"),
            "spectrum_xlsx": result.summary.get("spectrum_xlsx"),
            "inversion_summary_csv": result.summary.get("summary_csv"),
            "config": result.summary.get("config"),
            "stage_status": result.summary.get("stage_status"),
        }
    return records


def run_ct(out: Path) -> dict:
    image = ROOT / "testData" / "ct_tif" / "solid_water_air_back4phase.tif"
    context = AgentRuntimeContext(workspace=out, uploaded_path=image, uploaded_paths=[image])
    context.last_user_goal = "This is NMR experimental decay data from biomass-bearing soil from Vienna. Run the T2 inversion with the L-curve choosing the smoothing factor automatically, then fit a two-peak Gaussian decomposition and interpret the result"
    inspected = execute_agent_tool("inspect_ct_phase_image", {}, context)
    log("ct:inspect", inspected)
    confirm_phase_assignment(context, dict(context.ct_state["assignment"]))
    confirm_run_parameters(context, {"pixel_size_um": 4.6, "run_lcurve": True, "run_gaussian": True, "peak_count": 2})
    started = time.time()
    result = execute_agent_tool("run_ct_simulation_workflow", {}, context)
    log("ct:run", result)
    return {
        "input": str(image),
        "assignment": context.ct_state.get("assignment"),
        "status": result.status,
        "seconds": round(time.time() - started, 1),
        "run_dir": result.summary.get("run_dir"),
        "decay": result.summary.get("decay"),
        "mesh": result.summary.get("mesh"),
        "stage_status": result.summary.get("stage_status"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ROOT / "outputs" / "showcase"))
    parser.add_argument("--skip-ct", action="store_true")
    parser.add_argument("--index-only", help="rewrite README.md and the categories of an existing output folder")
    args = parser.parse_args()
    if args.index_only:
        out = Path(args.index_only)
        summary = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        for item in summary["files"]:
            item["category"] = classify(Path(item["path"]))
        (out / "manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(write_index(out, summary))
        return
    out = Path(args.out) / datetime.now().strftime("%Y%m%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)

    summary = {"created": datetime.now().isoformat(timespec="seconds")}
    summary["01_measured_inversion"] = run_measured(out / "01_measured_inversion")
    summary["02_ideal_structure"] = run_ideal(out / "02_ideal_structure")
    if not args.skip_ct:
        summary["03_ct_image"] = run_ct(out / "03_ct_image")

    files = []
    for path in sorted(p for p in out.rglob("*") if p.is_file()):
        relative = path.relative_to(out)
        parts = relative.parts
        files.append({
            "path": str(relative).replace("\\", "/"),
            "usage": parts[0],
            "case": parts[1] if parts[0] == "02_ideal_structure" and len(parts) > 2 else None,
            "category": classify(relative),
            "bytes": path.stat().st_size,
        })
    summary["files"] = files
    (out / "manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_index(out, summary)
    print(f"Outputs: {out}")


USAGE_TITLES = {
    "01_measured_inversion": "Usage 1: measured decay data -> T2 inversion",
    "02_ideal_structure": "Usage 2: ideal structure -> simulation -> inversion",
    "03_ct_image": "Usage 3: segmented CT image -> simulation -> inversion",
}


def _link(path: str) -> str:
    return f"[{Path(path).name}]({path.replace(' ', '%20')})"


def _literature_block(interpretation: Path) -> list[str]:
    text = interpretation.read_text(encoding="utf-8")
    # The heading depends on the report language (Chinese or English).
    starts = [i for i in (text.find("## 文献依据的解释"), text.find("## Literature-Based Interpretation")) if i >= 0]
    start = min(starts) if starts else -1
    ends = [i for i in (text.find("## 需要注意"), text.find("## Points to note")) if i > start]
    end = min(ends) if ends else -1
    if start < 0:
        return []
    block = text[start:end if end > start else None].strip().splitlines()
    return ["#" + line if line.startswith("## ") else line for line in block]


def _peaks(spectrum_xlsx: str | None) -> list[float]:
    import pandas as pd

    from t2_agent.literature import spectrum_peaks

    if not spectrum_xlsx or not Path(spectrum_xlsx).exists():
        return []
    table = next(iter(pd.read_excel(spectrum_xlsx, sheet_name=None).values()))
    return spectrum_peaks(table["t2_ms"].to_numpy(float), table["amplitude"].to_numpy(float))


def _alpha(summary_csv: str | None) -> float | None:
    import pandas as pd

    if not summary_csv or not Path(summary_csv).exists():
        return None
    row = pd.read_csv(summary_csv).iloc[0]
    return float(row.get("best_regularization", row.get("regularization")))


def write_index(out: Path, summary: dict) -> Path:
    """English index: what each usage produced, filed by stage, with the interpretations."""

    files = summary["files"]
    lines = [
        "# Agent example run index",
        "",
        f"Generated: {summary['created']}. All three usages run through the same whitelisted tools the web agent calls (no language model involved).",
        "The file classification rules are in `CATEGORIES` in `scripts/run_showcase_examples.py`; the full list is in `manifest.json`.",
        "",
    ]
    for usage, title in USAGE_TITLES.items():
        usage_files = [item for item in files if item["usage"] == usage]
        if not usage_files:
            continue
        lines += [f"## {title}", ""]
        if usage == "01_measured_inversion":
            lines += [f"Input: `{Path(summary[usage]['input']).name}`; steps: " + " → ".join(step["tool"] for step in summary[usage]["steps"]), ""]
        if usage == "02_ideal_structure":
            lines += [
                "Each case first returns \"waiting for parameter confirmation\" and runs only after confirmation; default geometry: large pore side 20 μm, small pore 8 μm, throat 5 × 1 μm, D = 2 μm²/ms, T2,bulk = 3000 ms, ρ = 0.005 μm/ms.",
                "",
                "| Case | Coupled | Sw (large/small) | Water configuration | Fast-diffusion T2 estimate (large/small, ms) | Inverted peak positions (ms) | α |",
                "|---|---|---|---|---|---|---|",
            ]
            for case, record in summary[usage].items():
                config = record.get("config") or {}
                estimate = record.get("estimated_t2_ms") or {}
                names = {"full": "fully saturated", "bubble": "central bubble", "corner": "corner water"}
                water = {pore: names.get(kind, kind) for pore, kind in (record.get("water_configuration") or {}).items()}
                peaks = ", ".join(f"{p:.0f}" for p in _peaks(record.get("spectrum_xlsx"))) or "—"
                alpha = _alpha(record.get("inversion_summary_csv"))
                lines.append(
                    f"| {case} | {'yes' if config.get('coupled') else 'no'} | {config.get('large_water_saturation', 1):.2f} / {config.get('small_water_saturation', 1):.2f} | "
                    f"{water.get('large', '')} / {water.get('small', '')} | {estimate.get('large', float('nan')):.0f} / {estimate.get('small', float('nan')):.0f} | {peaks} | "
                    + (f"{alpha:.3g}" if alpha is not None else "—")
                    + " |"
                )
            lines.append("")
        if usage == "03_ct_image":
            record = summary[usage]
            decay = record.get("decay") or {}
            mesh = record.get("mesh") or {}
            lines += [
                f"Input: `{Path(record['input']).name}` (4.6 μm/pixel, with background); phases: " + ", ".join(f"{value}->{phase}" for value, phase in (record.get("assignment") or {}).items()),
                f"Mesh: {mesh.get('mesh_nodes')} nodes / {mesh.get('mesh_triangles')} triangles; fast-diffusion T2 estimate ≈ {decay.get('estimated_t2_ms', float('nan')):.0f} ms; simulated {decay.get('t_max_ms')} ms; run time {record.get('seconds')} s.",
                "",
            ]

        cases = sorted({item["case"] for item in usage_files if item["case"]}) or [None]
        for case in cases:
            subset = [item for item in usage_files if item["case"] == case]
            if case:
                lines += [f"### {case}", ""]
            lines += ["| Category | Files | Representative files |", "|---|---|---|"]
            for key, label in CATEGORY_LABELS.items():
                group = [item for item in subset if item["category"] == key]
                if not group:
                    continue
                shown = [item for item in group if item["path"].endswith((".png", ".md"))][:3] or group[:2]
                lines.append(f"| {label} | {len(group)} | " + "<br>".join(_link(item["path"]) for item in shown) + " |")
            lines.append("")
            interpretation = next((out / item["path"] for item in subset if item["category"] == "interpretation" and item["path"].endswith(".md")), None)
            if interpretation is not None:
                lines += _literature_block(interpretation) + [""]
    index = out / "README.md"
    index.write_text("\n".join(lines), encoding="utf-8")
    return index


if __name__ == "__main__":
    main()
