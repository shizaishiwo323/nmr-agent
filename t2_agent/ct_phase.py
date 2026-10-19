"""Segmented CT label images (TIF) -> phase assignment -> 2D NMR simulation input.

A segmented CT slice stores one integer label per material phase, for example
``0 = outside``, ``102 = water``, ``153 = air`` and ``255 = solid``. The label
values are arbitrary, so the agent first proposes an assignment (the "AI first
guess"), the user verifies or corrects it with draggable markers on a preview,
and only the confirmed assignment is converted to the internal simulation
labels used by :mod:`t2_agent.simulation_2d`.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
from matplotlib.collections import LineCollection
from PIL import Image
from scipy import ndimage

from .simulation_2d import AIR, OUTSIDE, SOLID, WATER, Simulation2DParams, timestamped_name, xy_to_row_col


CT_SUFFIXES = {".tif", ".tiff"}
PHASES = ("solid", "water", "air", "background")
PHASE_TO_LABEL = {"background": OUTSIDE, "water": WATER, "solid": SOLID, "air": AIR}
PHASE_COLORS = {
    "solid": (245, 197, 24),
    "water": (220, 38, 38),
    "air": (56, 152, 255),
    "background": (30, 30, 30),
}
PHASE_NAMES = {
    "中文": {"solid": "固相", "water": "水相（液）", "air": "气相（空气）", "background": "背景/外部"},
    "English": {"solid": "Solid", "water": "Water (liquid)", "air": "Air (gas)", "background": "Background"},
}
PHASE_SHORT = {
    "中文": {"solid": "固", "water": "液", "air": "气", "background": "背"},
    "English": {"solid": "S", "water": "W", "air": "A", "background": "B"},
}
MAX_LABEL_VALUES = 4


def phase_name(phase: str, language: str = "中文") -> str:
    names = PHASE_NAMES["English" if str(language).lower().startswith("english") else "中文"]
    return names.get(phase, phase)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_label_image(path: Path) -> tuple[np.ndarray, dict[str, Any]]:
    """Read a single-channel label image (TIF/PNG) as a 2D integer array."""

    image = Image.open(Path(path))
    frame_count = int(getattr(image, "n_frames", 1) or 1)
    meta: dict[str, Any] = {
        "mode": image.mode,
        "frame_count": frame_count,
        "used_frame": 0,
        "width": int(image.size[0]),
        "height": int(image.size[1]),
    }
    if frame_count > 1:
        image.seek(0)
    array = np.asarray(image)
    if array.ndim == 3:
        channels = array[..., :3].astype(np.int64)
        if not (np.array_equal(channels[..., 0], channels[..., 1]) and np.array_equal(channels[..., 1], channels[..., 2])):
            raise ValueError(
                "The image has colour channels with different values. Export the segmented CT slice as a single-channel (grayscale) label image."
            )
        array = channels[..., 0]
    if array.ndim != 2:
        raise ValueError(f"Expected a 2D label image, got shape {list(array.shape)}.")
    if np.issubdtype(array.dtype, np.floating):
        if not np.all(np.isfinite(array)) or not np.allclose(array, np.round(array)):
            raise ValueError("The image contains non-integer intensities; it does not look like a segmented label image.")
        array = np.round(array)
    return array.astype(np.int64), meta


# ---------------------------------------------------------------------------
# Prompt parsing (deterministic backup for what the language model extracts)
# ---------------------------------------------------------------------------

_PHASE_WORDS = {
    "solid": r"固体|固相|骨架|颗粒|岩石|solid|grains?|matrix|rock",
    "water": r"水相|液相|液体|盐水|水|液|water|liquid|brine",
    "air": r"空气|气相|气体|气泡|气|air|gas",
    "background": r"外部|背景|外面|外侧|outside|background|exterior",
}
_ANY_PHASE = "|".join(f"(?P<{key}>{words})" for key, words in _PHASE_WORDS.items())


def _phase_from_match(match: re.Match[str]) -> str | None:
    for key in _PHASE_WORDS:
        if match.groupdict().get(key):
            return key
    return None


def parse_phase_labels(text: str, values: list[int] | None = None) -> dict[str, int]:
    """Extract explicit ``label value -> phase`` statements such as ``255 固体、102 水``."""

    if not text:
        return {}
    allowed = None if values is None else {int(value) for value in values}
    value_first = re.compile(
        rf"(?<![\d.])(\d{{1,5}})(?![\d.])\s*(?:[:：=]|->|→|是|为|代表|表示|对应)?\s*(?:{_ANY_PHASE})",
        flags=re.IGNORECASE,
    )
    phase_first = re.compile(
        rf"(?:{_ANY_PHASE})\s*(?:[:：=]|->|→|是|为|用|对应)\s*(?:灰度|像素值|标签|值|label|value)?\s*(?<![\d.])(\d{{1,5}})(?![\d.])",
        flags=re.IGNORECASE,
    )
    found: dict[str, int] = {}
    for pattern, value_group in ((value_first, 1), (phase_first, -1)):
        candidates: dict[str, int] = {}
        for match in pattern.finditer(text):
            phase = _phase_from_match(match)
            raw = match.group(value_group if value_group > 0 else match.lastindex)
            try:
                value = int(raw)
            except (TypeError, ValueError):
                continue
            if phase is None or (allowed is not None and value not in allowed):
                continue
            if phase in candidates or value in candidates.values():
                continue
            candidates[phase] = value
        if len(candidates) > len(found):
            found = candidates
    return found


def parse_background_statement(text: str) -> bool | None:
    """Return True/False when the prompt states whether background pixels exist."""

    if not text:
        return None
    lowered = text.lower()
    negative = (
        r"(?:无|没有|不含|不包含|不存在|未包含|没)(?:任何)?(?:外部)?背景",
        r"背景(?:像素)?[：: ]*(?:无|没有|不存在)",
        r"\bno\s+background",
        r"\bwithout\s+(?:any\s+)?background",
        r"background\s*(?:pixels?)?\s*[:=]?\s*(?:none|no)\b",
        r"不含外部|没有外部|无外部",
    )
    if any(re.search(pattern, lowered) for pattern in negative):
        return False
    positive = (
        r"(?:有|含|包含|带|带有|存在|含有)(?:外部)?背景",
        r"背景(?:像素|区域|值|标签)",
        r"(?:外部|背景)\s*(?:[:：=]|是|为)?\s*\d",
        r"\d+\s*(?:[:：=]|是|为|代表|表示)?\s*(?:外部|背景)",
        r"\bwith\s+(?:a\s+)?background",
        r"background\s+(?:pixels?|region|label|value)",
        r"\d+\s*(?:=|:)?\s*(?:outside|background)",
    )
    if any(re.search(pattern, lowered) for pattern in positive):
        return True
    return None


_NUM = r"(\d+(?:\.\d+)?)"
_UM = r"(?:μm|µm|um|微米|micron|microns|micrometers?)"


def parse_pixel_size_um(text: str) -> float | None:
    if not text:
        return None
    patterns = (
        rf"{_NUM}\s*{_UM}\s*(?:/|每|per)\s*(?:个)?(?:pixel|px|像素|voxel|体素)",
        rf"每(?:个)?(?:像素|体素)\s*(?:为|是|=|:|：)?\s*{_NUM}\s*{_UM}",
        rf"(?:分辨率|像素尺寸|像素大小|像素尺度|像素间距|体素尺寸|pixel\s*size|resolution|voxel\s*size)\D{{0,12}}?{_NUM}\s*{_UM}",
        rf"(?:分辨率|像素尺寸|像素大小|像素尺度|pixel\s*size|voxel\s*size)\s*(?:为|是|=|:|：)\s*{_NUM}",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = float(match.group(1))
            if value > 0:
                return value
    return None


_CN_DIGITS = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8}


def parse_run_preferences(text: str) -> dict[str, Any]:
    """Extract L-curve / smoothing / Gaussian choices stated in the prompt."""

    prefs: dict[str, Any] = {}
    if not text:
        return prefs
    lowered = text.lower()
    lcurve_word = r"l\s*[-_ ]?\s*curve|l\s*曲线|lcurve"
    if re.search(rf"(?:不|无需|不需要|不用|不要|关闭|禁用|跳过)\s*(?:做|用|执行|使用|进行|运行)?\s*(?:{lcurve_word})|\b(?:no|without|skip|disable)\s+(?:the\s+)?(?:{lcurve_word})", lowered):
        prefs["run_lcurve"] = False
    elif re.search(lcurve_word, lowered):
        prefs["run_lcurve"] = True

    reg = re.search(
        r"(?:平滑因子|正则化因子|正则化系数|正则化参数|正则化|regularization|smoothing\s*factor|alpha)\s*(?:[:：=]|为|是|取|设为|设置为|用)?\s*([0-9]*\.?[0-9]+(?:e[-+]?\d+)?)",
        lowered,
    )
    if reg:
        prefs["regularization"] = float(reg.group(1))
        if prefs.get("run_lcurve") is not True:
            prefs["run_lcurve"] = False

    gauss_word = r"高斯分峰|高斯|分峰|gaussian|peak\s*decomposition|peak\s*fitting"
    if re.search(rf"(?:不|无需|不需要|不用|不要|跳过|关闭)\s*(?:做|用|执行|进行|运行)?\s*(?:{gauss_word})|\b(?:no|without|skip)\s+(?:{gauss_word})", lowered):
        prefs["run_gaussian"] = False
    elif re.search(gauss_word, lowered):
        prefs["run_gaussian"] = True

    peaks = re.search(r"(\d)\s*(?:个)?(?:高斯)?峰|(\d)\s*(?:gaussian\s*)?peaks?", lowered) or re.search(
        r"([一二两三四五六七八])\s*(?:个)?(?:高斯)?峰", text
    )
    if peaks:
        token = next(group for group in peaks.groups() if group)
        count = int(token) if token.isdigit() else _CN_DIGITS.get(token)
        if count and 1 <= count <= 8:
            prefs["peak_count"] = count
            prefs.setdefault("run_gaussian", True)

    if re.search(
        r"(?:其[余他它]|剩下|别的)的?(?:参数|设置)?\s*(?:都|全部)?\s*(?:用|按|使用|采用|保持|为|取)?\s*默认"
        r"|(?:用|按|使用|采用|保持)\s*默认|默认参数|default\s+(?:settings|parameters|values)|use\s+(?:the\s+)?defaults",
        lowered,
    ):
        prefs["defaults_accepted"] = True
    return prefs


# ---------------------------------------------------------------------------
# Analysis and AI first guess
# ---------------------------------------------------------------------------


def _border_values(array: np.ndarray) -> np.ndarray:
    return np.concatenate([array[0, :], array[-1, :], array[:, 0], array[:, -1]])


def representative_point(mask: np.ndarray) -> list[float]:
    """Return an interior point (x, y in pixel units) of the largest region of ``mask``."""

    labeled, count = ndimage.label(mask)
    if count == 0:
        return [0.0, 0.0]
    sizes = ndimage.sum(np.ones_like(labeled), labeled, index=np.arange(1, count + 1))
    largest = labeled == (int(np.argmax(sizes)) + 1)
    distance = ndimage.distance_transform_edt(np.pad(largest, 1))[1:-1, 1:-1]
    row, col = np.unravel_index(int(np.argmax(distance)), distance.shape)
    return [float(col) + 0.5, float(row) + 0.5]


def _value_statistics(array: np.ndarray, values: list[int]) -> dict[int, dict[str, Any]]:
    border = _border_values(array)
    stats: dict[int, dict[str, Any]] = {}
    for value in values:
        mask = array == value
        ring = ndimage.binary_dilation(mask) & ~mask
        neighbours = {int(other): int(np.count_nonzero(array[ring] == other)) for other in values if other != value}
        total = max(1, sum(neighbours.values()))
        stats[int(value)] = {
            "count": int(np.count_nonzero(mask)),
            "fraction": float(np.mean(mask)),
            "border_fraction": float(np.mean(border == value)),
            "components": int(ndimage.label(mask)[1]),
            "neighbour_fraction": {key: count / total for key, count in neighbours.items()},
        }
    return stats


def guess_phase_assignment(
    array: np.ndarray,
    values: list[int],
    has_background: bool,
    stats: dict[int, dict[str, Any]] | None = None,
) -> tuple[dict[int, str], dict[str, str], str]:
    """Heuristic AI first guess of which label value is which phase.

    * background: the value that dominates the image border (only when the user
      said background pixels exist);
    * solid: the largest remaining phase (grains/matrix usually dominate a
      segmented section and are the densest, brightest CT phase);
    * water vs air: water is the wetting phase, so it usually occupies more pore
      area and touches the solid more than gas does.
    """

    stats = stats or _value_statistics(array, values)
    remaining = [int(value) for value in values]
    assignment: dict[int, str] = {}
    reasons: dict[str, str] = {}
    confidence = "high"

    material_count = len(remaining) - (1 if has_background else 0)
    if material_count < 2:
        raise ValueError("At least two material phases (solid + water) are needed after removing background.")
    if material_count > 3:
        raise ValueError("More than three material phases were found; only solid, water and air are supported.")

    if has_background:
        background = max(remaining, key=lambda v: (stats[v]["border_fraction"], -stats[v]["components"]))
        assignment[background] = "background"
        reasons["background"] = f"value {background} covers {stats[background]['border_fraction']:.0%} of the image border"
        if stats[background]["border_fraction"] < 0.5:
            confidence = "low"
        remaining.remove(background)

    solid = max(remaining, key=lambda v: (stats[v]["fraction"], v))
    brightest = max(remaining)
    assignment[solid] = "solid"
    reasons["solid"] = f"value {solid} is the largest material phase ({stats[solid]['fraction']:.0%} of pixels)"
    if solid != brightest:
        reasons["solid"] += f"; note the brightest value is {brightest}"
        confidence = "medium" if confidence == "high" else confidence
    remaining.remove(solid)

    if len(remaining) == 1:
        water = remaining[0]
        assignment[water] = "water"
        reasons["water"] = f"value {water} is the remaining pore phase"
    else:
        def wetting_score(value: int) -> float:
            pore_total = sum(stats[v]["fraction"] for v in remaining) or 1.0
            return stats[value]["fraction"] / pore_total + stats[value]["neighbour_fraction"].get(solid, 0.0)

        water, air = sorted(remaining, key=wetting_score, reverse=True)
        assignment[water] = "water"
        assignment[air] = "air"
        solid_contact_water = stats[water]["neighbour_fraction"].get(solid, 0.0)
        solid_contact_air = stats[air]["neighbour_fraction"].get(solid, 0.0)
        reasons["water"] = (
            f"value {water} has more pore area ({stats[water]['fraction']:.1%}) and solid contact "
            f"({solid_contact_water:.0%} of its boundary), typical of the wetting liquid"
        )
        reasons["air"] = (
            f"value {air} is the smaller pore phase ({stats[air]['fraction']:.1%}) with less solid contact "
            f"({solid_contact_air:.0%}), typical of trapped gas"
        )
        if abs(wetting_score(water) - wetting_score(air)) < 0.15:
            confidence = "low"
    return assignment, reasons, confidence


def display_gray_levels(values: list[int]) -> dict[int, int]:
    """Map label values to unique 8-bit display grays (identity for 8-bit labels)."""

    ordered = sorted(int(value) for value in values)
    if all(0 <= value <= 255 for value in ordered):
        return {value: value for value in ordered}
    if len(ordered) == 1:
        return {ordered[0]: 128}
    return {value: int(round(40 + 215 * index / (len(ordered) - 1))) for index, value in enumerate(ordered)}


def save_display_png(array: np.ndarray, gray_levels: dict[int, int], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    display = np.zeros(array.shape, dtype=np.uint8)
    for value, gray in gray_levels.items():
        display[array == value] = gray
    Image.fromarray(display, mode="L").save(path)
    return path


def phase_rgb(array: np.ndarray, assignment: dict[int, str]) -> np.ndarray:
    rgb = np.zeros((*array.shape, 3), dtype=np.uint8)
    for value, phase in assignment.items():
        rgb[array == int(value)] = PHASE_COLORS[phase]
    return rgb


def save_phase_preview_figure(
    array: np.ndarray,
    gray_levels: dict[int, int],
    assignment: dict[int, str],
    markers: dict[str, list[float]],
    path: Path,
    title: str,
) -> Path:
    """Side-by-side CT label image and phase-coloured overlay with phase markers."""

    path.parent.mkdir(parents=True, exist_ok=True)
    display = np.zeros(array.shape, dtype=np.uint8)
    for value, gray in gray_levels.items():
        display[array == value] = gray
    rgb = phase_rgb(array, assignment)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 5.2))
    axes[0].imshow(display, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
    axes[0].set_title("Segmented CT labels")
    axes[1].imshow(display, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
    axes[1].imshow(rgb, alpha=0.55, interpolation="nearest")
    axes[1].set_title(title)
    value_by_phase = {phase: value for value, phase in assignment.items()}
    for phase, (x, y) in markers.items():
        color = np.asarray(PHASE_COLORS.get(phase, (255, 255, 255))) / 255.0
        for ax in axes:
            ax.plot(x - 0.5, y - 0.5, marker="o", markersize=11, markerfacecolor=color, markeredgecolor="white", markeredgewidth=2)
            ax.annotate(
                f"{phase} ({value_by_phase.get(phase, '?')})",
                (x - 0.5, y - 0.5),
                xytext=(8, -8),
                textcoords="offset points",
                color="white",
                fontsize=8,
                bbox={"boxstyle": "round,pad=0.2", "fc": color, "ec": "none", "alpha": 0.9},
            )
    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def needs_background_question(value_count: int, has_background: bool | None) -> bool:
    """Two-value images never need the question; three or more do when unstated."""

    return value_count >= 3 and has_background is None


def analyze_ct_label_image(
    image_path: Path,
    output_dir: Path,
    *,
    has_background: bool | None = None,
    explicit_labels: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Inspect a segmented CT label image and prepare the phase-confirmation step."""

    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    array, meta = load_label_image(image_path)
    values = [int(value) for value in np.unique(array)]
    base: dict[str, Any] = {
        "input_path": str(image_path.resolve()),
        "image_meta": meta,
        "shape": [int(array.shape[0]), int(array.shape[1])],
        "values": values,
        "value_count": len(values),
    }
    if len(values) < 2:
        return base | {"status": "failed", "error": "single_value_image", "message": "The image contains only one pixel value; no phases can be separated."}
    if len(values) > MAX_LABEL_VALUES:
        return base | {
            "status": "failed",
            "error": "not_segmented",
            "message": (
                f"The image contains {len(values)} distinct pixel values. A segmented CT label image should contain "
                "2-4 values (solid, water, optional air, optional background). Please segment/threshold the CT slice first."
            ),
        }

    explicit_labels = {phase: int(value) for phase, value in (explicit_labels or {}).items() if phase in PHASES and int(value) in values}
    if has_background is None and explicit_labels:
        if "background" in explicit_labels:
            has_background = True
        elif len(explicit_labels) == len(values):
            has_background = False
    if len(values) == 2:
        has_background = False
    if len(values) == 4 and has_background is False:
        return base | {
            "status": "failed",
            "error": "four_material_phases",
            "message": "Four label values without background would mean four material phases; only solid, water and air are supported.",
        }

    stats = _value_statistics(array, values)
    gray_levels = display_gray_levels(values)
    stem = image_path.stem
    display_png = save_display_png(array, gray_levels, output_dir / timestamped_name(f"{stem}__ct_labels_display", "png"))
    base |= {
        "value_stats": {str(key): {k: v for k, v in item.items() if k != "neighbour_fraction"} for key, item in stats.items()},
        "display_png": str(display_png.resolve()),
        "display_gray_levels": {str(key): value for key, value in gray_levels.items()},
        "has_background": has_background,
    }
    if needs_background_question(len(values), has_background):
        return base | {
            "status": "needs_background_answer",
            "message": (
                f"The image has {len(values)} pixel values {values}. Please tell me whether it contains background "
                "(outside-the-sample) pixels, because the third/fourth value could be either air or background."
            ),
            "suggested_has_background": bool(len(values) == 4 or max(item["border_fraction"] for item in stats.values()) > 0.95),
            "artifacts": [str(display_png)],
        }

    assignment, reasons, confidence = guess_phase_assignment(array, values, bool(has_background), stats)
    ai_assignment = dict(assignment)
    source = "ai"
    if explicit_labels:
        for phase, value in explicit_labels.items():
            previous_phase = assignment.get(value)
            previous_value = next((v for v, p in assignment.items() if p == phase), None)
            if previous_value is not None and previous_phase is not None:
                assignment[previous_value] = previous_phase
            assignment[value] = phase
        source = "prompt" if len(explicit_labels) >= len(values) - 1 else "prompt_partial"
    value_points = {str(value): representative_point(array == value) for value in values}
    markers = {phase: value_points[str(value)] for value, phase in assignment.items()}
    preview_png = save_phase_preview_figure(
        array,
        gray_levels,
        assignment,
        markers,
        output_dir / timestamped_name(f"{stem}__phase_guess_preview", "png"),
        "AI phase guess" if source == "ai" else "Phase assignment from prompt",
    )
    agreement = {str(value): ai_assignment.get(value) == phase for value, phase in assignment.items()}
    return base | {
        "status": "needs_phase_confirmation",
        "message": "Phase markers are ready. The user must confirm or drag-correct them in the phase preview before meshing.",
        "has_background": bool(has_background),
        "ai_assignment": {str(key): value for key, value in ai_assignment.items()},
        "assignment": {str(key): value for key, value in assignment.items()},
        "assignment_source": source,
        "ai_reasons": reasons,
        "ai_confidence": confidence,
        "prompt_agrees_with_ai": all(agreement.values()) if explicit_labels else None,
        "markers": markers,
        "value_points": value_points,
        "preview_png": str(preview_png.resolve()),
        "artifacts": [str(display_png), str(preview_png)],
    }


def reassign_phase(assignment: dict[str, str], value: str, phase: str) -> dict[str, str]:
    """Assign ``phase`` to ``value`` and swap with the value that previously held it."""

    updated = dict(assignment)
    value = str(value)
    if value not in updated or phase not in PHASES:
        return updated
    old_phase = updated[value]
    holder = next((key for key, current in updated.items() if current == phase), None)
    updated[value] = phase
    if holder is not None and holder != value:
        updated[holder] = old_phase
    return updated


def validate_assignment(assignment: dict[str, str], values: list[int], has_background: bool) -> list[str]:
    problems: list[str] = []
    if sorted(int(key) for key in assignment) != sorted(int(value) for value in values):
        problems.append("Every pixel value must be assigned to exactly one phase.")
    phases = list(assignment.values())
    if len(set(phases)) != len(phases):
        problems.append("Two pixel values are assigned to the same phase.")
    if "water" not in phases:
        problems.append("A water/liquid phase is required: NMR signal only comes from the liquid.")
    if "solid" not in phases:
        problems.append("A solid phase is required for surface relaxation.")
    if has_background and "background" not in phases:
        problems.append("Background was declared but no value is assigned to it.")
    return problems


# ---------------------------------------------------------------------------
# Confirmed assignment -> simulation labels
# ---------------------------------------------------------------------------


def apply_phase_assignment(array: np.ndarray, assignment: dict[str, str]) -> np.ndarray:
    labels = np.full(array.shape, OUTSIDE, dtype=np.uint8)
    for value, phase in assignment.items():
        labels[array == int(value)] = PHASE_TO_LABEL[phase]
    return labels


def crop_to_sample(labels: np.ndarray) -> tuple[np.ndarray, list[int]]:
    """Crop away rows/columns that contain only background."""

    sample = labels != OUTSIDE
    if not np.any(sample):
        raise ValueError("No sample pixels remain after removing background.")
    rows, cols = np.where(sample)
    bbox = [int(rows.min()), int(rows.max()), int(cols.min()), int(cols.max())]
    return labels[bbox[0] : bbox[1] + 1, bbox[2] : bbox[3] + 1], bbox


def save_internal_label_png(labels: np.ndarray, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    rgb = np.zeros((*labels.shape, 3), dtype=np.uint8)
    for phase, label in PHASE_TO_LABEL.items():
        rgb[labels == label] = PHASE_COLORS[phase]
    Image.fromarray(rgb, mode="RGB").save(path)
    return path


def estimate_surface_t2(labels: np.ndarray, pixel_size_um: float, bulk_t2_ms: float, rho_solid_um_per_ms: float) -> dict[str, float]:
    """Fast-diffusion (Brownstein-Tarr) estimate T2 = 1 / (1/T2b + rho * S/V) for the water domain."""

    water = labels == WATER
    water_pixels = int(np.count_nonzero(water))
    if water_pixels == 0:
        return {"surface_to_volume_per_um": 0.0, "estimated_t2_ms": float(bulk_t2_ms)}
    solid = labels == SOLID
    contacts = 0
    for axis in (0, 1):
        a = water[:-1, :] if axis == 0 else water[:, :-1]
        b = water[1:, :] if axis == 0 else water[:, 1:]
        sa = solid[:-1, :] if axis == 0 else solid[:, :-1]
        sb = solid[1:, :] if axis == 0 else solid[:, 1:]
        contacts += int(np.count_nonzero(a & sb)) + int(np.count_nonzero(b & sa))
    surface_um = contacts * pixel_size_um
    area_um2 = water_pixels * pixel_size_um**2
    s_over_v = surface_um / area_um2
    rate = 1.0 / max(bulk_t2_ms, 1e-9) + rho_solid_um_per_ms * s_over_v
    return {"surface_to_volume_per_um": float(s_over_v), "estimated_t2_ms": float(1.0 / rate)}


def _nice_number(value: float) -> float:
    if value <= 0:
        return 1.0
    exponent = math.floor(math.log10(value))
    fraction = value / 10**exponent
    nice = 1.0 if fraction < 1.5 else 2.0 if fraction < 3.5 else 5.0 if fraction < 7.5 else 10.0
    return float(nice * 10**exponent)


def recommend_time_axis(estimated_t2_ms: float, steps: int = 400) -> dict[str, float]:
    """Simulate ~5 estimated T2 so the decay is resolved before inversion."""

    t_max = float(np.clip(_nice_number(5.0 * estimated_t2_ms), 200.0, 30000.0))
    dt = max(0.1, _nice_number(t_max / steps))
    return {"t_max_ms": t_max, "dt_ms": dt}


@dataclass
class CtRunConfig:
    pixel_size_um: float = 1.0
    diffusion_um2_per_ms: float = 2.0
    bulk_t2_ms: float = 3000.0
    rho_solid_um_per_ms: float = 0.005
    rho_gas_um_per_ms: float = 0.0
    dt_ms: float | None = None
    t_max_ms: float | None = None
    mesh_boundary_px: float = 1.0
    mesh_bulk_px: float = 3.0
    mesh_max_points: int = 80000
    max_grid_size: int = 600
    run_lcurve: bool = True
    regularization: float = 1.0
    num_bins: int = 200
    t2_min_ms: float | None = None
    t2_max_ms: float | None = None
    run_gaussian: bool = True
    peak_count: int = 2

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, values: dict[str, Any] | None) -> "CtRunConfig":
        values = dict(values or {})
        if "pixel_size_um" not in values:
            for key in ("pixel_size_x_um", "pixel_size_y_um"):
                if values.get(key):
                    values["pixel_size_um"] = values[key]
                    break
        known = {field: values[field] for field in cls.__dataclass_fields__ if field in values and values[field] is not None}
        config = cls(**known)
        for name in ("pixel_size_um", "diffusion_um2_per_ms", "bulk_t2_ms", "rho_solid_um_per_ms", "rho_gas_um_per_ms", "regularization", "mesh_boundary_px", "mesh_bulk_px"):
            setattr(config, name, float(getattr(config, name)))
        config.run_lcurve = bool(config.run_lcurve)
        config.run_gaussian = bool(config.run_gaussian)
        config.peak_count = int(config.peak_count)
        config.num_bins = int(config.num_bins)
        config.mesh_max_points = int(config.mesh_max_points)
        return config


def simulation_params_for(config: CtRunConfig, labels: np.ndarray, downsample_scale: float = 1.0) -> tuple[Simulation2DParams, dict[str, float]]:
    pixel = float(config.pixel_size_um) * float(downsample_scale)
    estimate = estimate_surface_t2(labels, pixel, config.bulk_t2_ms, config.rho_solid_um_per_ms)
    recommended = recommend_time_axis(estimate["estimated_t2_ms"])
    params = Simulation2DParams(
        pixel_size_x_um=pixel,
        pixel_size_y_um=pixel,
        diffusion_um2_per_ms=config.diffusion_um2_per_ms,
        bulk_t2_ms=config.bulk_t2_ms,
        rho_solid_um_per_ms=config.rho_solid_um_per_ms,
        rho_gas_um_per_ms=config.rho_gas_um_per_ms,
        dt_ms=float(config.dt_ms or recommended["dt_ms"]),
        t_max_ms=float(config.t_max_ms or recommended["t_max_ms"]),
        max_grid_size=config.max_grid_size,
        solver="triangular",
        mesh_bulk_size_um=max(config.mesh_bulk_px, 1.0) * pixel,
        mesh_boundary_size_um=max(config.mesh_boundary_px, 0.25) * pixel,
        mesh_max_points=config.mesh_max_points,
    )
    return params, estimate | recommended


def ct_edge_classifier(labels: np.ndarray, midpoint: np.ndarray, params: Simulation2DParams) -> str:
    """Classify a water-domain boundary edge by the nearest non-water pixel.

    solid -> surface relaxation, air -> gas/liquid interface relaxivity,
    background or image edge -> reflecting (no-flux) boundary.
    """

    width_um = labels.shape[1] * params.pixel_size_x_um
    height_um = labels.shape[0] * params.pixel_size_y_um
    tol_x = 0.25 * params.pixel_size_x_um
    tol_y = 0.25 * params.pixel_size_y_um
    if (
        float(midpoint[0]) <= tol_x
        or float(midpoint[0]) >= width_um - tol_x
        or float(midpoint[1]) <= tol_y
        or float(midpoint[1]) >= height_um - tol_y
    ):
        # Edge of the image/crop: the slice was cut here, so the boundary is reflecting.
        return "noflux"
    row, col = xy_to_row_col(labels, float(midpoint[0]), float(midpoint[1]), params)
    r0, r1 = max(0, row - 2), min(labels.shape[0], row + 3)
    c0, c1 = max(0, col - 2), min(labels.shape[1], col + 3)
    local = labels[r0:r1, c0:c1]
    candidates = np.argwhere(local != WATER)
    if candidates.size == 0:
        return "noflux"
    px = float(midpoint[0]) / max(params.pixel_size_x_um, 1e-12)
    py = labels.shape[0] - float(midpoint[1]) / max(params.pixel_size_y_um, 1e-12)
    centers_x = candidates[:, 1] + c0 + 0.5
    centers_y = candidates[:, 0] + r0 + 0.5
    nearest = int(np.argmin((centers_x - px) ** 2 + (centers_y - py) ** 2))
    label = local[candidates[nearest, 0], candidates[nearest, 1]]
    if label == SOLID:
        return "solid"
    if label == AIR:
        return "gas"
    return "noflux"


def save_ct_mesh_plot(mesh: dict[str, Any], output_path: Path) -> Path:
    """Triangular water mesh with boundary edges coloured by boundary condition."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    points = mesh["points"]
    triangulation = mtri.Triangulation(points[:, 0], points[:, 1], mesh["triangles"])
    fig, ax = plt.subplots(figsize=(7.5, 7.0))
    ax.triplot(triangulation, color="0.55", lw=0.15)
    styles = {
        "solid": ("#d4a106", "solid-water (rho_solid)"),
        "gas": ("#1f77ff", "air-water (rho_gas)"),
        "noflux": ("#444444", "no-flux / sample edge"),
    }
    for kind, edges in mesh.get("boundary_edges", {}).items():
        if not edges:
            continue
        color, label = styles.get(kind, ("k", kind))
        segments = [[points[a], points[b]] for a, b in edges]
        ax.add_collection(LineCollection(segments, colors=color, linewidths=0.9, label=label))
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x (um)")
    ax.set_ylabel("y (um)")
    ax.set_title("pyGIMLi triangular water-domain mesh")
    ax.legend(loc="upper right", fontsize=7, framealpha=0.85)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path
