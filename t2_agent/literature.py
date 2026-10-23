"""Literature-backed interpretation of T2 results with AGU-style citations.

The knowledge base in ``docs/nmr_t2_literature_knowledge`` holds the citation
keys, verified AGU references (Crossref-checked DOIs or book title pages) and
the scenario map. This module turns the numbers of one analysis into short,
specific statements, each tied to the papers that support it, and returns a
reference list. Only references marked ``reference_verified`` are cited.

Each statement leads with what the number means for the sample, gives the
mechanism and the source, and is emitted only when the agent has computed the
quantity it rests on; checks the agent does not run are never suggested.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

KB_DIR = Path(__file__).resolve().parents[1] / "docs" / "nmr_t2_literature_knowledge"

# Words in the user's request that put a measured decay in a soil or organic-matter context.
SOIL_WORDS = ("soil", "peat", "organic", "biomass", "humus", "compost", "biochar", "clay", "loam", "silt",
              "土壤", "土样", "土体", "黏土", "粘土", "砂土", "粉土", "泥炭", "有机", "生物质", "腐殖", "堆肥", "生物炭")
ORGANIC_WORDS = ("peat", "organic", "biomass", "humus", "compost", "biochar", "泥炭", "有机", "生物质", "腐殖", "堆肥", "生物炭")


@lru_cache(maxsize=1)
def load_references() -> dict[str, dict[str, Any]]:
    path = KB_DIR / "literature_manifest.enriched.json"
    if not path.exists():
        return {}
    entries = json.loads(path.read_text(encoding="utf-8"))
    return {entry["citation_key"]: entry for entry in entries if entry.get("reference_verified") and entry.get("reference_agu")}


def in_text(keys: list[str]) -> str:
    """AGU in-text form, e.g. (Hansen, 1992; Whittall & MacKay, 1989)."""

    refs = load_references()
    parts = [refs[key]["in_text"] for key in keys if key in refs]
    return f"({'; '.join(parts)})" if parts else ""


@dataclass
class Finding:
    scenario: str
    text: str
    keys: list[str] = field(default_factory=list)


@dataclass
class AnalysisFacts:
    """Numbers the interpretation draws on; fields stay None when not available."""

    workflow: str = "measured"  # measured | ideal | ct
    inversion_mode: str | None = None
    selection_rule: str | None = None
    alpha: float | None = None
    t2_ms: np.ndarray | None = None
    spectrum: np.ndarray | None = None
    main_peak_ms: float | None = None
    short_fraction: float | None = None
    long_fraction: float | None = None
    peak_positions_ms: list[float] = field(default_factory=list)
    gaussian_peaks: list[dict[str, float]] = field(default_factory=list)
    gaussian_r2: float | None = None
    early_misfit_fraction: float | None = None
    decay_end_fraction: float | None = None
    first_echo_ms: float | None = None
    echo_spacing_ms: float | None = None
    sample_context: str = ""
    ideal: dict[str, Any] | None = None
    ct: dict[str, Any] | None = None
    bulk_t2_ms: float | None = None
    pore_diameter_um: dict[str, float | None] | None = None
    rho_um_per_ms: float | None = None
    diffusion_um2_per_ms: float | None = None


def _zh(language: str) -> bool:
    return not language.lower().startswith("english")


def _fmt(value: float) -> str:
    if value is None or not math.isfinite(value):
        return "—"
    return f"{value:.0f}" if abs(value) >= 100 else f"{value:.3g}"


def _pct(value: float) -> str:
    return f"{value:.0%}" if abs(value) >= 0.095 else f"{value:.1%}"


def _small_pct(value: float) -> str:
    value = abs(value)
    return f"{value:.2%}" if value < 0.001 else f"{value:.1%}"


def _has(text: str, words: tuple[str, ...]) -> bool:
    low = (text or "").lower()
    return any(word in low for word in words)


def spectrum_peaks(t2_ms: np.ndarray, amplitude: np.ndarray) -> list[float]:
    """Positions of the spectral maxima that carry at least 5% of the maximum."""

    from scipy.signal import find_peaks

    amp = np.asarray(amplitude, dtype=float)
    if amp.size < 3 or not np.isfinite(amp).any() or amp.max() <= 0:
        return []
    index, _ = find_peaks(amp, height=0.05 * amp.max(), prominence=0.03 * amp.max())
    return [float(t2_ms[i]) for i in index]


def class_fractions(t2_ms: np.ndarray, amplitude: np.ndarray, cuts: tuple[float, ...]) -> list[float]:
    """Share of the spectrum between successive cut values (bin sums on the log grid; they add to 1)."""

    t2 = np.asarray(t2_ms, dtype=float)
    amp = np.clip(np.asarray(amplitude, dtype=float), 0.0, None)
    total = float(amp.sum())
    edges = [-np.inf, *cuts, np.inf]
    if total <= 0:
        return [0.0] * (len(edges) - 1)
    return [float(amp[(t2 >= lo) & (t2 < hi)].sum() / total) for lo, hi in zip(edges[:-1], edges[1:])]


def harmonic_mean_t2(t2_ms: np.ndarray, amplitude: np.ndarray) -> float | None:
    """Amplitude-weighted harmonic mean, the T2 fixed by the initial decay rate."""

    t2 = np.asarray(t2_ms, dtype=float)
    amp = np.clip(np.asarray(amplitude, dtype=float), 0.0, None)
    weight = float(np.sum(amp / t2))
    return float(amp.sum() / weight) if weight > 0 else None


def early_time_misfit(trimmed_xlsx: Path, early_ms: float = 10.0) -> tuple[float | None, float | None]:
    """Mean full-resolution residual (data - fit) before ``early_ms`` and the final signal, both relative to the first sample."""

    try:
        table = next(iter(pd.read_excel(trimmed_xlsx, sheet_name=None).values()))
        used = table["trimmed_time_ms"].notna() & table["trimmed_fit_amplitude"].notna()
        time = table.loc[used, "trimmed_time_ms"].to_numpy(dtype=float)
        data = table.loc[used, "trimmed_amplitude"].to_numpy(dtype=float)
        fit = table.loc[used, "trimmed_fit_amplitude"].to_numpy(dtype=float)
    except Exception:
        return None, None
    if data.size == 0 or data[0] == 0:
        return None, None
    early = time < early_ms
    misfit = float(np.mean(data[early] - fit[early]) / data[0]) if early.sum() >= 3 else None
    return misfit, float(data[-1] / data[0])


def echo_timing(trimmed_xlsx: Path) -> tuple[float | None, float | None]:
    """First echo time and echo spacing (median of the first intervals) of a measured decay."""

    try:
        table = next(iter(pd.read_excel(trimmed_xlsx, sheet_name=None).values()))
        time = table["trimmed_time_ms"].dropna().to_numpy(dtype=float)
    except Exception:
        return None, None
    if time.size < 3:
        return None, None
    return float(time[0]), float(np.median(np.diff(time[: min(time.size, 50)])))


def gaussian_fit_r2(fit_xlsx: Path) -> float | None:
    try:
        table = next(iter(pd.read_excel(fit_xlsx, sheet_name=None).values()))
        original = table["original_spectrum"].to_numpy(dtype=float)
        fitted = table["fitted_spectrum"].to_numpy(dtype=float)
    except Exception:
        return None
    total = float(np.sum((original - original.mean()) ** 2))
    return float(1.0 - np.sum((original - fitted) ** 2) / total) if total > 0 else None


def wall_coverage_from_labels(labels: np.ndarray) -> dict[str, float] | None:
    """Pixel-face counts of a CT label image (0 background, 1 water, 2 solid, 3 air).

    Returns the share of the solid pore wall touched by water and the ratio of the
    surface-to-volume of the whole pore space to that of the water domain; image-edge
    and background faces count as relaxing, as in the forward model.
    """

    lab = np.asarray(labels)
    water, solid, air, outside = lab == 1, lab == 2, lab == 3, lab == 0
    pore = water | air
    if not water.any() or not pore.any():
        return None

    def faces(a: np.ndarray, b: np.ndarray) -> int:
        return int(np.sum(a[:, :-1] & b[:, 1:]) + np.sum(a[:, 1:] & b[:, :-1]) + np.sum(a[:-1, :] & b[1:, :]) + np.sum(a[1:, :] & b[:-1, :]))

    def edge(a: np.ndarray) -> int:
        return int(a[0, :].sum() + a[-1, :].sum() + a[:, 0].sum() + a[:, -1].sum())

    wet_wall, dry_wall = faces(water, solid), faces(air, solid)
    if wet_wall + dry_wall == 0:
        return None
    water_sv = (wet_wall + faces(water, outside) + edge(water)) / water.sum()
    pore_sv = (wet_wall + dry_wall + faces(pore, outside) + edge(pore)) / pore.sum()
    return {"wetted_wall_fraction": wet_wall / (wet_wall + dry_wall), "saturated_to_water_sv_ratio": float(pore_sv / water_sv)}


def water_regions_from_labels(labels: np.ndarray, pixel_um: float, rho: float, bulk_t2_ms: float) -> dict[str, float] | None:
    """Connected water regions of a CT label image and their fast-diffusion T2 from pixel-face S/V.

    Relaxing faces are water faces next to solid or background and at the image border, as in
    the forward model. Returns the region count, the water share and T2 of the largest region,
    and the share and harmonic-mean T2 of all other regions.
    """

    from scipy import ndimage

    lab = np.asarray(labels)
    water, sink = lab == 1, (lab == 2) | (lab == 0)
    regions, count = ndimage.label(water)
    if count == 0:
        return None

    def faces(a: np.ndarray, b: np.ndarray) -> int:
        return int(np.sum(a[:, :-1] & b[:, 1:]) + np.sum(a[:, 1:] & b[:, :-1]) + np.sum(a[:-1, :] & b[1:, :]) + np.sum(a[1:, :] & b[:-1, :]))

    sizes, t2 = [], []
    for k in range(1, count + 1):
        mask = regions == k
        edge = faces(mask, sink) + int(mask[0, :].sum() + mask[-1, :].sum() + mask[:, 0].sum() + mask[:, -1].sum())
        sizes.append(mask.sum())
        t2.append(1.0 / (1.0 / bulk_t2_ms + rho * edge / (mask.sum() * pixel_um)))
    sizes, t2 = np.asarray(sizes, float), np.asarray(t2, float)
    order = np.argsort(-sizes)
    big, rest = order[0], order[1:]
    out = {"count": int(count), "largest_share": float(sizes[big] / sizes.sum()), "largest_t2_ms": float(t2[big])}
    if rest.size:
        out["others_share"] = float(sizes[rest].sum() / sizes.sum())
        out["others_t2_ms"] = float(sizes[rest].sum() / np.sum(sizes[rest] / t2[rest]))
    return out


# --------------------------------------------------------------------------
# Measured decays
# --------------------------------------------------------------------------


def _soil_findings(facts: AnalysisFacts, zh: bool) -> list[Finding]:
    """Water-state classes of a soil or organic-rich sample (Bayer et al., 2010)."""

    t2, amp = facts.t2_ms, facts.spectrum
    tight, loose, bulk_like = class_fractions(t2, amp, (60.0, 300.0))
    above_1s = class_fractions(t2, amp, (1000.0,))[1]
    below_30 = class_fractions(t2, amp, (30.0,))[0]
    organic = _has(facts.sample_context, ORGANIC_WORDS)
    bound = tight + loose
    keys = ["Bayer2010SoilNMR", "Jaeger2010PeatSwelling"]
    if bound >= 0.6:
        lead_zh, lead_en = f"约 {_pct(bound)} 的信号来自被细孔或基质束缚的水，水以束缚态为主", f"about {_pct(bound)} of the signal comes from water held in fine pores or by the matrix, so bound water dominates"
    elif bulk_like >= 0.5:
        lead_zh, lead_en = f"大孔或体相类水占 {_pct(bulk_like)}，以较自由的孔隙水为主", f"macropore or bulk-like water holds {_pct(bulk_like)}, so freer pore water dominates"
    else:
        lead_zh, lead_en = "束缚水与大孔水的比例相当", "bound and macropore water are comparable"
    if above_1s < 0.05:
        free_zh = f"T2 > 1 s 的信号仅 {_pct(above_1s)}，而从泥炭中提取的孔隙水 T2 约为 2 s，几乎没有体相（自由）水；{_pct(bulk_like)} 的大孔或体相类水是可自由流动水的上限，而不是可排水量"
        free_en = f"Only {_pct(above_1s)} relaxes slower than 1 s, whereas pore solution extracted from peat relaxes in about 2 s, so bulk (free) water is nearly absent; the {_pct(bulk_like)} of macropore or bulk-like water is an upper bound on mobile water, not a drainable volume"
    else:
        free_zh = f"T2 > 1 s 的信号占 {_pct(above_1s)}，接近泥炭提取孔隙水约 2 s 的体相弛豫，属于较自由的水"
        free_en = f"{_pct(above_1s)} relaxes slower than 1 s, close to the about 2 s of pore solution extracted from peat, i.e. free water"
    organic_zh = "；有机质的聚合物网络（水凝胶效应）与顺磁中心会使 T2 比同孔径的矿物土更短，因此这些类别描述的是水的状态，而不是孔径分布" if organic else ""
    organic_en = "; the polymer network of organic matter (hydrogel effect) and paramagnetic centres shorten T2 relative to a mineral soil with the same pores, so these classes describe water states rather than a pore-size distribution" if organic else ""
    org_keys = ["CostabelStange2025Peat"] if organic else []
    out = [Finding(
        "soil_water_state_classes",
        (f"{lead_zh}。按 Bayer 等对土壤与泥炭水状态的经验分类，T2 < 60 ms（微孔或紧束缚水）占 {_pct(tight)}，60–300 ms（中孔或松束缚水）占 {_pct(loose)}，> 300 ms（大孔或体相水）占 {_pct(bulk_like)}；分区边界随文献略有不同 {in_text(keys[:1])}。"
         f"{free_zh} {in_text(keys[1:])}{organic_zh}{(' ' + in_text(org_keys)) if org_keys else ''}。"
         if zh else
         f"{lead_en[0].upper() + lead_en[1:]}. Using the empirical water-state classes for soils and peats, T2 < 60 ms (micropore or tightly bound water) holds {_pct(tight)}, 60–300 ms (mesopore or loosely bound water) {_pct(loose)} and > 300 ms (macropore or bulk water) {_pct(bulk_like)}; the class bounds vary slightly between studies {in_text(keys[:1])}. "
         f"{free_en} {in_text(keys[1:])}{organic_en}{(' ' + in_text(org_keys)) if org_keys else ''}."),
        keys + org_keys,
    )]

    # Two Gaussian populations, read against the classes.
    comps = sorted((p for p in facts.gaussian_peaks if p.get("position_ms") and p.get("area_fraction") is not None), key=lambda p: p["position_ms"])
    if len(comps) == 2 and _components_resolved(facts, comps):
        short, long_ = comps
        r2 = f"（R² = {facts.gaussian_r2:.2f}）" if facts.gaussian_r2 is not None else ""
        r2_en = f" (R² = {facts.gaussian_r2:.2f})" if facts.gaussian_r2 is not None else ""
        keys2 = ["Jaeger2010PeatSwelling"] + (["CostabelStange2025Peat", "Mashhadi2025SDRPeat"] if organic else [])

        def band(position: float) -> tuple[str, str]:
            if position < 60:
                return "紧束缚水范围", "tightly bound range"
            if position <= 300:
                return "松束缚水范围", "loosely bound range"
            return "松束缚水与体相水的交界及以上", "loosely bound to bulk boundary and above"

        b1, b2 = band(short["position_ms"]), band(long_["position_ms"])
        first_zh = f"第一群以 {_fmt(short['position_ms'])} ms 为中心，落在{b1[0]}；谱中 {_pct(below_30)} 的信号 T2 < 30 ms，泥炭中这一范围的水扩散系数明显降低"
        first_en = f"The first is centred at {_fmt(short['position_ms'])} ms in the {b1[1]}; {_pct(below_30)} of the signal has T2 < 30 ms, the range in which water in peat shows reduced diffusivity"
        if organic:
            first_zh += "，与有机基质或细孔中的受限水相符"
            first_en += ", consistent with water held by the organic matrix or fine pores"
            second_zh = f"第二群以 {_fmt(long_['position_ms'])} ms 为中心，落在{b2[0]}，对应较开放的孔隙或完整植物细胞内的水；后者可以贡献显著信号，但几乎不参与渗流"
            second_en = f"The second, at {_fmt(long_['position_ms'])} ms, lies in the {b2[1]} and matches more open pores or water inside intact plant cells, which can carry much of the signal yet contribute little to flow"
        else:
            second_zh = f"第二群以 {_fmt(long_['position_ms'])} ms 为中心，落在{b2[0]}，对应较大孔隙中的水"
            second_en = f"The second, at {_fmt(long_['position_ms'])} ms, lies in the {b2[1]} and matches water in larger pores"
        out.append(Finding(
            "two_water_populations",
            (f"谱可用两个高斯分量很好地描述{r2}：{_fmt(short['position_ms'])} ms 占 {_pct(short['area_fraction'])}，{_fmt(long_['position_ms'])} ms 占 {_pct(long_['area_fraction'])}，两者相距 {long_['position_ms'] / short['position_ms']:.1f} 倍，是两个可区分的水群。"
             f"{first_zh} {in_text(keys2[:1])}。{second_zh}{(' ' + in_text(keys2[1:])) if len(keys2) > 1 else ''}。"
             if zh else
             f"Two Gaussian components describe the spectrum well{r2_en}: {_fmt(short['position_ms'])} ms with {_pct(short['area_fraction'])} and {_fmt(long_['position_ms'])} ms with {_pct(long_['area_fraction'])}, {long_['position_ms'] / short['position_ms']:.1f} times apart, i.e. two distinct water populations. "
             f"{first_en} {in_text(keys2[:1])}. {second_en}{(' ' + in_text(keys2[1:])) if len(keys2) > 1 else ''}."),
            keys2,
        ))
    return out


def _echo_spacing_finding(facts: AnalysisFacts, zh: bool, soil: bool) -> Finding | None:
    te = facts.echo_spacing_ms
    if not te or not facts.first_echo_ms:
        return None
    retained = math.exp(-facts.first_echo_ms / 0.1)
    below_1ms = class_fractions(facts.t2_ms, facts.spectrum, (1.0,))[0]
    if soil:
        keys = ["Peng2023Bentonite", "Jaeger2010PeatSwelling"]
        return Finding(
            "echo_spacing_lower_bound",
            (f"首个回波在 {_fmt(facts.first_echo_ms)} ms（回波间隔 {_fmt(te)} ms）：T2 短于首回波时间的组分在首个回波前已损失 63% 以上，T2 = 0.1 ms 的组分只剩 {_pct(retained)}。黏土吸附水的 T2 约为 0.05–0.13 ms，泥炭中的不冻结合水约为 0.3 ms {in_text(keys)}，"
             f"而本谱 < 1 ms 的部分只有 {_pct(below_1ms)}，因此上面的束缚水比例是下限。"
             if zh else
             f"The first echo is at {_fmt(facts.first_echo_ms)} ms (echo spacing {_fmt(te)} ms): components with T2 shorter than this lose more than 63% of their amplitude before it, and a 0.1 ms component keeps {_pct(retained)}. Adsorbed water in clay relaxes in about 0.05–0.13 ms and non-freezable water in peat in about 0.3 ms {in_text(keys)}, "
             f"while only {_pct(below_1ms)} of this spectrum lies below 1 ms, so the bound-water fractions above are lower bounds."),
            keys,
        )
    keys = ["Coates1999NMRLogging"]
    return Finding(
        "echo_spacing_lower_bound",
        (f"首个回波在 {_fmt(facts.first_echo_ms)} ms（回波间隔 {_fmt(te)} ms）：T2 短于首回波时间的组分在首个回波前已损失 63% 以上，谱中短 T2 的占比是下限 {in_text(keys)}。"
         if zh else
         f"The first echo is at {_fmt(facts.first_echo_ms)} ms (echo spacing {_fmt(te)} ms): components with T2 shorter than this lose more than 63% of their amplitude before it, so the short-T2 share is a lower bound {in_text(keys)}."),
        keys,
    )


def _measured_findings(facts: AnalysisFacts, zh: bool) -> list[Finding]:
    soil = _has(facts.sample_context, SOIL_WORDS)
    out: list[Finding] = []
    if soil and facts.t2_ms is not None and facts.spectrum is not None:
        out.extend(_soil_findings(facts, zh))
    else:
        keys = ["BrownsteinTarr1979", "Kleinberg1994RelaxationMechanism"]
        out.append(Finding(
            "short_t2_dominant",
            ((f"主峰位于约 {_fmt(facts.main_peak_ms)} ms。" if facts.main_peak_ms else "")
             + f"在快扩散区制下 1/T2 ≈ 1/T2,bulk + ρ·S/V，T2 分布反映孔隙的表面积/体积比，长 T2 对应较大孔隙；换算为孔径需要已知该样品的表面弛豫率 ρ {in_text(keys)}。"
             if zh else
             (f"The main peak lies near {_fmt(facts.main_peak_ms)} ms. " if facts.main_peak_ms else "")
             + f"In the fast-diffusion regime 1/T2 ≈ 1/T2,bulk + ρ·S/V, so the T2 distribution follows the surface-to-volume ratio and long T2 means larger pores; converting T2 to pore size needs the surface relaxivity ρ of this sample {in_text(keys)}."),
            keys,
        ))
    echo = _echo_spacing_finding(facts, zh, soil)
    if echo:
        out.append(echo)
    if facts.early_misfit_fraction is not None and abs(facts.early_misfit_fraction) > 0.01:
        keys = ["Whittall1991NNLS"]
        below = facts.early_misfit_fraction > 0
        out.append(Finding(
            "cpmg_sampling_trim",
            (f"前 10 ms 的全分辨率残差平均为初始信号的 {facts.early_misfit_fraction:+.1%}，即拟合{'低于' if below else '高于'}早期回波，"
             f"{'短 T2 组分被低估' if below else '短 T2 组分被高估'}；应先检查首批回波（基线偏移、非理想脉冲、振铃）后再解读短 T2 部分 {in_text(keys)}。"
             if zh else
             f"Over the first 10 ms the full-resolution residual averages {facts.early_misfit_fraction:+.1%} of the initial signal: the fit lies {'below' if below else 'above'} the early echoes, so the short-T2 part is {'underestimated' if below else 'overestimated'}; check the first echoes (baseline offset, imperfect pulses, ringing) before reading it {in_text(keys)}."),
            keys,
        ))
    if facts.decay_end_fraction is not None and facts.decay_end_fraction > 0.05:
        keys = ["Coates1999NMRLogging"]
        out.append(Finding(
            "acquisition_window_too_short_for_long_t2",
            (f"衰减在采样结束时仍有初始值的 {facts.decay_end_fraction:.1%}，最长的 T2 组分没有被完全约束，长 T2 尾部的位置与面积不确定 {in_text(keys)}。"
             if zh else
             f"The decay still holds {facts.decay_end_fraction:.1%} of its initial value at the last echo, so the longest T2 components are not fully constrained {in_text(keys)}."),
            keys,
        ))
    return out


# --------------------------------------------------------------------------
# Ideal triangle pair
# --------------------------------------------------------------------------


def _pore_geometry(config: dict[str, Any]) -> dict[str, dict[str, float]]:
    from .ideal_workflow import triangle_area_um2, wetted_solid_perimeter_um

    out = {}
    for pore in ("large", "small"):
        side = float(config.get(f"{pore}_side_um", 20.0 if pore == "large" else 8.0))
        depth = float(config.get(f"{pore}_depth_um", side))
        sw = float(config.get(f"{pore}_water_saturation", 1.0))
        area = triangle_area_um2(side)
        out[pore] = {
            "side": side,
            "depth": depth,
            "sw": sw,
            "area": area,
            "water_area": sw * area,
            "wetted": wetted_solid_perimeter_um(side, sw),
            "volume": area * depth,
            "water_volume": sw * area * depth,
        }
    return out


def _rate(bulk: float, rho: float, sv: float) -> float:
    return 1.0 / bulk + rho * sv


def _ideal_findings(facts: AnalysisFacts, zh: bool) -> list[Finding]:
    info = facts.ideal or {}
    config = info.get("config", {})
    estimates = info.get("estimated_t2_ms", {})
    diffusion = float(config.get("diffusion_um2_per_ms", 2.0))
    rho = float(config.get("rho_solid_um_per_ms", 0.005))
    bulk = float(config.get("bulk_t2_ms", facts.bulk_t2_ms or 3000.0))
    geo = _pore_geometry(config)
    large, small = geo["large"], geo["small"]
    regime = rho * large["side"] / (2.0 * math.sqrt(3.0)) / diffusion
    peaks = facts.peak_positions_ms
    total_volume = large["volume"] + small["volume"]
    small_share_water = small["water_volume"] / (large["water_volume"] + small["water_volume"])
    small_capacity = small["volume"] / total_volume
    reproduces = abs(large["side"] - 20.0) < 1e-6 and abs(small["side"] - 8.0) < 1e-6 and abs(rho - 0.005) < 1e-9
    origin_keys = ["Zhou2025WRRUnsaturated"] if reproduces else []
    origin_zh = f"该双等边三角孔复现了已有模拟研究的几何与参数 {in_text(origin_keys)}：边长 20 与 8 μm，ρ = 5 μm/s。" if reproduces else ""
    origin_en = f"The triangle pair reproduces the geometry and parameters of an earlier simulation study {in_text(origin_keys)}: sides of 20 and 8 μm and ρ = 5 μm/s. " if reproduces else ""
    out: list[Finding] = []
    est_l, est_s = estimates.get("large"), estimates.get("small")

    if config.get("coupled"):
        width = float(config.get("throat_width_um", 1.0))
        length = float(config.get("throat_length_um", 5.0))
        # Fast-exchange limit: wetted wall of both pores (minus the two throat openings) over all water.
        wall = large["wetted"] + small["wetted"] - 2.0 * width
        water = large["water_area"] + small["water_area"] + length * width
        t2_fx = 1.0 / _rate(bulk, rho, wall / water)
        k_ex = diffusion * width / length * (1.0 / large["water_area"] + 1.0 / small["water_area"])
        delta_r = abs(rho * (small["wetted"] / small["water_area"] - large["wetted"] / large["water_area"]))
        ratio = k_ex / delta_r if delta_r > 0 else math.inf
        main = facts.main_peak_ms or (max(peaks) if peaks else None)
        if ratio > 3:
            state_zh, state_en = "交换远快于两孔弛豫速率之差，处于快交换，两孔表现为一个孔", "exchange is much faster than the difference of the two relaxation rates (fast exchange), so the pair behaves as one pore"
        elif ratio > 0.3:
            state_zh, state_en = "交换与两孔弛豫速率之差相当，处于中间交换，两峰部分合并", "exchange is comparable with the difference of the two relaxation rates (intermediate exchange), so the peaks partly merge"
        else:
            state_zh, state_en = "交换慢于两孔弛豫速率之差，两孔基本各自弛豫", "exchange is slower than the difference of the two relaxation rates, so each pore relaxes largely on its own"
        keys = ["McCall1991RestrictedDiffusion", "Fleury2009PoreCoupling"]
        single = main is not None and len(peaks) <= 1
        if single and main:
            a_eq = 4.0 * math.sqrt(3.0) * rho / max(1.0 / main - 1.0 / bulk, 1e-12)
            peak_zh = (f"两孔经 {_fmt(length)} μm × {_fmt(width)} μm 的喉道连通，反演只得到一个 {_fmt(main)} ms 的峰：比大孔估计 {_fmt(est_l)} ms 短 {1 - main / est_l:.0%}，比全部含水域 S/V 给出的快交换极限 {_fmt(t2_fx)} ms 长 {main / t2_fx - 1:.0%}。"
                       if est_l else f"两孔经喉道连通，反演只得到一个 {_fmt(main)} ms 的峰，快交换极限为 {_fmt(t2_fx)} ms。")
            peak_en = (f"The pores are joined by a {_fmt(length)} μm × {_fmt(width)} μm throat and the inversion returns one peak at {_fmt(main)} ms, {1 - main / est_l:.0%} below the large-pore estimate of {_fmt(est_l)} ms and {main / t2_fx - 1:.0%} above the fast-exchange limit of {_fmt(t2_fx)} ms set by the S/V of all the water. "
                       if est_l else f"The pores are joined by a throat and the inversion returns one peak at {_fmt(main)} ms; the fast-exchange limit is {_fmt(t2_fx)} ms. ")
            tail_zh = f"小孔中 {_pct(small_share_water)} 的水并入了这个峰；若按单个饱和三角孔解读，它对应边长约 {_fmt(a_eq)} μm 的孔，而实际是 {_fmt(large['side'])} 与 {_fmt(small['side'])} μm 两个孔，所以单峰不等于单一孔群"
            tail_en = f"The {_pct(small_share_water)} of the water in the small pore is merged into this peak; read as one saturated triangle it implies a side of about {_fmt(a_eq)} μm, whereas the pores are {_fmt(large['side'])} and {_fmt(small['side'])} μm, so one peak is not one pore family"
        else:
            listed = ", ".join(f"{_fmt(p)} ms" for p in peaks) or "—"
            peak_zh = f"两孔经 {_fmt(length)} μm × {_fmt(width)} μm 的喉道连通，反演峰位于 {listed}，快交换极限为 {_fmt(t2_fx)} ms。"
            peak_en = f"The pores are joined by a {_fmt(length)} μm × {_fmt(width)} μm throat; the inverted peaks lie at {listed} and the fast-exchange limit is {_fmt(t2_fx)} ms. "
            tail_zh = "交换使两峰向彼此靠拢，峰面积不再等于各孔的水量"
            tail_en = "Exchange pulls the peaks together, so their areas no longer equal the water held by each pore"
        out.append(Finding(
            "pore_coupling_exchange",
            (f"{origin_zh}{peak_zh}"
             f"喉道交换时间约 {1.0 / k_ex:.0f} ms，约为 T2 的 1/{(main or t2_fx) * k_ex:.0f}，交换速率是两孔表面弛豫速率差的 {ratio:.1f} 倍：{state_zh} {in_text(keys)}。"
             f"{tail_zh} {in_text(['Grunewald2009PoreCoupling'])}。饱和度降低时含水通道变得曲折并最终断开，耦合随之减弱 {in_text(['Zhou2026GRLExchange'])}；本工具在 Sw ≤ 0.395 时不允许耦合，因为角隅水不再接触喉道。"
             if zh else
             f"{origin_en}{peak_en}"
             f"Exchange through the throat takes about {1.0 / k_ex:.0f} ms, about 1/{(main or t2_fx) * k_ex:.0f} of T2, and the exchange rate is {ratio:.1f} times the difference of the two surface-relaxation rates: {state_en} {in_text(keys)}. "
             f"{tail_en} {in_text(['Grunewald2009PoreCoupling'])}. As saturation falls the water paths become tortuous and finally disconnect, which weakens coupling {in_text(['Zhou2026GRLExchange'])}; this tool does not allow coupling at Sw ≤ 0.395, where corner water no longer reaches the throat."),
            origin_keys + keys + ["Grunewald2009PoreCoupling", "Zhou2026GRLExchange"],
        ))
    else:
        keys = ["BrownsteinTarr1979"]
        matches = []
        for est, name_zh, name_en in ((est_s, "小孔", "small"), (est_l, "大孔", "large")):
            if est and peaks:
                nearest = min(peaks, key=lambda p: abs(math.log10(p / est)))
                matches.append((name_zh, name_en, est, nearest, nearest / est - 1.0))
        listed_zh = "；".join(f"{z}估计 {_fmt(e)} ms ↔ 峰 {_fmt(p)} ms（{d:+.0%}）" for z, _, e, p, d in matches)
        listed_en = "; ".join(f"{n} estimate {_fmt(e)} ms ↔ peak {_fmt(p)} ms ({d:+.0%})" for _, n, e, p, d in matches)
        all_close = matches and all(abs(d) <= 0.1 for *_, d in matches)
        same_peak = len(matches) == 2 and matches[0][3] == matches[1][3]
        small_area = None
        if est_l and est_s and not same_peak and facts.t2_ms is not None and facts.spectrum is not None:
            small_area = class_fractions(facts.t2_ms, facts.spectrum, (math.sqrt(est_l * est_s),))[0]
        area_zh = f"小孔峰占谱面积 {_pct(small_area)}，小孔含水体积份额为 {_pct(small_share_water)}。" if small_area is not None else ""
        area_en = f"The small-pore peak holds {_pct(small_area)} of the spectrum, against a water-volume share of {_pct(small_share_water)}." if small_area is not None else ""
        verdict_zh = ("两孔互不连通，峰位与各自的快扩散估计相差在 10% 以内，峰可以直接对应各自的孔" if all_close and not same_peak
                      else "两个孔的估计落在同一个峰上，谱上无法区分两孔" if same_peak else "峰位与估计有明显偏差")
        verdict_en = ("The pores are not connected and each peak lies within 10% of its fast-diffusion estimate, so the peaks map onto the pores" if all_close and not same_peak
                      else "Both pore estimates fall on the same peak, so the spectrum cannot separate the pores" if same_peak else "The peaks deviate clearly from the estimates")
        out.append(Finding(
            "uncoupled_peaks_match_pores",
            (f"{origin_zh}{verdict_zh}：{listed_zh}。大孔的 ρ·r/D = {regime:.3f}（r 为内切圆半径），远小于 1，处于快扩散区，T2 由 S/V 决定 {in_text(keys)}。{area_zh}"
             if zh else
             f"{origin_en}{verdict_en}: {listed_en}. For the large pore ρ·r/D = {regime:.3f} (r is the inradius), far below 1, so relaxation is in the fast-diffusion regime and T2 is set by S/V {in_text(keys)}. {area_en}"),
            origin_keys + keys,
        ))

    # Partial saturation: short T2 from small pores or from partly drained large pores.
    if min(large["sw"], small["sw"]) < 1.0 and facts.t2_ms is not None and facts.spectrum is not None:
        keys = ["Zhou2025WRRUnsaturated", "Mohnke2015TriangularPores"]
        sat_l = 1.0 / _rate(bulk, rho, 3.0 * large["side"] / large["area"])
        sat_s = 1.0 / _rate(bulk, rho, 3.0 * small["side"] / small["area"])
        cut = math.sqrt(sat_l * sat_s)
        water_fraction = (large["water_volume"] + small["water_volume"]) / total_volume
        short_share = class_fractions(facts.t2_ms, facts.spectrum, (cut,))[0] * water_fraction
        names = {"full": ("全饱和", "fully water-filled"), "bubble": ("中心气泡", "central gas bubble"), "corner": ("角隅水", "corner water")}
        configuration = {pore: names.get(kind, (kind, kind))[0 if zh else 1] for pore, kind in info.get("water_configuration", {}).items()}
        equal = est_l and est_s and abs(math.log(est_l / est_s)) < math.log(1.15)
        equal_zh = f"部分饱和的大孔与饱和的小孔估计 T2 几乎相同（{_fmt(est_l)} 与 {_fmt(est_s)} ms）：两者的含水体积与润湿面积之比相同，弛豫一样快，在谱上合成一个峰。" if equal else ""
        equal_en = f"The partly drained large pore and the small pore have nearly equal estimates ({_fmt(est_l)} and {_fmt(est_s)} ms): their ratios of water volume to wetted surface are equal, so they relax alike and merge into one peak. " if equal else ""
        if short_share > 1.2 * small_capacity:
            capacity_zh = f"容量检验：T2 < {_fmt(cut)} ms（饱和小孔与饱和大孔估计的几何中点）的信号占饱和孔隙总信号的 {_pct(short_share)}，而小孔饱和时最多只能容纳 {_pct(small_capacity)}，所以这部分短 T2 不能只归于小孔，其中至少 {_pct(short_share - small_capacity)} 来自部分排空的大孔"
            capacity_en = f"Capacity check: the signal with T2 < {_fmt(cut)} ms (the geometric midpoint of the saturated small- and large-pore estimates) is {_pct(short_share)} of the saturated signal, whereas the small pore can hold at most {_pct(small_capacity)}, so this short T2 cannot belong to the small pore alone; at least {_pct(short_share - small_capacity)} comes from the partly drained large pore"
        else:
            capacity_zh = f"容量检验：T2 < {_fmt(cut)} ms 的信号占饱和孔隙总信号的 {_pct(short_share)}，未超过小孔的饱和容量 {_pct(small_capacity)}"
            capacity_en = f"Capacity check: the signal with T2 < {_fmt(cut)} ms is {_pct(short_share)} of the saturated signal, within the {_pct(small_capacity)} the small pore can hold"
        out.append(Finding(
            "partial_saturation_capacity",
            (f"部分饱和（大孔 Sw = {large['sw']:.2f}，{configuration.get('large', '')}；小孔 Sw = {small['sw']:.2f}，{configuration.get('small', '')}）时，气相减少水的体积而孔壁仍大部分湿润，S/V 升高、T2 变短，短 T2 既可能来自小孔，也可能来自部分饱和的大孔。{equal_zh}"
             f"{capacity_zh} {in_text(keys)}。"
             if zh else
             f"Under partial saturation (large Sw = {large['sw']:.2f}, {configuration.get('large', '')}; small Sw = {small['sw']:.2f}, {configuration.get('small', '')}) gas removes water volume while much of the wall stays wet, so S/V rises and T2 shortens; short T2 can come from small pores or from partly saturated large pores. {equal_en}"
             f"{capacity_en} {in_text(keys)}."),
            keys,
        ))
    return out


# --------------------------------------------------------------------------
# Segmented CT slice
# --------------------------------------------------------------------------


def _ct_findings(facts: AnalysisFacts, zh: bool) -> list[Finding]:
    info = facts.ct or {}
    out: list[Finding] = []
    bulk, rho = facts.bulk_t2_ms, facts.rho_um_per_ms
    if facts.t2_ms is None or facts.spectrum is None or not bulk or not rho:
        return out
    t_hm = harmonic_mean_t2(facts.t2_ms, facts.spectrum)
    wall = info.get("relaxing_boundary_um")
    area = info.get("water_area_um2")
    peak = facts.main_peak_ms
    regions = None
    if info.get("labels") is not None and info.get("pixel_size_um"):
        regions = water_regions_from_labels(info["labels"], float(info["pixel_size_um"]), rho, bulk)
    porosity, sw = info.get("porosity_2d"), info.get("water_saturation_2d")
    if porosity is not None and sw is not None and peak:
        lead_zh = f"CT 切片的二维孔隙度为 {porosity:.1%}，含水饱和度为 {sw:.1%}；T2 谱是一个主峰位于 {_fmt(peak)} ms 的宽峰。"
        lead_en = f"The CT slice has a 2D porosity of {porosity:.1%} and a water saturation of {sw:.1%}; its T2 spectrum is one broad peak at {_fmt(peak)} ms. "
        region_zh = region_en = ""
        keys = ["BrownsteinTarr1979"]
        if regions and regions.get("others_share"):
            region_zh = (f"含水域由 {regions['count']} 个互不连通的水团组成：最大水团占 {_pct(regions['largest_share'])} 的水，按其边界 S/V 估计 T2 ≈ {_fmt(regions['largest_t2_ms'])} ms；"
                         f"其余较小水团占 {_pct(regions['others_share'])}，S/V 更高，估计 T2 ≈ {_fmt(regions['others_t2_ms'])} ms，弛豫更快，构成谱的短 T2 一侧，因此谱是一个向短 T2 拖尾的不对称宽峰 {in_text(keys)}。")
            region_en = (f"The water forms {regions['count']} disconnected regions: the largest holds {_pct(regions['largest_share'])} of the water with an S/V-based T2 of about {_fmt(regions['largest_t2_ms'])} ms, "
                         f"while the smaller regions hold {_pct(regions['others_share'])} at a higher S/V (about {_fmt(regions['others_t2_ms'])} ms), relax faster and form the short-T2 side, so the spectrum is one asymmetric peak with a tail towards short T2 {in_text(keys)}.")
        out.append(Finding("ct_porosity_and_water_regions", (lead_zh + region_zh) if zh else (lead_en + region_en), keys if region_zh else []))
    if t_hm and wall and area and peak:
        sv = wall / area
        predicted = 1.0 / _rate(bulk, rho, sv)
        rho_from_peak = (1.0 / peak - 1.0 / bulk) / sv
        sv_pixel = info.get("pixel_surface_to_volume_per_um")
        regime_txt_zh = regime_txt_en = ""
        sizes = facts.pore_diameter_um or {}
        if sizes.get("pore_space_median") and facts.diffusion_um2_per_ms:
            kappa = rho * 0.5 * float(sizes["pore_space_median"]) / facts.diffusion_um2_per_ms
            regime_txt_zh = f"（孔隙局部孔径中位数 {_fmt(sizes['pore_space_median'])} μm，ρ·r/D = {kappa:.2f}，接近快扩散区上限，峰相对 S/V 开始偏移）"
            regime_txt_en = f" (median local pore diameter {_fmt(sizes['pore_space_median'])} μm, ρ·r/D = {kappa:.2f}, near the fast-diffusion limit, where the peak starts to depart from S/V)"
        pixel_zh = pixel_en = ""
        if sv_pixel:
            t_pixel = 1.0 / _rate(bulk, rho, sv_pixel)
            pixel_zh = f"按像素边界计数的 S/V 为 {sv_pixel:.4f} μm⁻¹，比网格边界长 {sv_pixel / sv - 1:.0%}，对应 T2 {_fmt(t_pixel)} ms；标定 ρ 时 S/V 必须与模型使用同一种边界表示。"
            pixel_en = f"Counting pixel faces gives S/V = {sv_pixel:.4f} μm⁻¹, a boundary {sv_pixel / sv - 1:.0%} longer than the mesh, and T2 = {_fmt(t_pixel)} ms; a calibration of ρ must use the same boundary representation as the model. "
        keys = ["BrownsteinTarr1979"]
        out.append(Finding(
            "sv_first_moment_check",
            (f"谱的振幅加权调和平均 T2 为 {_fmt(t_hm)} ms，网格含水域边界 S/V = {sv:.4f} μm⁻¹ 由 1/T2 = 1/T2B + ρ·S/V 给出 {_fmt(predicted)} ms，两者相差 {_small_pct(t_hm / predicted - 1)}。这一关系由扩散–弛豫方程在含水域上积分得到（初始衰减速率），与扩散区制无关 {in_text(keys)}，说明模拟谱完全由几何决定。"
             f"主峰 {_fmt(peak)} ms 比调和平均高 {peak / t_hm - 1:.1%}{regime_txt_zh}：与实测谱比较或反算 ρ 时应使用调和平均 T2，用峰位会使 ρ 偏{'低' if rho_from_peak < rho else '高'} {abs(rho_from_peak / rho - 1):.0%}。{pixel_zh}"
             if zh else
             f"The amplitude-weighted harmonic-mean T2 of the spectrum is {_fmt(t_hm)} ms; the meshed water boundary, S/V = {sv:.4f} μm⁻¹, gives {_fmt(predicted)} ms from 1/T2 = 1/T2B + ρ·S/V, a difference of {_small_pct(t_hm / predicted - 1)}. This relation follows from integrating the diffusion-relaxation equation over the water domain (initial decay rate) and holds in any diffusion regime {in_text(keys)}, so the simulated spectrum is fully explained by the geometry. "
             f"The main peak at {_fmt(peak)} ms lies {peak / t_hm - 1:.1%} above the harmonic mean{regime_txt_en}: compare measured spectra, or back-calculate ρ, with the harmonic mean, since the peak would return a ρ {abs(rho_from_peak / rho - 1):.0%} {'low' if rho_from_peak < rho else 'high'}. {pixel_en}"),
            keys,
        ))
        surface_share = max(1e-6, 1.0 - t_hm / bulk)
        keys = ["BrownsteinTarr1979", "Kleinberg1994RelaxationMechanism"]
        out.append(Finding(
            "rho_calibration_conditioning",
            (f"体弛豫贡献了 {_pct(1 - surface_share)} 的弛豫速率，表面弛豫只占 {_pct(surface_share)}，所以 T2 对孔径不敏感；用实测 T2 反算 ρ 时，T2 的 5% 误差会放大为 ρ 的约 {5 / surface_share:.0f}%，T2B 需要在同一流体上单独测准 {in_text(keys)}。"
             if zh else
             f"Bulk relaxation supplies {_pct(1 - surface_share)} of the relaxation rate and surface relaxation only {_pct(surface_share)}, so T2 is insensitive to pore size; when ρ is back-calculated from a measured T2, a 5% error in T2 becomes about {5 / surface_share:.0f}% in ρ, and T2B must be measured separately on the same fluid {in_text(keys)}."),
            keys,
        ))
    coverage = info.get("wall_coverage")
    sw = info.get("water_saturation_2d")
    if coverage and sw is not None and sw < 0.999 and t_hm and wall and area:
        fw = coverage["wetted_wall_fraction"]
        t_sat = 1.0 / _rate(bulk, rho, wall / area * coverage["saturated_to_water_sv_ratio"])
        t_now = 1.0 / _rate(bulk, rho, wall / area)
        keys = ["Mohnke2015TriangularPores", "Falzone2016Saturation", "Behroozmand2015Review"]
        out.append(Finding(
            "saturation_wall_coverage",
            (f"二维含水饱和度为 {sw:.1%}，但水仍覆盖 {fw:.1%} 的孔壁：气相占据孔体，孔壁大多仍湿润。若孔隙全部充水，按 S/V 预测 T2 只变 {t_sat / t_now - 1:+.1%}，所以在这种充填方式下 T2 几乎不随饱和度变化，饱和度应从信号幅值读取 {in_text(keys[:2])}；"
             f"用总孔壁面积而非水润湿面积标定 ρ 会使 ρ 偏低 {1 - fw:.0%} {in_text(keys[2:])}。"
             if zh else
             f"The 2D water saturation is {sw:.1%}, yet water still covers {fw:.1%} of the pore wall: gas occupies pore bodies while the walls stay mostly wet. Filling the pores would change T2 by only {t_sat / t_now - 1:+.1%} according to S/V, so with this filling T2 barely tracks saturation and saturation should be read from the signal amplitude {in_text(keys[:2])}; "
             f"calibrating ρ on the total wall area instead of the wetted area would make ρ {1 - fw:.0%} too low {in_text(keys[2:])}."),
            keys,
        ))
    above_bulk = class_fractions(facts.t2_ms, facts.spectrum, (bulk,))[1]
    if above_bulk > 0.01:
        keys = ["Borgia1998UniformPenalty", "Coates1999NMRLogging"]
        end_zh = f"模拟在结束时信号仍有 {facts.decay_end_fraction:.0%}，" if facts.decay_end_fraction and facts.decay_end_fraction > 0.05 else ""
        end_en = f"The simulated signal still holds {facts.decay_end_fraction:.0%} at the end of the run, so " if facts.decay_end_fraction and facts.decay_end_fraction > 0.05 else "Therefore "
        out.append(Finding(
            "area_above_bulk_t2",
            (f"谱有 {above_bulk:.1%} 的面积位于 T2B = {_fmt(bulk)} ms 以上，比体相水弛豫还慢，物理上不可能，是平滑造成的展宽 {in_text(keys[:1])}。{end_zh}谱的宽度、上沿和分量份额需在约 5 倍 T2 的模拟时长下重算后才能解读，调和平均 T2 由 S/V 决定，不受影响 {in_text(keys[1:])}。"
             if zh else
             f"{above_bulk:.1%} of the spectrum lies above T2B = {_fmt(bulk)} ms, slower than bulk water, which is physically impossible; it is broadening by the smoothing {in_text(keys[:1])}. "
             f"{end_en}the width, upper edge and component shares should be recomputed with a run of about five T2 before they are read, whereas the harmonic-mean T2 is fixed by S/V {in_text(keys[1:])}."),
            keys,
        ))
    return out


# --------------------------------------------------------------------------
# Shared rules
# --------------------------------------------------------------------------


def _components_resolved(facts: AnalysisFacts, comps: list[dict[str, float]]) -> bool:
    """Two Gaussian components count as separate populations only if the spectrum shows two maxima."""

    if len(facts.peak_positions_ms) >= len(comps):
        return True
    widths = [p.get("width_log10") for p in comps if p.get("width_log10")]
    sigma = float(np.mean(widths)) / 2.3548 if widths else 0.1
    separation = abs(math.log10(comps[-1]["position_ms"] / comps[0]["position_ms"]))
    return separation > 2.0 * sigma and comps[-1]["position_ms"] / comps[0]["position_ms"] >= 3.0


def _unresolved_components(facts: AnalysisFacts, zh: bool) -> Finding | None:
    comps = sorted((p for p in facts.gaussian_peaks if p.get("position_ms") and p.get("area_fraction") is not None), key=lambda p: p["position_ms"])
    if len(comps) < 2 or _components_resolved(facts, comps):
        return None
    ratio = comps[-1]["position_ms"] / comps[0]["position_ms"]
    listed = "、".join(f"{_fmt(p['position_ms'])} ms（{_pct(p['area_fraction'])}）" for p in comps)
    listed_en = ", ".join(f"{_fmt(p['position_ms'])} ms ({_pct(p['area_fraction'])})" for p in comps)
    keys = ["Borgia1998UniformPenalty"]
    return Finding(
        "unresolved_gaussian_components",
        (f"高斯分量 {listed} 只相距 {ratio:.2f} 倍，而谱上只有一个极大值；它们描述的是一个不对称峰的形状，而不是两个水群，其面积份额没有物理意义。正则化反演中，相距约 3 倍的两条谱线在信噪比约 240 时才勉强可分 {in_text(keys)}。"
         if zh else
         f"The Gaussian components {listed_en} are only {ratio:.2f} times apart and the spectrum has a single maximum; they describe the shape of one asymmetric peak, not two water populations, and their area shares carry no physical meaning. In regularized inversion two lines three times apart are only marginally resolved at a signal-to-noise ratio of about 240 {in_text(keys)}."),
        keys,
    )


def _inversion_basis(facts: AnalysisFacts, zh: bool) -> Finding | None:
    if facts.inversion_mode == "fixed_nnls":
        keys = ["WhittallMacKay1989NNLS", "Borgia1998UniformPenalty"]
        return Finding(
            "regularization_sensitive",
            (f"T2 谱由非负正则化反演得到，本次使用固定平滑因子 α = {_fmt(facts.alpha)}；同一衰减可被多种谱同样好地拟合，峰数与峰宽依赖 α {in_text(keys)}。"
             if zh else
             f"The T2 spectrum is a non-negative regularized inversion with a fixed smoothing factor α = {_fmt(facts.alpha)}; several spectra fit the same decay equally well, so peak number and width depend on α {in_text(keys)}."),
            keys,
        )
    if facts.inversion_mode == "lcurve" and facts.alpha is not None:
        rule = facts.selection_rule or "ratio"
        keys = ["Zou2016LCurveSlope", "WhittallMacKay1989NNLS"] if rule == "ratio" else ["Hansen1992LCurve", "WhittallMacKay1989NNLS"]
        rule_zh = "L-curve 斜率准则：斜率绝对值的倒数在 0.1–10 内最接近 0.25（曲率平滑算子的推荐阈值）" if rule == "ratio" else "L-curve 最大曲率准则"
        rule_en = "the slope-of-the-L-curve criterion, the reciprocal of the absolute slope closest to 0.25 within 0.1–10 (the threshold recommended for curvature smoothing)" if rule == "ratio" else "the maximum-curvature rule"
        return Finding(
            "regularization_sensitive",
            (f"平滑因子 α = {_fmt(facts.alpha)} 由 L-curve 在残差范数与谱粗糙度之间折中选出，选择规则为{rule_zh}；同一衰减可对应多种谱，因此峰位比峰数更稳健 {in_text(keys)}。"
             if zh else
             f"The smoothing factor α = {_fmt(facts.alpha)} was chosen on the L-curve between residual norm and spectral roughness, using {rule_en}; one decay admits several spectra, so peak positions are more robust than peak counts {in_text(keys)}."),
            keys,
        )
    return None


def build_findings(facts: AnalysisFacts, language: str = "中文") -> list[Finding]:
    """Findings in reading order: what the result says about the sample first, method notes last."""

    zh = _zh(language)
    out: list[Finding] = []
    if facts.workflow == "measured":
        out.extend(_measured_findings(facts, zh))
    elif facts.ideal:
        out.extend(_ideal_findings(facts, zh))
    elif facts.ct:
        out.extend(_ct_findings(facts, zh))

    unresolved = _unresolved_components(facts, zh)
    if unresolved:
        out.append(unresolved)

    bulk = facts.bulk_t2_ms
    if facts.ideal and bulk and facts.main_peak_ms and facts.main_peak_ms > 0.5 * bulk:
        keys = ["BrownsteinTarr1979", "Kleinberg1994RelaxationMechanism"]
        surface_share = max(0.0, 1.0 - facts.main_peak_ms / bulk)
        out.append(Finding(
            "bulk_dominated",
            (f"主峰 {_fmt(facts.main_peak_ms)} ms 已接近体弛豫 T2,bulk = {_fmt(bulk)} ms，表面弛豫只贡献约 {surface_share:.0%} 的弛豫速率，T2 对孔径不敏感 {in_text(keys)}。"
             if zh else
             f"The main peak at {_fmt(facts.main_peak_ms)} ms is close to T2,bulk = {_fmt(bulk)} ms, so surface relaxation supplies only about {surface_share:.0%} of the rate and T2 is insensitive to pore size {in_text(keys)}."),
            keys,
        ))

    # A measured spectrum without Gaussian components still gets a note on its peak count.
    if facts.workflow == "measured" and len(facts.peak_positions_ms) >= 2 and not facts.gaussian_peaks:
        keys = ["WhittallMacKay1989NNLS"]
        peaks = ", ".join(f"{_fmt(p)} ms" for p in facts.peak_positions_ms)
        out.append(Finding(
            "multimodal_spectrum",
            (f"谱中有 {len(facts.peak_positions_ms)} 个峰（{peaks}），提示存在多个弛豫环境；峰数受正则化影响，可用高斯分峰检查两群是否可分 {in_text(keys)}。"
             if zh else
             f"The spectrum has {len(facts.peak_positions_ms)} peaks ({peaks}), indicating several relaxation environments; the count depends on regularization, and a Gaussian decomposition shows whether the populations separate {in_text(keys)}."),
            keys,
        ))
    if facts.t2_ms is not None and facts.spectrum is not None and facts.spectrum.size:
        upper = facts.spectrum[facts.t2_ms >= 0.5 * facts.t2_ms.max()]
        if upper.size and upper.max() > 0.05 * facts.spectrum.max():
            keys = ["Whittall1991NNLS", "Coates1999NMRLogging"]
            out.append(Finding(
                "peak_at_t2_bounds",
                ("谱在反演 T2 上限附近仍有明显幅值，长 T2 组分可能是搜索范围或正则化造成的边界效应；应扩大 T2 上限重新反演后再作物理解释 "
                 f"{in_text(keys)}。" if zh else
                 f"The spectrum keeps significant amplitude near the upper T2 bound, which may be a range or regularization artefact; extend the bound and re-invert before a physical reading {in_text(keys)}."),
                keys,
            ))
    small = [peak for peak in facts.gaussian_peaks if peak.get("area_fraction") is not None and peak["area_fraction"] < 0.02]
    if small:
        keys = ["WhittallMacKay1989NNLS", "Borgia1998UniformPenalty"]
        listed = ", ".join(f"{_fmt(peak['position_ms'])} ms ({peak['area_fraction']:.1%})" for peak in small)
        out.append(Finding(
            "gaussian_overfit_or_bad_residual",
            (f"高斯分峰中面积占比低于 2% 的组分（{listed}）在反演的非唯一性范围内，不宜解释为独立孔群 {in_text(keys)}。"
             if zh else
             f"Gaussian components below 2% of the area ({listed}) lie within the non-uniqueness of the inversion and should not be read as separate pore populations {in_text(keys)}."),
            keys,
        ))
    basis = _inversion_basis(facts, zh)
    if basis:
        out.append(basis)
    return out


def render_section(findings: list[Finding], language: str = "中文") -> tuple[list[str], list[str]]:
    """Markdown lines for the findings and the AGU reference list, plus the cited keys."""

    zh = _zh(language)
    refs = load_references()
    if not findings:
        return [], []
    lines = ["## 文献依据的解释" if zh else "## Literature-Based Interpretation", ""]
    for finding in findings:
        lines.append(f"- {finding.text}")
    lines.append("")
    # AGU order: first author, then later authors alphabetically ("&" ignored).
    cited = sorted({key for finding in findings for key in finding.keys if key in refs}, key=lambda key: " ".join(refs[key]["reference_agu"].lower().replace("&", "").split()))
    if cited:
        lines.append("## 参考文献" if zh else "## References")
        lines.append("")
        lines.extend(refs[key]["reference_agu"] for key in cited)
        lines.append("")
    return lines, cited
