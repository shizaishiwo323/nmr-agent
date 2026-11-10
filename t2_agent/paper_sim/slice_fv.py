"""Finite-volume pixel-grid T2 solver of the segmented CT slice (Section 3.2).

Surface relaxation is applied on every water face against glass, background or
the image edge; water-air faces carry no surface term. Implicit Euler in time.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage
from scipy.sparse import csr_matrix, diags, eye
from scipy.sparse.linalg import factorized


@dataclass(frozen=True)
class SliceSettings:
    pixel_size_um: float = 4.6
    diffusion_um2_per_ms: float = 2.0
    t2_bulk_ms: float = 3000.0
    rho_um_per_ms: float = 0.005
    dt_ms: float = 5.0
    t_max_ms: float = 1500.0
    solid_value: int = 255
    water_value: int = 102
    air_value: int = 153
    outside_value: int = 0
    smooth_radius_px: int = 2
    interface_sigma_px: float = 1.25
    t2_bins: int = 150
    t2_log_step: float = 4.0 / 119.0  # original 120-bin spacing over 1-1e4 ms

    @property
    def times_ms(self) -> np.ndarray:
        return np.arange(0.0, self.t_max_ms, self.dt_ms)

    @property
    def t2_axis_ms(self) -> np.ndarray:
        return 10 ** (np.arange(self.t2_bins) * self.t2_log_step)


def classify_and_clean(raw: np.ndarray, settings: SliceSettings) -> np.ndarray:
    """Snap unknown labels to the nearest phase value and smooth the interfaces."""

    solid, water, air, outside = settings.solid_value, settings.water_value, settings.air_value, settings.outside_value
    valid = np.array([outside, water, air, solid], dtype=np.int16)
    cleaned = raw.astype(np.int16).copy()
    for value in np.unique(cleaned):
        if value in valid:
            continue
        cleaned[cleaned == value] = int(valid[int(np.argmin(np.abs(valid - int(value))))])
    if settings.interface_sigma_px > 0:
        outside_mask = cleaned == outside
        internal = [solid, water, air]
        scores = [ndimage.gaussian_filter((cleaned == value).astype(float), sigma=settings.interface_sigma_px, mode="nearest") for value in internal]
        smoothed = np.asarray(internal, dtype=np.uint8)[np.argmax(np.stack(scores, axis=0), axis=0)]
        smoothed[outside_mask] = outside
        cleaned = smoothed.astype(np.int16)
    radius = int(settings.smooth_radius_px)
    if radius > 0:
        structure = np.ones((radius + 1, radius + 1))
        water_mask = ndimage.binary_closing(ndimage.binary_opening(cleaned == water, structure=structure), structure=structure)
        solid_mask = ndimage.binary_closing(cleaned == solid, structure=structure)
        outside_mask = cleaned == outside
        air_mask = cleaned == air
        cleaned2 = np.full(cleaned.shape, air, dtype=np.int16)
        cleaned2[outside_mask] = outside
        cleaned2[solid_mask] = solid
        cleaned2[water_mask & ~solid_mask & ~outside_mask] = water
        cleaned2[air_mask & ~solid_mask & ~outside_mask & ~water_mask] = air
        cleaned = cleaned2
    return cleaned.astype(np.uint8)


def build_water_operator(labels: np.ndarray, settings: SliceSettings):
    """Graph Laplacian of the water pixels and the surface sink per pixel."""

    water = labels == settings.water_value
    index = -np.ones(labels.shape, dtype=int)
    coords = np.argwhere(water)
    index[water] = np.arange(coords.shape[0])
    n = coords.shape[0]
    if n == 0:
        raise ValueError("No water pixels found in the cleaned image.")
    rows, cols, data = [], [], []
    boundary_counts = np.zeros(n, dtype=float)
    for k, (r, c) in enumerate(coords):
        degree = boundary = 0
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = r + dr, c + dc
            if rr < 0 or cc < 0 or rr >= labels.shape[0] or cc >= labels.shape[1]:
                boundary += 1
                continue
            if water[rr, cc]:
                rows.append(k)
                cols.append(index[rr, cc])
                data.append(-1.0)
                degree += 1
            elif labels[rr, cc] in (settings.solid_value, settings.outside_value):
                boundary += 1
        rows.append(k)
        cols.append(k)
        data.append(float(degree))
        boundary_counts[k] = boundary
    laplacian = csr_matrix((data, (rows, cols)), shape=(n, n))
    sink = boundary_counts / settings.pixel_size_um
    return coords, laplacian, sink


def solve_decay(laplacian, sink, settings: SliceSettings) -> np.ndarray:
    """Normalized water signal on ``settings.times_ms``."""

    n = laplacian.shape[0]
    dt = settings.dt_ms
    lhs = (
        eye(n, format="csr")
        + laplacian * (settings.diffusion_um2_per_ms * dt / settings.pixel_size_um**2)
        + eye(n, format="csr") * (dt / settings.t2_bulk_ms)
        + diags(settings.rho_um_per_ms * dt * sink, format="csr")
    )
    solve = factorized(lhs.tocsc())
    u = np.ones(n, dtype=float)
    amplitudes = []
    for _ in settings.times_ms:
        amplitudes.append(float(np.sum(u)))
        u = solve(u)
    amplitudes = np.asarray(amplitudes)
    return amplitudes / amplitudes[0]


def phase_statistics(labels: np.ndarray, settings: SliceSettings) -> dict[str, float]:
    water = labels == settings.water_value
    air = labels == settings.air_value
    inside = labels != settings.outside_value
    pore = water | air
    return {
        "porosity_2d": float(pore.sum() / max(inside.sum(), 1)),
        "water_saturation": float(water.sum() / max(pore.sum(), 1)),
        "water_pixels": int(water.sum()),
        "air_pixels": int(air.sum()),
        "solid_pixels": int((labels == settings.solid_value).sum()),
        "outside_pixels": int((labels == settings.outside_value).sum()),
    }


def local_thickness_um(labels: np.ndarray, settings: SliceSettings, phase: str = "pore") -> np.ndarray:
    """Local diameter (largest inscribed disc) of every pixel of the pore space or of the water phase."""

    from skimage.morphology import medial_axis

    water = labels == settings.water_value
    pore = water | (labels == settings.air_value) if phase == "pore" else water
    skeleton, distance = medial_axis(pore, return_distance=True, rng=0)
    thickness = np.zeros(labels.shape, float)
    for yy, xx in np.argwhere(skeleton):
        radius = distance[yy, xx]
        n = int(np.ceil(radius))
        y0, y1 = max(0, yy - n), min(labels.shape[0], yy + n + 1)
        x0, x1 = max(0, xx - n), min(labels.shape[1], xx + n + 1)
        yg, xg = np.ogrid[y0:y1, x0:x1]
        mask = (yg - yy) ** 2 + (xg - xx) ** 2 <= radius**2
        block = thickness[y0:y1, x0:x1]
        np.maximum(block, np.where(mask, 2 * radius, 0), out=block)
    return thickness[pore] * settings.pixel_size_um
