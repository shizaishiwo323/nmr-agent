from pathlib import Path

import numpy as np
import pandas as pd

from T2process.nmr_t2 import LCurveConfig, NnlsConfig, run_lcurve_workbook, run_nnls_workbook


def _write_decay_workbook(path: Path) -> None:
    time_ms = np.linspace(0.2, 80.0, 160)
    decay = 100.0 * np.exp(-time_ms / 18.0) + 8.0 * np.exp(-time_ms / 3.0)
    pd.DataFrame({"time_ms": time_ms, "signal": decay}).to_excel(path, index=False)


def _assert_fit_export(path: Path) -> None:
    frame = pd.read_excel(path)
    assert list(frame.columns) == [
        "fit_time_ms",
        "decay_amplitude",
        "fit_amplitude",
        "noise_amplitude",
        "residual",
    ]
    np.testing.assert_allclose(frame["decay_amplitude"], frame["fit_amplitude"] + frame["noise_amplitude"])
    np.testing.assert_allclose(frame["noise_amplitude"], frame["residual"])


def _assert_trimmed_export(path: Path) -> None:
    frame = pd.read_excel(path)
    assert "trimmed_fit_amplitude" in frame
    assert "trimmed_inversion_noise" in frame
    assert frame["trimmed_fit_amplitude"].notna().all()
    assert frame["trimmed_inversion_noise"].notna().all()


def test_nnls_and_lcurve_export_decay_fit_and_noise(tmp_path: Path) -> None:
    source = tmp_path / "decay.xlsx"
    _write_decay_workbook(source)

    nnls = run_nnls_workbook(
        source,
        tmp_path / "nnls",
        config=NnlsConfig(num_bins=30, regularization=1.0),
        trim_from_peak=False,
    )
    lcurve = run_lcurve_workbook(
        source,
        tmp_path / "lcurve",
        config=LCurveConfig(num_bins=30, alpha_min=1e-3, alpha_max=1e1, alpha_count=5),
        trim_from_peak=False,
    )

    _assert_fit_export(nnls["fit_xlsx"])
    _assert_fit_export(lcurve["fit_xlsx"])
    _assert_trimmed_export(nnls["trimmed_xlsx"])
    _assert_trimmed_export(lcurve["trimmed_xlsx"])
