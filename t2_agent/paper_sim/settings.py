"""Physical, acquisition and inversion settings (Table 1 of the manuscript)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np


@dataclass(frozen=True)
class PaperSettings:
    """Physical parameters and the T2 echo train shared by all controlled cases."""

    diffusion_um2_per_ms: float = 2.0
    t1_bulk_ms: float = 3000.0
    t2_bulk_ms: float = 3000.0
    rho1_um_per_ms: float = 0.005
    rho2_um_per_ms: float = 0.005
    echo_ms: float = 3.4907
    t2_sample_count: int = 1501
    maximum_triangle_area_um2: float = 0.05
    mesh_quality: float = 28.0

    def validate(self) -> None:
        positive = {
            "diffusion_um2_per_ms": self.diffusion_um2_per_ms,
            "t1_bulk_ms": self.t1_bulk_ms,
            "t2_bulk_ms": self.t2_bulk_ms,
            "echo_ms": self.echo_ms,
            "maximum_triangle_area_um2": self.maximum_triangle_area_um2,
        }
        bad = [name for name, value in positive.items() if value <= 0.0]
        if bad:
            raise ValueError(f"Settings must be positive: {bad}")
        if self.rho1_um_per_ms < 0.0 or self.rho2_um_per_ms < 0.0:
            raise ValueError("Surface relaxivities cannot be negative")
        if self.t2_sample_count < 2:
            raise ValueError("At least two echoes are required")

    @property
    def t2_times_ms(self) -> np.ndarray:
        return self.echo_ms * np.arange(self.t2_sample_count, dtype=float)

    def as_dict(self) -> dict:
        values = asdict(self)
        values["equation"] = (
            "M dm/dt = -(D K + rho R + M/T_bulk) m; Robin surface relaxation on "
            "solid-water edges only, no flux on water-air edges"
        )
        values["receiver"] = "water-domain integral 1^T M m"
        return values


@dataclass(frozen=True)
class DT2Acquisition:
    """Narrow-pulse PFG encoding followed by transverse detection."""

    b_values_ms_per_um2: tuple[float, ...] = (
        0.0, 0.001, 0.001976211095535186, 0.003905246984744,
        0.007719070806, 0.01526417967, 0.03017088168, 0.05963623317,
        0.1178768635, 0.2329951811, 0.460665797, 0.910298177,
        1.798870916, 3.556480306,
    )
    te_min_ms: float = 25.0
    te_max_ms: float = 1300.0
    te_count: int = 24
    diffusion_time_ms: float = 20.0
    maximum_time_step_ms: float = 1.0
    gradient_axis: str = "y"

    @property
    def b_axis(self) -> np.ndarray:
        return np.asarray(self.b_values_ms_per_um2, dtype=float)

    @property
    def te_axis_ms(self) -> np.ndarray:
        return np.geomspace(self.te_min_ms, self.te_max_ms, self.te_count)

    def validate(self) -> None:
        if self.gradient_axis not in {"x", "y"}:
            raise ValueError("gradient_axis must be x or y")
        if self.diffusion_time_ms <= 0 or self.maximum_time_step_ms <= 0:
            raise ValueError("Diffusion time and time step must be positive")
        if self.te_min_ms < self.diffusion_time_ms:
            raise ValueError("Minimum TE must not precede the second narrow pulse")
        if any(value < 0 for value in self.b_values_ms_per_um2):
            raise ValueError("b values cannot be negative")

    def as_dict(self) -> dict:
        result = asdict(self)
        result["b_values_ms_per_um2"] = list(self.b_values_ms_per_um2)
        result["te_axis_ms"] = self.te_axis_ms.tolist()
        result["sequence"] = "instantaneous +q pulse; diffusion; instantaneous -q pulse; T2 detection"
        result["b_definition"] = "b = q^2 * diffusion_time (narrow-pulse approximation)"
        return result


@dataclass(frozen=True)
class T1T2Acquisition:
    """Ideal saturation, spatial T1 recovery, then transverse detection."""

    recovery_min_ms: float = 1.0
    recovery_max_ms: float = 12000.0
    recovery_count: int = 24
    detection_min_ms: float = 3.4907
    detection_max_ms: float = 1300.0
    detection_count: int = 24
    maximum_time_step_ms: float = 2.0

    @property
    def recovery_times_ms(self) -> np.ndarray:
        return np.r_[0.0, np.geomspace(self.recovery_min_ms, self.recovery_max_ms, self.recovery_count)]

    @property
    def detection_times_ms(self) -> np.ndarray:
        return np.geomspace(self.detection_min_ms, self.detection_max_ms, self.detection_count)

    def validate(self) -> None:
        if min(self.recovery_min_ms, self.detection_min_ms, self.maximum_time_step_ms) <= 0:
            raise ValueError("Acquisition times must be positive")
        if self.recovery_max_ms <= self.recovery_min_ms:
            raise ValueError("Recovery maximum must exceed minimum")
        if self.detection_max_ms <= self.detection_min_ms:
            raise ValueError("Detection maximum must exceed minimum")

    def as_dict(self) -> dict:
        result = asdict(self)
        result["recovery_times_ms"] = self.recovery_times_ms.tolist()
        result["detection_times_ms"] = self.detection_times_ms.tolist()
        result["sequence"] = "ideal saturation; spatial T1 recovery; ideal transfer; spatial T2 detection"
        result["kernel"] = "(1 - exp(-TR/T1)) * exp(-TE/T2)"
        return result


@dataclass(frozen=True)
class InversionGrids:
    """Inversion grids and regularization of the controlled cases (Table 1)."""

    t2_min_ms: float = 3.0
    t2_max_ms: float = 5000.0
    t2_bins: int = 140
    t2_alpha: float = 0.08
    dt2_d_min: float = 1.0e-3
    dt2_d_max: float = 3.0
    dt2_d_bins: int = 32
    dt2_t2_min_ms: float = 10**0.5
    dt2_t2_max_ms: float = 10**3.5
    dt2_t2_bins: int = 40
    t1t2_t1_min_ms: float = 10.0
    t1t2_t1_max_ms: float = 20000.0
    t1t2_t1_bins: int = 32
    t1t2_t2_min_ms: float = 3.0
    t1t2_t2_max_ms: float = 5000.0
    t1t2_t2_bins: int = 32
    two_d_alpha: float = 0.025

    @property
    def t2_axis_ms(self) -> np.ndarray:
        return np.geomspace(self.t2_min_ms, self.t2_max_ms, self.t2_bins)

    @property
    def d_axis(self) -> np.ndarray:
        return np.geomspace(self.dt2_d_min, self.dt2_d_max, self.dt2_d_bins)

    @property
    def dt2_t2_axis_ms(self) -> np.ndarray:
        return np.geomspace(self.dt2_t2_min_ms, self.dt2_t2_max_ms, self.dt2_t2_bins)

    @property
    def t1_axis_ms(self) -> np.ndarray:
        return np.geomspace(self.t1t2_t1_min_ms, self.t1t2_t1_max_ms, self.t1t2_t1_bins)

    @property
    def t1t2_t2_axis_ms(self) -> np.ndarray:
        return np.geomspace(self.t1t2_t2_min_ms, self.t1t2_t2_max_ms, self.t1t2_t2_bins)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExchangeSettings:
    """Effective two-compartment exchange of the dual-pore case (Section 3.2)."""

    exchange_length_um: float = 5.0
    effective_diffusion_um2_per_ms: float = 1.667
    time_step_ms: float = 2.0
    extra: dict = field(default_factory=dict)

    @property
    def k_ex_per_ms(self) -> float:
        return self.effective_diffusion_um2_per_ms / self.exchange_length_um**2
