"""Consistent-mass FEM forward responses on pyGIMLi triangular meshes.

T2 uses a generalized Lanczos evaluation of 1^T M exp(-M^-1 A t) 1; D-T2 and
T1-T2 propagate the spatial magnetization with Crank-Nicolson steps. Ported
from the paper code package without changes to the numerics.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.linalg import eigh_tridiagonal
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import factorized, splu

from .geometry import MARKER_SOLID_WATER
from .settings import DT2Acquisition, PaperSettings, T1T2Acquisition


def _robin_matrix(mesh, rho_um_per_ms: float) -> csr_matrix:
    import pygimli as pg
    import pygimli.utils as pg_utils

    matrix = pg.solver.createMassMatrix(mesh, b=0.0)
    rhs = pg.Vector(mesh.nodeCount(), 0.0)
    if rho_um_per_ms:
        boundaries = pg.solver.parseArgToBoundaries({MARKER_SOLID_WATER: rho_um_per_ms}, mesh)
        pg.solver.assembleRobinBC(matrix, boundaries, rhs=rhs)
    return pg_utils.toCSR(matrix).tocsr()


def consistent_matrices(mesh, settings: PaperSettings):
    """Mass M, transverse A2 = D K + rho2 R + M/T2b and longitudinal A1."""

    import pygimli as pg
    import pygimli.utils as pg_utils

    mass = pg_utils.toCSR(pg.solver.createMassMatrix(mesh, b=1.0)).tocsr()
    stiffness = pg_utils.toCSR(pg.solver.createStiffnessMatrix(mesh, a=settings.diffusion_um2_per_ms)).tocsr()
    transverse = (stiffness + _robin_matrix(mesh, settings.rho2_um_per_ms) + mass / settings.t2_bulk_ms).tocsr()
    longitudinal = (stiffness + _robin_matrix(mesh, settings.rho1_um_per_ms) + mass / settings.t1_bulk_ms).tocsr()
    return mass, transverse, longitudinal


def solve_t2(mesh, settings: PaperSettings, times_ms: np.ndarray | None = None, lanczos_steps: int = 512) -> tuple[np.ndarray, dict]:
    """Normalized T2 decay 1^T M exp(-M^-1 A2 t) 1 / (1^T M 1) and its modes."""

    settings.validate()
    times = settings.t2_times_ms if times_ms is None else np.asarray(times_ms, dtype=float)
    mass, transverse, _ = consistent_matrices(mesh, settings)
    ones = np.ones(mesh.nodeCount(), dtype=float)
    total_mass = float(ones @ (mass @ ones))
    q = ones / math.sqrt(total_mass)
    q_previous = np.zeros_like(q)
    beta_previous = 0.0
    diagonal: list[float] = []
    off_diagonal: list[float] = []
    solve_mass = factorized(mass.tocsc())
    maximum_iterations = min(lanczos_steps, mesh.nodeCount())
    for iteration in range(maximum_iterations):
        aq = transverse @ q
        alpha = float(q @ aq)
        residual = aq - alpha * (mass @ q)
        if iteration:
            residual -= beta_previous * (mass @ q_previous)
        z = solve_mass(residual)
        z -= q * float(q @ (mass @ z))
        if iteration:
            z -= q_previous * float(q_previous @ (mass @ z))
        beta = float(math.sqrt(max(z @ (mass @ z), 0.0)))
        diagonal.append(alpha)
        if beta < 1e-13 or iteration == maximum_iterations - 1:
            break
        off_diagonal.append(beta)
        q_previous, q = q, z / beta
        beta_previous = beta
    try:
        rates, vectors = eigh_tridiagonal(np.asarray(diagonal), np.asarray(off_diagonal), check_finite=False, lapack_driver="stemr")
    except np.linalg.LinAlgError:
        rates, vectors = eigh_tridiagonal(np.asarray(diagonal), np.asarray(off_diagonal), check_finite=False, lapack_driver="stev")
    rates = np.maximum(rates, 0.0)
    weights = np.square(vectors[0])
    weights /= weights.sum()
    signal = weights @ np.exp(-np.outer(rates, times))
    return signal, {
        "method": "consistent-mass FEM, generalized Lanczos",
        "lanczos_steps": len(diagonal),
        "water_area_um2": total_mass,
        "nodes": mesh.nodeCount(),
        "cells": mesh.cellCount(),
        "rate_per_ms": rates,
        "modal_weight": weights,
    }


class _CrankNicolson:
    def __init__(self, mass, operator, maximum_step_ms: float):
        self.mass = mass.tocsr()
        self.operator = operator.tocsr()
        self.maximum_step_ms = maximum_step_ms
        self._cache: dict = {}

    def _step(self, state: np.ndarray, step_ms: float) -> np.ndarray:
        key = round(float(step_ms), 12)
        if key not in self._cache:
            left = (self.mass + 0.5 * step_ms * self.operator).tocsc()
            right = (self.mass - 0.5 * step_ms * self.operator).tocsr()
            self._cache[key] = (splu(left), right)
        factor, right = self._cache[key]
        rhs = right @ state
        if np.iscomplexobj(rhs):
            return factor.solve(np.real(rhs)) + 1j * factor.solve(np.imag(rhs))
        return factor.solve(rhs)

    def evolve(self, state: np.ndarray, duration_ms: float) -> np.ndarray:
        if duration_ms <= 1.0e-14:
            return state
        count = max(1, int(math.ceil(duration_ms / self.maximum_step_ms)))
        step = duration_ms / count
        for _ in range(count):
            state = self._step(state, step)
        return state


def _node_coordinate(mesh, axis: str) -> np.ndarray:
    index = 0 if axis == "x" else 1
    coordinate = np.asarray([node.pos()[index] for node in mesh.nodes()], dtype=float)
    return coordinate - np.mean(coordinate)


def solve_dt2(mesh, settings: PaperSettings, acquisition: DT2Acquisition) -> tuple[np.ndarray, dict]:
    """D-T2 signal S(b, TE), shape (n_b, n_TE), normalized by the water area."""

    settings.validate()
    acquisition.validate()
    mass, transverse, _ = consistent_matrices(mesh, settings)
    propagator = _CrankNicolson(mass, transverse, acquisition.maximum_time_step_ms)
    ones = np.ones(mesh.nodeCount(), dtype=float)
    total_mass = float(ones @ (mass @ ones))
    observer = np.asarray(ones @ mass).ravel()
    coordinate = _node_coordinate(mesh, acquisition.gradient_axis)
    signal = np.empty((len(acquisition.b_axis), len(acquisition.te_axis_ms)))
    for b_index, b_value in enumerate(acquisition.b_axis):
        q_per_um = math.sqrt(b_value / acquisition.diffusion_time_ms)
        state = np.exp(1j * q_per_um * coordinate)
        state = propagator.evolve(state, acquisition.diffusion_time_ms)
        state *= np.exp(-1j * q_per_um * coordinate)
        current_time = acquisition.diffusion_time_ms
        for te_index, echo_time in enumerate(acquisition.te_axis_ms):
            state = propagator.evolve(state, float(echo_time - current_time))
            current_time = float(echo_time)
            signal[b_index, te_index] = float(np.real(observer @ state) / total_mass)
    return signal, {"method": "consistent-mass FEM, Crank-Nicolson, narrow-pulse PFG", "water_area_um2": total_mass,
                    "acquisition": acquisition.as_dict()}


def solve_t1t2(mesh, settings: PaperSettings, acquisition: T1T2Acquisition) -> tuple[np.ndarray, dict]:
    """T1-T2 signal S(TR, TE) from one spatial saturation-recovery sequence."""

    settings.validate()
    acquisition.validate()
    mass, transverse, longitudinal = consistent_matrices(mesh, settings)
    longitudinal_propagator = _CrankNicolson(mass, longitudinal, acquisition.maximum_time_step_ms)
    transverse_propagator = _CrankNicolson(mass, transverse, acquisition.maximum_time_step_ms)
    ones = np.ones(mesh.nodeCount(), dtype=float)
    observer = np.asarray(ones @ mass).ravel()
    total_mass = float(observer @ ones)
    deficit = ones.copy()
    previous_recovery = 0.0
    signal = np.empty((len(acquisition.recovery_times_ms), len(acquisition.detection_times_ms)))
    for recovery_index, recovery_time in enumerate(acquisition.recovery_times_ms):
        deficit = longitudinal_propagator.evolve(deficit, float(recovery_time - previous_recovery))
        previous_recovery = float(recovery_time)
        transverse_state = ones - deficit
        previous_detection = 0.0
        for detection_index, detection_time in enumerate(acquisition.detection_times_ms):
            transverse_state = transverse_propagator.evolve(transverse_state, float(detection_time - previous_detection))
            previous_detection = float(detection_time)
            signal[recovery_index, detection_index] = float(observer @ transverse_state / total_mass)
    return signal, {"method": "consistent-mass FEM, Crank-Nicolson saturation recovery", "water_area_um2": total_mass,
                    "acquisition": acquisition.as_dict()}
