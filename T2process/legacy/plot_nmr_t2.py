"""CLI entry point for standardized paired plotting workflow.

The script reads one raw-decay workbook and one spectrum workbook, then
generates a figure for each common signal sheet.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from nmr_t2 import run_plotting_workbook_pair


DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "Example data"
DEFAULT_RAW = DEFAULT_DATA_DIR / "SimulationDecay.xlsx"


def main() -> None:
    """Generate standardized raw-vs-spectrum figures."""

    parser = argparse.ArgumentParser(description="Standardized plotting pipeline for raw decay and T2 spectrum.")
    parser.add_argument("--raw-file", type=Path, default=DEFAULT_RAW, help="Raw decay workbook path.")
    parser.add_argument("--spectrum-file", type=Path, required=True, help="Spectrum workbook path.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory where figures will be saved.")
    parser.add_argument("--time-to-ms-scale", type=float, default=1000.0, help="Time scaling factor to milliseconds.")

    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir is not None else (args.spectrum_file.parent / "plots_standard")

    figure_map = run_plotting_workbook_pair(
        raw_decay_workbook=args.raw_file,
        spectrum_workbook=args.spectrum_file,
        output_dir=output_dir,
        time_to_ms_scale=float(args.time_to_ms_scale),
    )

    print("Plotting workflow completed.")
    print(f"Generated {len(figure_map)} figure(s).")
    for signal_name, figure_path in figure_map.items():
        print(f"- {signal_name}: {figure_path}")


if __name__ == "__main__":
    main()
