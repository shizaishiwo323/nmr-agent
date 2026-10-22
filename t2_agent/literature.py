"""Literature-backed interpretation of T2 results with AGU-style citations.

The knowledge base in ``docs/nmr_t2_literature_knowledge`` holds the citation
keys, verified AGU references (Crossref-checked DOIs or book title pages) and
the scenario map. This module turns the numbers of one analysis into short,
specific statements, each tied to the papers that support it, and returns a
reference list. Only references marked ``reference_verified`` are cited.
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
    early_misfit_fraction: float | None = None
    decay_end_fraction: float | None = None
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
    return f"{value:.0f}" if abs(value) >= 1000 else f"{value:.3g}"


def spectrum_peaks(t2_ms: np.ndarray, amplitude: np.ndarray) -> list[float]:
    """Positions of the spectral maxima that carry at least 5% of the maximum."""

    from scipy.signal import find_peaks

    amp = np.asarray(amplitude, dtype=float)
    if amp.size < 3 or not np.isfinite(amp).any() or amp.max() <= 0:
        return []
    index, _ = find_peaks(amp, height=0.05 * amp.max(), prominence=0.03 * amp.max())
    return [float(t2_ms[i]) for i in index]


def early_time_misfit(trimmed_xlsx: Path, early_ms: float = 10.0) -> tuple[float | None, float | None]:
    """Mean full-resolution residual before ``early_ms`` and the final signal, both relative to the first sample."""

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


def build_findings(facts: AnalysisFacts, language: str = "中文") -> list[Finding]:
    zh = _zh(language)
    out: list[Finding] = []

    # Inversion basis --------------------------------------------------------
    if facts.inversion_mode == "fixed_nnls":
        keys = ["WhittallMacKay1989NNLS", "Borgia1998UniformPenalty"]
        out.append(Finding(
            "regularization_sensitive",
            (f"T2 谱由多指数衰减的非负正则化反演得到；本次使用固定平滑因子 α = {_fmt(facts.alpha)}。同一衰减可被多种谱同样好地拟合，且单一固定平滑因子可能展宽尖峰或把拖尾拆成小峰，峰数与峰宽应结合 α 的敏感性理解 {in_text(keys)}。"
             if zh else
             f"The T2 spectrum is a non-negative regularized inversion of a multi-exponential decay, here with a fixed smoothing factor α = {_fmt(facts.alpha)}. Different spectra can fit the same decay equally well, and a single fixed factor can broaden sharp peaks or split a tail into small peaks, so peak number and width depend on α {in_text(keys)}."),
            keys,
        ))
    elif facts.inversion_mode == "lcurve" and facts.alpha is not None:
        keys = ["Hansen1992LCurve", "WhittallMacKay1989NNLS"]
        rule = facts.selection_rule or "ratio"
        rule_zh = "斜率倒数最接近 0.25 的准则（本工具的规则，不是 Hansen 的最大曲率拐角）" if rule == "ratio" else "L-curve 最大曲率准则"
        rule_en = "the slope-reciprocal ratio closest to 0.25 (this tool's rule, not Hansen's maximum-curvature corner)" if rule == "ratio" else "the maximum-curvature rule"
        out.append(Finding(
            "regularization_sensitive",
            (f"平滑因子 α = {_fmt(facts.alpha)} 由 L-curve 在残差范数与谱粗糙度之间折中选出，选择规则为{rule_zh}。逆 Laplace 反演是病态问题，同一衰减可对应多种谱，因此峰位比峰数更稳健 {in_text(keys)}。"
             if zh else
             f"The smoothing factor α = {_fmt(facts.alpha)} was chosen on the L-curve as a compromise between residual norm and spectral roughness, using {rule_en}. The inverse Laplace problem is ill-posed and one decay admits several spectra, so peak positions are more robust than peak counts {in_text(keys)}."),
            keys,
        ))

    # Early-time misfit -------------------------------------------------------
    if facts.early_misfit_fraction is not None and abs(facts.early_misfit_fraction) > 0.01:
        keys = ["Whittall1991NNLS"]
        out.append(Finding(
            "cpmg_sampling_trim",
            (f"前 10 ms 的全分辨率残差平均为初始信号的 {facts.early_misfit_fraction:+.1%}，反演对早期回波存在系统偏差。CPMG 数据中的基线偏移、非理想 180° 脉冲和早期振铃会影响短 T2 组分的恢复，短 T2 部分应谨慎解释，必要时检查采集设置或剔除首批回波后重新反演 {in_text(keys)}。"
             if zh else
             f"Over the first 10 ms the full-resolution residual averages {facts.early_misfit_fraction:+.1%} of the initial signal, a systematic early-echo misfit. Baseline offsets, imperfect 180° pulses and ringing in CPMG data affect the short-T2 part, which should be read with caution; check the acquisition or re-invert without the first echoes {in_text(keys)}."),
            keys,
        ))
    if facts.decay_end_fraction is not None and facts.decay_end_fraction > 0.05:
        keys = ["Whittall1991NNLS", "Coates1999NMRLogging"]
        out.append(Finding(
            "acquisition_window_too_short_for_long_t2",
            (f"衰减在采样结束时仍有初始值的 {facts.decay_end_fraction:.1%}，最长的 T2 组分没有被完全约束，长 T2 尾部的位置与面积不确定 {in_text(keys)}。"
             if zh else
             f"The decay still holds {facts.decay_end_fraction:.1%} of its initial value at the last echo, so the longest T2 components are not fully constrained {in_text(keys)}."),
            keys,
        ))

    # Relaxation regime and pore size -----------------------------------------
    if facts.workflow == "measured":
        keys = ["BrownsteinTarr1979", "Kleinberg1994RelaxationMechanism"]
        out.append(Finding(
            "short_t2_dominant",
            ((f"主峰位于约 {_fmt(facts.main_peak_ms)} ms。" if facts.main_peak_ms else "")
             + f"在快扩散区制下 1/T2 ≈ 1/T2,bulk + ρ·S/V，T2 分布可近似映射孔隙表面积/体积比，长 T2 对应较大孔隙 {in_text(keys)}；"
             f"但换算孔径需要已知表面弛豫率 ρ，而 ρ 随孔壁矿物（尤其含铁、锰的顺磁矿物）变化可达两个数量级，石英砂约 0.3 μm/s、赤铁矿包覆约 18 μm/s {in_text(['Foley1996ParamagneticIons', 'KeatingKnight2007IronOxides'])}。"
             if zh else
             (f"The main peak lies near {_fmt(facts.main_peak_ms)} ms. " if facts.main_peak_ms else "")
             + f"In the fast-diffusion regime 1/T2 ≈ 1/T2,bulk + ρ·S/V, so the T2 distribution maps the surface-to-volume distribution and long T2 corresponds to larger pores {in_text(keys)}; "
             f"converting to pore size needs the surface relaxivity ρ, which varies by about two orders of magnitude with wall mineralogy, from ≈0.3 μm/s for quartz sand to ≈18 μm/s for hematite coatings {in_text(['Foley1996ParamagneticIons', 'KeatingKnight2007IronOxides'])}."),
            keys + ["Foley1996ParamagneticIons", "KeatingKnight2007IronOxides"],
        ))
        keys = ["KleinbergHorsfield1990TransverseRelaxation", "Hurlimann1998EffectiveGradients"]
        out.append(Finding(
            "internal_gradient_shortening",
            (f"若测量场强较高或回波间隔较长，颗粒与孔隙水的磁化率差会产生内部梯度，使大孔组分的 T2 额外缩短；报告 T2 时应注明回波间隔，并优先在低场、短回波间隔下比较样品 {in_text(keys)}。"
             if zh else
             f"At higher field or longer echo spacing, susceptibility contrast between grains and water creates internal gradients that shorten T2 of the large-pore components; report the echo spacing and compare samples at low field and short echo spacing {in_text(keys)}."),
            keys,
        ))

    if facts.workflow in {"ideal", "ct"}:
        keys = ["Mitchell2019FiniteElementNMR"]
        out.append(Finding(
            "fem_fvm_mesh_model",
            ("该谱来自有限元求解扩散-弛豫方程得到的模拟衰减，表面弛豫以 Robin 边界条件进入；数值结果依赖网格与时间步，应与网格细化检查一起解释 "
             f"{in_text(keys)}。"
             if zh else
             "The spectrum comes from a finite-element solution of the diffusion-relaxation equation, with surface relaxation entering as a Robin boundary condition; the numerical result depends on the mesh and time step and should be read with a refinement check "
             f"{in_text(keys)}."),
            keys,
        ))

    if facts.ideal:
        info = facts.ideal
        config = info.get("config", {})
        estimates = info.get("estimated_t2_ms", {})
        diffusion = float(config.get("diffusion_um2_per_ms", 2.0))
        rho = float(config.get("rho_solid_um_per_ms", 0.005))
        side = float(config.get("large_side_um", 20.0))
        inradius = side / (2.0 * math.sqrt(3.0))
        regime = rho * inradius / diffusion
        keys = ["BrownsteinTarr1979", "MullerPetke2015DiffusionRegimes"]
        peaks = ", ".join(f"{_fmt(p)} ms" for p in facts.peak_positions_ms) or "—"
        matches = []
        for pore, (label_zh, label_en) in (("large", ("大孔", "large")), ("small", ("小孔", "small"))):
            estimate = estimates.get(pore)
            if estimate and facts.peak_positions_ms:
                nearest = min(facts.peak_positions_ms, key=lambda p: abs(math.log10(p / estimate)))
                matches.append((label_zh, label_en, estimate, nearest, nearest / estimate - 1.0))
        match_zh = "；".join(f"{zh_label}估计 {_fmt(est)} ms ↔ 最近反演峰 {_fmt(peak)} ms（{diff:+.0%}）" for zh_label, _, est, peak, diff in matches)
        match_en = "; ".join(f"{en_label} estimate {_fmt(est)} ms ↔ nearest peak {_fmt(peak)} ms ({diff:+.0%})" for _, en_label, est, peak, diff in matches)
        out.append(Finding(
            "fast_diffusion_assumption_breakdown",
            (f"大孔的 ρ·r/D = {regime:.3f}（r 为内切圆半径 {inradius:.2f} μm），远小于 1，处于快扩散区制，T2 由 S/V 控制而非孔内扩散时间 {in_text(keys)}。"
             f"反演谱峰位于 {peaks}；{match_zh}。"
             if zh else
             f"For the large pore ρ·r/D = {regime:.3f} (r is the inradius, {inradius:.2f} μm), far below 1, so the pore is in the fast-diffusion regime and T2 is set by S/V rather than by diffusion time {in_text(keys)}. "
             f"The inverted peaks lie at {peaks}; {match_en}."),
            keys,
        ))
        if config.get("coupled"):
            keys = ["McCall1991RestrictedDiffusion", "Grunewald2009PoreCoupling", "Song2014PoreCouplingReview"]
            out.append(Finding(
                "broad_or_merged_peaks",
                (f"两孔经喉道（长 {_fmt(float(config.get('throat_length_um', 0)))} μm、宽 {_fmt(float(config.get('throat_width_um', 0)))} μm）连通，水分子可在孔间扩散交换，大小孔的弛豫环境被部分平均，峰会向彼此靠拢甚至合并；单峰不说明只有一个孔群 {in_text(keys)}。"
                 if zh else
                 f"The pores are joined by a throat ({_fmt(float(config.get('throat_length_um', 0)))} μm long, {_fmt(float(config.get('throat_width_um', 0)))} μm wide), so water exchanges between them and their relaxation environments are partly averaged; peaks move together or merge, and one peak does not imply one pore population {in_text(keys)}."),
                keys,
            ))
        saturations = [float(config.get("large_water_saturation", 1.0)), float(config.get("small_water_saturation", 1.0))]
        if min(saturations) < 1.0:
            keys = ["Mohnke2015TriangularPores"]
            names = {"full": ("全饱和", "fully water-filled"), "bubble": ("中心气泡", "central gas bubble"), "corner": ("角隅水", "corner water")}
            kinds = set(info.get("water_configuration", {}).values())
            configuration = {pore: names.get(kind, (kind, kind))[0 if zh else 1] for pore, kind in info.get("water_configuration", {}).items()}
            if "corner" in kinds:
                how_zh = "水退到三角形角隅，固-液接触仅剩角部两侧，接触长度/水面积比增大"
                how_en = "water retreats into the triangle corners, so the solid-water contact per water area increases"
            else:
                how_zh = "气泡占据孔中心而水沿孔壁连续分布，固-液接触长度不变但水面积减小"
                how_en = "a gas bubble occupies the pore centre while water still lines the whole wall, so the contact length is unchanged but the water area shrinks"
            out.append(Finding(
                "partial_saturation",
                (f"部分饱和（大孔 Sw = {saturations[0]:.2f}，{configuration.get('large', '')}；小孔 Sw = {saturations[1]:.2f}，{configuration.get('small', '')}）时，{how_zh}，因此 S/V 升高、T2 变短；同一孔隙在不同饱和度下给出不同 T2，不能把 T2 变化直接读成孔径变化 {in_text(keys)}。"
                 if zh else
                 f"Under partial saturation (large Sw = {saturations[0]:.2f}, {configuration.get('large', '')}; small Sw = {saturations[1]:.2f}, {configuration.get('small', '')}) {how_en}; S/V therefore rises and T2 shortens, and the same pore gives different T2 at different saturation, so a T2 shift is not a pore-size change {in_text(keys)}."),
                keys,
            ))

    bulk = facts.bulk_t2_ms
    if bulk and facts.main_peak_ms and facts.workflow in {"ideal", "ct"} and facts.main_peak_ms > 0.5 * bulk:
        keys = ["BrownsteinTarr1979", "Kleinberg1994RelaxationMechanism"]
        surface_share = max(0.0, 1.0 - facts.main_peak_ms / bulk)
        out.append(Finding(
            "bulk_dominated",
            (f"主峰 {_fmt(facts.main_peak_ms)} ms 已接近体弛豫 T2,bulk = {_fmt(bulk)} ms，表面弛豫只贡献约 {surface_share:.0%} 的弛豫速率；此时 T2 对孔径不敏感，孔径差异主要被体弛豫掩盖，若要分辨孔隙尺寸需更高表面弛豫率或更小孔隙 {in_text(keys)}。"
             if zh else
             f"The main peak at {_fmt(facts.main_peak_ms)} ms is close to the bulk value T2,bulk = {_fmt(bulk)} ms, so surface relaxation supplies only about {surface_share:.0%} of the relaxation rate; T2 is then insensitive to pore size, which bulk relaxation largely masks {in_text(keys)}."),
            keys,
        ))

    sizes = facts.pore_diameter_um or {}
    if facts.ct and sizes.get("pore_space_median") and facts.rho_um_per_ms and facts.diffusion_um2_per_ms:
        radius = 0.5 * float(sizes["pore_space_median"])
        regime = facts.rho_um_per_ms * radius / facts.diffusion_um2_per_ms
        keys = ["BrownsteinTarr1979", "MullerPetke2015DiffusionRegimes"]
        # Brownstein & Tarr (1979): fast diffusion for rho*a/D << 1, slow diffusion for >> 1.
        if regime < 0.1:
            state_zh, state_en = "远小于 1，处于快扩散区制", "far below 1 (fast-diffusion regime)"
        elif regime < 1.0:
            state_zh, state_en = "小于 1，仍属快扩散区制，但已接近其上限，较大孔隙的 T2-孔径换算会有偏差", "below 1, still fast diffusion but near its limit, so the T2-to-size conversion of the larger pores is biased"
        elif regime < 10.0:
            state_zh, state_en = "介于 1 与 10 之间，处于中间区制，快扩散换算孔径会有明显偏差", "between 1 and 10 (intermediate regime; fast-diffusion pore sizes are clearly biased)"
        else:
            state_zh, state_en = "远大于 1，处于慢扩散区制", "far above 1 (slow-diffusion regime)"
        out.append(Finding(
            "fast_diffusion_assumption_breakdown",
            (f"孔隙空间的局部孔径（最大内切圆直径）中位数为 {_fmt(sizes['pore_space_median'])} μm，对应 ρ·r/D = {regime:.3f}，{state_zh} {in_text(keys)}。"
             if zh else
             f"The median local pore diameter (largest inscribed disk) of the pore space is {_fmt(sizes['pore_space_median'])} μm, giving ρ·r/D = {regime:.3f}, {state_en} {in_text(keys)}."),
            keys,
        ))

    if facts.ct:
        info = facts.ct
        sw = info.get("water_saturation_2d")
        if sw is not None and sw < 0.999:
            keys = ["Mohnke2015TriangularPores", "KleinbergHorsfield1990TransverseRelaxation"]
            out.append(Finding(
                "partial_saturation",
                (f"CT 切片的二维含水饱和度为 {sw:.1%}；气-水界面在模型中不产生表面弛豫，部分饱和改变了含水区的 S/V，T2 变化同时反映孔径和水的占据方式 {in_text(keys[:1])}。二维切片不代表三维孔隙网络的连通性。"
                 if zh else
                 f"The 2D water saturation of the CT slice is {sw:.1%}; gas-water interfaces do not relax in the model, and partial saturation changes the S/V of the water domain, so T2 reflects both pore size and water occupancy {in_text(keys[:1])}. A 2D slice does not represent 3D connectivity."),
                keys[:1],
            ))

    # Spectrum shape ----------------------------------------------------------
    if len(facts.peak_positions_ms) >= 2:
        keys = ["WhittallMacKay1989NNLS", "Grunewald2009PoreCoupling"]
        peaks = ", ".join(f"{_fmt(p)} ms" for p in facts.peak_positions_ms)
        out.append(Finding(
            "multimodal_spectrum",
            (f"谱中有 {len(facts.peak_positions_ms)} 个峰（{peaks}），提示存在多个弛豫环境；峰数受正则化影响，且孔间耦合会改变各峰的位置与面积，不宜把每个峰直接当作独立孔群 {in_text(keys)}。"
             if zh else
             f"The spectrum has {len(facts.peak_positions_ms)} peaks ({peaks}), indicating several relaxation environments; the count depends on regularization and pore coupling shifts their positions and areas, so each peak is not automatically a separate pore population {in_text(keys)}."),
            keys,
        ))
    if facts.long_fraction is not None and facts.long_fraction > 0.1 and facts.t2_ms is not None and facts.spectrum is not None:
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
