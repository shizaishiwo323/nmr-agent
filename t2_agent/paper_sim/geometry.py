"""Water-domain geometries of the controlled cases.

Boundary marker 1 is a solid-water edge (Robin surface relaxation); marker 2 is
a water-air meniscus (no flux).
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

MARKER_SOLID_WATER = 1
MARKER_WATER_AIR = 2
HALF_CORNER_ANGLE_RAD = math.radians(30.0)  # equilateral corner: 60 degrees


def _mt():
    import pygimli.meshtools as mt

    return mt


def polygon_area(points: np.ndarray) -> float:
    points = np.asarray(points, dtype=float)
    return 0.5 * abs(float(np.sum(points[:, 0] * np.roll(points[:, 1], -1) - points[:, 1] * np.roll(points[:, 0], -1))))


def equilateral_vertices(side_um: float) -> np.ndarray:
    height = side_um * math.sqrt(3.0) / 2.0
    return np.asarray([[0.0, height], [-side_um / 2.0, 0.0], [side_um / 2.0, 0.0]])


def equilateral_area(side_um: float) -> float:
    return math.sqrt(3.0) / 4.0 * side_um**2


# ---------------------------------------------------------------------------
# Equal-area saturated shapes
# ---------------------------------------------------------------------------

SHAPE_NAMES = ("circle", "equilateral_triangle", "right_triangle_30_60_90")
SHAPE_LABELS = {
    "circle": "Circular pore",
    "equilateral_triangle": "Equilateral triangle",
    "right_triangle_30_60_90": "30°, 60°, 90° triangle",
}


def shape_polygons(area_um2: float, circle_vertices: int = 128) -> dict[str, np.ndarray]:
    """Vertex arrays of the three equal-area shapes (as in the paper code)."""

    side = math.sqrt(4.0 * area_um2 / math.sqrt(3.0))
    equilateral = np.asarray([[-side / 2.0, 0.0], [side / 2.0, 0.0], [0.0, side * math.sqrt(3.0) / 2.0]])
    short_leg = math.sqrt(2.0 * area_um2 / math.sqrt(3.0))
    long_leg = math.sqrt(3.0) * short_leg
    right = np.asarray([[0.0, 0.0], [short_leg, 0.0], [0.0, long_leg]])
    factor = 0.5 * circle_vertices * math.sin(2.0 * math.pi / circle_vertices)
    radius = math.sqrt(area_um2 / factor)
    angles = 2.0 * math.pi * np.arange(circle_vertices) / circle_vertices
    circle = np.c_[radius * np.cos(angles), radius * np.sin(angles)]
    return {"circle": circle, "equilateral_triangle": equilateral, "right_triangle_30_60_90": right}


def shape_dimensions(area_um2: float) -> dict[str, dict[str, float]]:
    side = math.sqrt(4.0 * area_um2 / math.sqrt(3.0))
    short_leg = math.sqrt(2.0 * area_um2 / math.sqrt(3.0))
    return {
        "circle": {"radius_um": math.sqrt(area_um2 / math.pi), "perimeter_um": 2.0 * math.sqrt(math.pi * area_um2)},
        "equilateral_triangle": {"side_um": side, "perimeter_um": 3.0 * side},
        "right_triangle_30_60_90": {
            "short_leg_um": short_leg,
            "long_leg_um": math.sqrt(3.0) * short_leg,
            "perimeter_um": short_leg * (3.0 + math.sqrt(3.0)),
        },
    }


def saturated_polygon_geometry(points: np.ndarray):
    """pyGIMLi PLC of a fully water-filled polygon; every edge is solid-water."""

    return _mt().createPolygon(np.asarray(points, dtype=float).tolist(), isClosed=True, marker=1, boundaryMarker=MARKER_SOLID_WATER)


# ---------------------------------------------------------------------------
# Corner water in an equilateral pore
# ---------------------------------------------------------------------------

def corner_factor(theta_deg: float) -> float:
    """Area of one corner wedge divided by r^2 for a 60-degree corner."""

    alpha = HALF_CORNER_ANGLE_RAD
    theta = math.radians(theta_deg)
    return math.cos(theta) * math.cos(alpha + theta) / math.sin(alpha) - (math.pi / 2.0 - alpha - theta)


def corner_water_limits(theta_deg: float, side_um: float = 20.0) -> dict[str, float]:
    """Saturation range in which three separate corner wedges exist.

    The wedges must not reach the mid-points of the walls (adjacent wedges
    would merge); a contact angle at or above 60 degrees leaves no wedge.
    """

    alpha = HALF_CORNER_ANGLE_RAD
    theta = math.radians(theta_deg)
    factor = corner_factor(theta_deg)
    if factor <= 1.0e-12 or math.cos(alpha + theta) <= 0.0:
        return {"max_saturation": 0.0, "factor": factor}
    radius_max = (side_um / 2.0) * math.sin(alpha) / math.cos(alpha + theta)
    max_sw = 3.0 * factor * radius_max**2 / equilateral_area(side_um)
    return {"max_saturation": float(min(max_sw, 1.0)), "factor": factor}


@dataclass
class CornerWater:
    polygons: list[np.ndarray]
    radius_um: float
    contact_length_um: float
    saturation: float
    contact_angle_deg: float
    side_um: float

    @property
    def solid_water_length_um(self) -> float:
        return 6.0 * self.contact_length_um

    @property
    def water_air_length_um(self) -> float:
        total = 0.0
        for polygon in self.polygons:
            arc = polygon[1:]
            total += float(np.sum(np.linalg.norm(np.diff(arc, axis=0), axis=1)))
        return total


def _unit(vector) -> np.ndarray:
    vector = np.asarray(vector, dtype=float)
    return vector / np.linalg.norm(vector)


def corner_water(saturation: float, theta_deg: float = 0.0, side_um: float = 20.0, arc_points: int = 128) -> CornerWater:
    """Three corner wedges holding the water fraction ``saturation`` of the pore.

    The meniscus radius is solved for the given contact angle so that the water
    area equals ``saturation`` times the pore area (the paper's matched-Sw
    construction; theta = 0 gives the saturation series).
    """

    if not 0.0 < saturation < 1.0:
        raise ValueError("Corner water needs 0 < Sw < 1; use the saturated triangle for Sw = 1.")
    limits = corner_water_limits(theta_deg, side_um)
    if limits["max_saturation"] <= 0.0:
        raise ValueError(f"No corner water exists at a contact angle of {theta_deg:g} degrees (dry-corner limit).")
    if saturation > limits["max_saturation"] + 1.0e-9:
        raise ValueError(
            f"Sw = {saturation:.4f} exceeds the corner-water limit {limits['max_saturation']:.4f} for theta = {theta_deg:g} degrees; "
            "above it the wedges merge and the configuration is no longer corner water."
        )
    alpha = HALF_CORNER_ANGLE_RAD
    theta = math.radians(theta_deg)
    total_area = equilateral_area(side_um)
    radius = math.sqrt(saturation * total_area / (3.0 * limits["factor"]))
    contact = radius * math.cos(alpha + theta) / math.sin(alpha)
    center_distance = radius * math.cos(theta) / math.sin(alpha)
    vertices = equilateral_vertices(side_um)
    interior = vertices.mean(axis=0)
    polygons = []
    for corner, a1, a2 in ((vertices[0], vertices[1], vertices[2]), (vertices[1], vertices[0], vertices[2]), (vertices[2], vertices[0], vertices[1])):
        p1 = corner + contact * _unit(a1 - corner)
        p2 = corner + contact * _unit(a2 - corner)
        center = corner + center_distance * _unit(interior - corner)
        start = math.atan2(*(p1 - center)[::-1])
        end = math.atan2(*(p2 - center)[::-1])
        if end - start > math.pi:
            end -= 2.0 * math.pi
        elif start - end > math.pi:
            end += 2.0 * math.pi
        steps = np.linspace(start, end, arc_points)
        arc = center + radius * np.c_[np.cos(steps), np.sin(steps)]
        polygons.append(np.vstack([corner, arc]))
    return CornerWater(polygons, radius, contact, saturation, theta_deg, side_um)


def corner_water_geometry(water: CornerWater):
    """PLC with solid-water wall segments (marker 1) and no-flux menisci (marker 2)."""

    mt = _mt()
    geometry = None
    for points in water.polygons:
        corner = points[0]
        polygon = mt.createPolygon(points.tolist(), isClosed=True, marker=1, boundaryMarker=MARKER_WATER_AIR)
        for boundary in polygon.boundaries():
            positions = np.asarray([[node.x(), node.y()] for node in boundary.nodes()], dtype=float)
            if np.any(np.linalg.norm(positions - corner, axis=1) < 1.0e-10):
                boundary.setMarker(MARKER_SOLID_WATER)
        geometry = polygon if geometry is None else geometry + polygon
    return geometry


def water_polygons(saturation: float, theta_deg: float, side_um: float, arc_points: int = 128) -> list[np.ndarray]:
    """Polygons for drawing: the full triangle at Sw = 1, otherwise the wedges."""

    if saturation >= 1.0 - 1.0e-12:
        return [equilateral_vertices(side_um)]
    return corner_water(saturation, theta_deg, side_um, arc_points).polygons


def build_mesh(geometry, maximum_area_um2: float, quality: float = 28.0):
    mesh = _mt().createMesh(geometry, quality=quality, area=maximum_area_um2)
    return mesh


def mesh_area(mesh) -> float:
    return float(np.sum(np.asarray(mesh.cellSizes())))
