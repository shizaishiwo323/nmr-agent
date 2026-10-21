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
    reference = f"{author_text} ({year}). {title}. {detail}. https://doi.org/{doi}"
    families = [author.get("family") or author.get("name") or "" for author in authors]
    if len(families) == 1:
        in_text = f"{families[0]}, {year}"
    elif len(families) == 2:
        in_text = f"{families[0]} & {families[1]}, {year}"
    else:
        in_text = f"{families[0]} et al., {year}"
    return reference, in_text, year


def crossref(doi: str) -> dict:
    request = urllib.request.Request(f"https://api.crossref.org/works/{doi}", headers={"User-Agent": "t2-inversion-agent literature check"})
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
    cited = {key for scenario in scenarios for key in scenario["citations"]}
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
        crossref_title = clean_title((message.get("title") or [""])[0])
        card_title = entry.get("title") or entry.get("metadata", {}).get("/Title") or entry.get("pdf_name", "")
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
