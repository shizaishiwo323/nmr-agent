"""CLI entry point for standardized NNLS inversion workflow.

This script is intentionally thin and delegates all heavy lifting to
`nmr_t2.pipelines.run_nnls_workbook`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from nmr_t2 import NnlsConfig, run_nnls_workbook


DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "Example data"
DEFAULT_INPUT = DEFAULT_DATA_DIR / "SimulationDecay.xlsx"


def main() -> None:
    """Run fixed-regularization NNLS inversion for one workbook."""

    parser = argparse.ArgumentParser(description="Standardized NNLS inversion pipeline.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input decay workbook path.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for standardized outputs.")
    parser.add_argument("--time-to-ms-scale", type=float, default=1000.0, help="Time scaling factor to milliseconds.")
    parser.add_argument("--num-bins", type=int, default=200, help="Number of logarithmic T2 bins.")
    parser.add_argument("--regularization", type=float, default=1.0, help="Regularization weight (eps).")
    parser.add_argument("--t2-min-ms", type=float, default=1.0, help="Minimum T2 (ms).")
    parser.add_argument("--t2-max-ms", type=float, default=1e4, help="Maximum T2 (ms).")
    parser.add_argument("--min-points-after-trim", type=int, default=10, help="Minimum point count required after trimming.")
    parser.add_argument(
        "--disable-peak-trim",
        action="store_true",
        help="Disable pre-peak trimming and use the full sorted signal.",
    )

    args = parser.parse_args()

    output_dir = args.output_dir if args.output_dir is not None else (args.input.parent / "outputs_standard")
    config = NnlsConfig(
        num_bins=int(args.num_bins),
        regularization=float(args.regularization),
        t2_min_ms=float(args.t2_min_ms),
        t2_max_ms=float(args.t2_max_ms),
        min_points_after_trim=int(args.min_points_after_trim),
    )

    results = run_nnls_workbook(
        input_workbook=args.input,
        output_dir=output_dir,
        config=config,
        time_to_ms_scale=float(args.time_to_ms_scale),
        trim_from_peak=not bool(args.disable_peak_trim),
    )

    print("NNLS workflow completed.")
    for key, value in results.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
