"""Tests the authoritative OSRIC-text oracle (and the lore facade)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import osric_text
from engine import rules_lookup


def test_osric_text_available():
    assert osric_text.available(), "OSRIC text not found -- run scripts/extract_osric.py"


def test_rules_search_finds_known_passages():
    for q in ("exceptional strength", "turn undead", "saving throw"):
        hits = osric_text.search(q, limit=4)
        assert hits, "no OSRIC hit for {!r}".format(q)
        assert hits[0].source.startswith("OSRIC")     # labelled + authoritative
        assert hits[0].snippet
        # results are ranked by relevance
        assert hits[0].score >= hits[-1].score


def test_facade():
    rr = rules_lookup.rules("exceptional strength")
    assert rr and rr[0]["source"].startswith("OSRIC")
    st = rules_lookup.status()
    assert st["rules_available"] is True
    # lore availability depends on the corpus being present; just check the key.
    assert "lore_available" in st


if __name__ == "__main__":
    test_osric_text_available()
    test_rules_search_finds_known_passages()
    test_facade()
    print("All rules-lookup tests passed.")
