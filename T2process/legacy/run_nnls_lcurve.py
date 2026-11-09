"""CLI entry point for standardized L-curve inversion workflow.

This script supports both single-file and batch-folder processing while
delegating implementation to `nmr_t2.pipelines.run_lcurve_workbook`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from nmr_t2 import LCurveConfig, run_lcurve_workbook


DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "Example data"
DEFAULT_INPUT = DEFAULT_DATA_DIR / "SimulationDecay.xlsx"


def _discover_input_files(input_dir: Path, pattern: str) -> list[Path]:
    """Discover batch input files using a glob pattern."""

    return sorted(file_path for file_path in input_dir.glob(pattern) if file_path.is_file())


def main() -> None:
    """Run L-curve inversion in single-file or batch mode."""

    parser = argparse.ArgumentParser(description="Standardized L-curve inversion pipeline.")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--input", type=Path, default=None, help="Single-file mode: one decay workbook.")
    mode_group.add_argument("--input-dir", type=Path, default=None, help="Batch mode: directory containing decay workbooks.")

    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for standardized outputs.")
    parser.add_argument("--pattern", type=str, default="*.xlsx", help="Batch mode glob pattern.")
    parser.add_argument("--time-to-ms-scale", type=float, default=1000.0, help="Time scaling factor to milliseconds.")
    parser.add_argument("--num-bins", type=int, default=200, help="Number of logarithmic T2 bins.")
    parser.add_argument("--t2-min-ms", type=float, default=1e-2, help="Minimum T2 (ms).")
    parser.add_argument("--t2-max-ms", type=float, default=1e5, help="Maximum T2 (ms).")
    parser.add_argument("--alpha-min", type=float, default=1e-6, help="Minimum alpha in log scan.")
    parser.add_argument("--alpha-max", type=float, default=1e2, help="Maximum alpha in log scan.")
    parser.add_argument("--alpha-count", type=int, default=60, help="Number of alpha candidates.")
    parser.add_argument("--min-points-after-trim", type=int, default=10, help="Minimum point count required after trimming.")
    parser.add_argument(
        "--disable-peak-trim",
        action="store_true",
        help="Disable pre-peak trimming and use the full sorted signal.",
    )

    args = parser.parse_args()

    config = LCurveConfig(
        num_bins=int(args.num_bins),
        t2_min_ms=float(args.t2_min_ms),
        t2_max_ms=float(args.t2_max_ms),
        alpha_min=float(args.alpha_min),
        alpha_max=float(args.alpha_max),
        alpha_count=int(args.alpha_count),
        min_points_after_trim=int(args.min_points_after_trim),
    )

    if args.input_dir is not None:
        if not args.input_dir.exists() or not args.input_dir.is_dir():
            raise NotADirectoryError(f"Invalid input directory: {args.input_dir}")

        files = _discover_input_files(args.input_dir, args.pattern)
        if not files:
            raise FileNotFoundError(f"No files match pattern '{args.pattern}' in {args.input_dir}")

        output_root = args.output_dir if args.output_dir is not None else (args.input_dir / "outputs_standard")
        print(f"Found {len(files)} file(s) for batch L-curve inversion.")

        success_count = 0
        for file_path in files:
            try:
                per_file_output_dir = output_root / file_path.stem
                results = run_lcurve_workbook(
                    input_workbook=file_path,
                    output_dir=per_file_output_dir,
                    config=config,
                    time_to_ms_scale=float(args.time_to_ms_scale),
                    trim_from_peak=not bool(args.disable_peak_trim),
                )
                success_count += 1
                print(f"[OK] {file_path.name}")
                for key, value in results.items():
                    print(f"    - {key}: {value}")
            except Exception as exc:
                print(f"[FAILED] {file_path.name}: {exc}")

        print(f"Batch completed: {success_count}/{len(files)} succeeded.")
        return

    input_file = args.input if args.input is not None else DEFAULT_INPUT
    output_dir = args.output_dir if args.output_dir is not None else (input_file.parent / "outputs_standard")
    results = run_lcurve_workbook(
        input_workbook=input_file,
        output_dir=output_dir,
        config=config,
        time_to_ms_scale=float(args.time_to_ms_scale),
        trim_from_peak=not bool(args.disable_peak_trim),
    )

    print("L-curve workflow completed.")
    for key, value in results.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
