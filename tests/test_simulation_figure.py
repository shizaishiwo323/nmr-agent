import numpy as np
import pytest

import t2_agent.tools  # noqa: F401  (puts T2process on sys.path)
from t2_agent import simulation_figure as sf
from t2_agent.ideal_workflow import IdealRunConfig


def test_local_diameter_of_a_disk_and_a_slab():
    yy, xx = np.mgrid[0:121, 0:121]
    disk = (yy - 60) ** 2 + (xx - 60) ** 2 <= 40**2
    thickness = sf.local_diameter_px(disk)
    assert np.median(thickness[disk]) == pytest.approx(80, abs=3)

    slab = np.zeros((60, 200), dtype=bool)
    slab[20:40, :] = True  # 20 px wide channel
    thickness = sf.local_diameter_px(slab)
    assert np.median(thickness[slab]) == pytest.approx(20, abs=2)


def test_ideal_rasterization_matches_saturation():
    for sw in (1.0, 0.7, 0.3):
        config = IdealRunConfig(large_water_saturation=sw, small_water_saturation=sw, coupled=False)
        phase, pixel = sf.rasterize_ideal_geometry(config)
        water = np.count_nonzero(phase == sf.WATER)
        pore = np.count_nonzero((phase == sf.WATER) | (phase == sf.AIR))
        assert water / pore == pytest.approx(sw, abs=0.03)
        assert pixel > 0


def test_spectrum_window_keeps_the_peak_and_estimates():
    t2 = np.logspace(-2, 5, 200)
    spectrum = np.exp(-((np.log10(t2) - np.log10(300.0)) / 0.1) ** 2)
    lo, hi = sf.spectrum_window(t2, spectrum, [77.0])
    assert lo <= 7.7 and hi >= 3000 and lo >= t2.min() and hi <= t2.max()


def test_figure_builds_for_an_ideal_case(tmp_path):
    t2 = np.logspace(-2, 5, 120)
    series = {
        "time_ms": np.linspace(0, 1000, 201),
        "signal": np.exp(-np.linspace(0, 1000, 201) / 300.0),
        "recon_time_ms": np.linspace(0, 1000, 50),
        "recon_signal": np.exp(-np.linspace(0, 1000, 50) / 300.0),
        "t2_ms": t2,
        "spectrum": np.exp(-((np.log10(t2) - np.log10(300.0)) / 0.1) ** 2),
        "alpha": 1e-4,
    }
    data = sf.ideal_figure_data(IdealRunConfig(large_water_saturation=0.7, small_water_saturation=0.7).to_dict(), series, {"large": 356.0, "small": 153.0})
    path = sf.save_simulation_figure(data, tmp_path / "fig.png", dpi=80)
    assert path.stat().st_size > 0
    assert data.water_diameter_um.size < data.pore_diameter_um.size
