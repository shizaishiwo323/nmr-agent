"""Add verified AGU-style references to the literature knowledge base.

For every citation key used by the interpretation scenarios, the script takes the
DOI already found in the PDF (text layer or metadata), queries Crossref, and
stores the AGU reference, the in-text form and the Crossref title in
literature_manifest.enriched.json. Keys without a DOI or whose Crossref title
does not match the card are left unverified, and the agent will not cite them.

Usage: python scripts/enrich_literature_references.py [--refresh]
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import time
import urllib.request
from pathlib import Path

KB = Path(__file__).resolve().parents[1] / "docs" / "nmr_t2_literature_knowledge"
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>,;]+")

# DOIs that the automatic scan cannot read (metadata only) or reads wrongly.
DOI_OVERRIDES = {
    "Whittall1991NNLS": "10.1016/0022-2364(91)90213-D",
    "Mohnke2010PoreScaleSimulation": None,  # scan returned a journal ISSN, not a DOI
    "Mohnke2014LBMNMR": None,
}

# Books without DOIs; entered from the title pages of the PDFs in the library.
BOOKS = {
    "Coates1999NMRLogging": {
        "reference_agu": "Coates, G. R., Xiao, L., & Prammer, M. G. (1999). NMR logging: Principles and applications. Houston, TX: Halliburton Energy Services.",
        "in_text": "Coates et al., 1999",
        "year": 1999,
    },
    "Dunn2002PorousMediaNMR": {
        "reference_agu": "Dunn, K.-J., Bergman, D. J., & Latorraca, G. A. (2002). Nuclear magnetic resonance: Petrophysical and logging applications. Oxford, UK: Pergamon.",
        "in_text": "Dunn et al., 2002",
        "year": 2002,
    },
}


# Papers added after the PDF library scan: DOI, library category, and why the agent cites them.
# Each claim the agent draws from them was checked against the full text (page or section noted).
EXTRA_PAPERS = {
    "Bayer2010SoilNMR": {
        "doi": "10.2174/1874769801003010015",
        "category": "05_soil_organic_matter",
        "selection_reason": "土壤与泥炭水状态的 T2 经验分类：<60 ms 微孔/紧束缚水，60–300 ms 中孔/松束缚水，>300 ms 大孔/体相水（p. 18）。",
    },
    "Jaeger2010PeatSwelling": {
        "doi": "10.2174/1874769801003010027",
        "category": "05_soil_organic_matter",
        "selection_reason": "泥炭提取孔隙水 T2B = 2.0 ± 0.3 s（p. 35）；T2 < 30 ms 的水扩散系数降低（p. 37）；风干泥炭不冻水 T2 ≈ 0.27–0.29 ms（p. 39）。",
    },
    "CostabelStange2025Peat": {
        "doi": "10.1016/j.geoderma.2025.117244",
        "category": "05_soil_organic_matter",
        "selection_reason": "泥炭 NMR：有机聚合物网络（水凝胶效应）与顺磁中心使 T2 缩短，分解程度越高弛豫越快（Sections 2.2, 4.2, 4.3）。",
    },
    "Mashhadi2025SDRPeat": {
        "doi": "10.1016/j.jhydrol.2025.134060",
        "category": "05_soil_organic_matter",
        "selection_reason": "未分解泥炭中完整植物细胞的水可主导 NMR 信号，但可能是几乎不参与渗流的死端孔（Section 5.1）。",
    },
    "Peng2023Bentonite": {
        "doi": "10.1002/vzj2.20284",
        "category": "05_soil_organic_matter",
        "selection_reason": "低场 NMR（TE 100–200 µs）中膨润土吸附水 T2 约 0.05–0.13 ms，毛细水 ≥ 0.3 ms（Sections 4.3, 5）。",
    },
    "Zhou2025WRRUnsaturated": {
        "doi": "10.1029/2024WR038139",
        "category": "02_simulation_geometry",
        "selection_reason": "双等边三角孔（20 与 8 µm，ρ = 5 µm/s）的部分饱和模拟：不饱和大孔与饱和小孔在 V/S 相同时给出相同的短 T2；用各孔饱和容量检验峰的归属（Sections 4.2, 5, 7）。",
    },
    "Zhou2026GRLExchange": {
        "doi": "10.1029/2025GL120450",
        "category": "03_pore_coupling",
        "selection_reason": "饱和度降低使含水通道变得曲折并最终断开，孔间流体交换受限（摘要）。",
    },
    "Falzone2016Saturation": {
        "doi": "10.3997/1873-0604.2016001",
        "category": "05_soil_organic_matter",
        "selection_reason": "砂样 T2 随饱和度的变化取决于扩散区制、孔隙充填方式、ρ 与孔径（摘要）。",
    },
    "Behroozmand2015Review": {
        "doi": "10.1007/s10712-014-9304-0",
        "category": "01_core_theory_inversion",
        "selection_reason": "近地表 NMR 综述：用 BET 总面积而非水润湿面积标定表面弛豫率会导致偏差。",
    },
}

# Crossref lists only the first author of these records, or splits a name wrongly;
# the author lists below are taken from the first page of each PDF.
AUTHOR_OVERRIDES = {
    "Bayer2010SoilNMR": ("Bayer, J. V., Jaeger, F., & Schaumann, G. E.", "Bayer et al., 2010"),
    "Jaeger2010PeatSwelling": ("Jaeger, F., Shchegolikhina, A., Van As, H., & Schaumann, G. E.", "Jaeger et al., 2010"),
    "Mashhadi2025SDRPeat": ("Mashhadi, S. R., Keating, K., Petersen, R. J., Parra, A. O., Costabel, S., Beisembina, G., Hiller, T., & Grombacher, D.", "Mashhadi et al., 2025"),
}


def _initials(given: str) -> str:
    # Handles "Rosemary", "R.L.", "R. L." and hyphenated "Jean-Pierre" / "J.-P.".
    out: list[str] = []
    for token in re.findall(r"-?[^\W\d_][^\s.\-]*", given):
        if token.startswith("-") and out:
            out[-1] += f"-{token[1]}."
        else:
            out.append(f"{token.lstrip('-')[0]}.")
    return " ".join(out)


def clean_title(raw: str) -> str:
    """Strip MathML/HTML markup that Crossref keeps in some titles."""

    text = re.sub(r"<[^>]+>", " ", raw)
    text = " ".join(text.split())
    text = re.sub(r"\bT (\d)\b", r"T\1", text)
    text = re.sub(r"(T\d) [−-] (T\d)", r"\1–\2", text)
    return text


def agu_reference(message: dict) -> tuple[str, str, int | None]:
    authors = message.get("author", [])
    names = []
    for author in authors:
        family = author.get("family") or author.get("name") or ""
        given = author.get("given") or ""
        names.append(f"{family}, {_initials(given)}".strip().rstrip(","))
    if len(names) == 1:
        author_text = names[0]
    elif len(names) == 2:
        author_text = f"{names[0]}, & {names[1]}"
    else:
        author_text = ", ".join(names[:-1]) + f", & {names[-1]}"
    # The print issue year is what readers find on the journal page.
    for date_key in ("published-print", "issued", "published-online"):
        parts = (message.get(date_key) or {}).get("date-parts", [[None]])[0]
        if parts and parts[0]:
            year = parts[0]
            break
    else:
        year = None
    title = clean_title((message.get("title") or [""])[0])
    journal = re.sub(r"\s*\(\d{4}\)$", "", (message.get("container-title") or [""])[0])
    volume = message.get("volume")
    issue = message.get("issue")
    pages = message.get("page") or message.get("article-number")
    detail = journal
    if volume:
        detail += f", {volume}"
        if issue:
            detail += f"({issue})"
    if pages:
        detail += f", {pages.replace('-', '–')}"
    doi = message.get("DOI")
    title_text = title if title.endswith(("?", "!")) else f"{title}."
    reference = f"{author_text} ({year}). {title_text} {detail}. https://doi.org/{doi}"
    families = [author.get("family") or author.get("name") or "" for author in authors]
    if len(families) == 1:
        in_text = f"{families[0]}, {year}"
    elif len(families) == 2:
        in_text = f"{families[0]} & {families[1]}, {year}"
    else:
        in_text = f"{families[0]} et al., {year}"
    return reference, in_text, year


def crossref(doi: str) -> dict:
    request = urllib.request.Request(f"https://api.crossref.org/works/{doi}", headers={"User-Agent": "nmr-agent literature check"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))["message"]


def scan_doi(entry: dict) -> str | None:
    cache = KB / entry["text_cache"].replace("\\", "/")
    text = cache.read_text(encoding="utf-8", errors="ignore")[:6000] if cache.exists() else ""
    match = DOI_RE.search(json.dumps(entry.get("metadata", {})) + " " + text)
    return match.group(0).rstrip(".)") if match else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="query Crossref again for keys that already have a reference")
    args = parser.parse_args()
    manifest_path = KB / "literature_manifest.enriched.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenarios = json.loads((KB / "result_interpretation_scenarios.json").read_text(encoding="utf-8"))
    cited = {key for scenario in scenarios for key in scenario["citations"]} | set(EXTRA_PAPERS)
    known = {entry["citation_key"] for entry in manifest}
    for key, paper in EXTRA_PAPERS.items():
        if key not in known:
            manifest.append({"citation_key": key, "agent_citation_key": key, "card_md": f"papers\\{key}.md", **paper})
    report = []
    for entry in manifest:
        key = entry["citation_key"]
        if key not in cited:
            continue
        if entry.get("reference_agu") and entry.get("reference_verified") and not args.refresh:
            continue
        if key in BOOKS:
            entry.update(BOOKS[key] | {"reference_verified": True, "reference_source": "book title page"})
            report.append((key, "book"))
            continue
        doi = DOI_OVERRIDES.get(key, entry.get("doi") or scan_doi(entry))
        if not doi:
            entry["reference_verified"] = False
            report.append((key, "no DOI"))
            continue
        try:
            message = crossref(doi)
        except Exception as exc:  # network or unknown DOI
            entry["reference_verified"] = False
            report.append((key, f"crossref failed: {exc}"))
            time.sleep(1.0)
            continue
        reference, in_text, year = agu_reference(message)
        if key in AUTHOR_OVERRIDES:
            authors, in_text = AUTHOR_OVERRIDES[key]
            reference = f"{authors} ({year})." + reference.split(").", 1)[1]
        crossref_title = clean_title((message.get("title") or [""])[0])
        card_title = entry.get("title") or entry.get("metadata", {}).get("/Title") or entry.get("pdf_name", "") or crossref_title
        similarity = difflib.SequenceMatcher(None, crossref_title.lower(), str(card_title).lower()).ratio()
        entry.update(
            {
                "doi": message.get("DOI"),
                "reference_agu": reference,
                "in_text": in_text,
                "year": year,
                "crossref_title": crossref_title,
                "title_similarity_to_card": round(similarity, 2),
                "reference_verified": True,
                "reference_source": "crossref",
            }
        )
        report.append((key, f"ok ({similarity:.2f}) {crossref_title[:70]}"))
        time.sleep(1.0)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    for key, status in report:
        print(f"{key}: {status}")


if __name__ == "__main__":
    main()
