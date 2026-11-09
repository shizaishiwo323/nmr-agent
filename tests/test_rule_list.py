"""Keep docs/interpretation_rules.md in step with the rules in t2_agent/literature.py."""

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "docs" / "nmr_t2_literature_knowledge"


def _code_rules_and_keys() -> tuple[set[str], set[str]]:
    source = (ROOT / "t2_agent" / "literature.py").read_text(encoding="utf-8")
    rules = set(re.findall(r'Finding\(\s*"([a-z0-9_]+)"', source))
    keys = set(re.findall(r'"([A-Z][A-Za-z]+\d{4}[A-Za-z0-9]*)"', source))
    return rules, keys


def test_rule_list_matches_code():
    rules, _keys = _code_rules_and_keys()
    doc = (ROOT / "docs" / "interpretation_rules.md").read_text(encoding="utf-8")
    listed = set(re.findall(r"^\| \d+ \| `([a-z0-9_]+)`", doc, re.M))
    assert listed == rules
    assert f"applies the {len(rules)} rules" in doc


def test_cited_references_are_verified_and_listed():
    _rules, keys = _code_rules_and_keys()
    manifest = {e["citation_key"]: e for e in json.loads((KB / "literature_manifest.enriched.json").read_text(encoding="utf-8"))}
    doc = (ROOT / "docs" / "interpretation_rules.md").read_text(encoding="utf-8")
    assert f"## References cited by the rules ({len(keys)})" in doc
    for key in keys:
        entry = manifest[key]
        assert entry.get("reference_verified") and entry.get("reference_agu")
        assert entry["reference_agu"] in doc


def test_every_library_entry_has_a_note():
    manifest = json.loads((KB / "literature_manifest.enriched.json").read_text(encoding="utf-8"))
    notes = {path.stem for path in (KB / "papers").glob("*.md")}
    assert {entry["citation_key"] for entry in manifest} == notes
