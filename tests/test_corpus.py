"""Tests the rules-lookup oracle over the 1e corpus.

Skips gracefully if adnd_1e.db isn't found (so the rest of the suite still runs
on a machine without the corpus).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import corpus


def test_corpus_present():
    path = corpus.corpus_path()
    if not path:
        print("  (corpus not found -- skipping corpus search tests)")
        return
    assert os.path.exists(path)


def test_search_returns_hits():
    if not corpus.available():
        print("  (corpus not found -- skipping)")
        return
    hits = corpus.search("saving throw", limit=5)
    assert len(hits) >= 1
    for h in hits:
        assert h.snippet                      # a non-empty excerpt
    # A classic 1e term should surface from the books.
    fb = corpus.search("fireball", limit=3)
    assert len(fb) >= 1


if __name__ == "__main__":
    test_corpus_present()
    test_search_returns_hits()
    print("All corpus tests passed (or skipped if no corpus).")
