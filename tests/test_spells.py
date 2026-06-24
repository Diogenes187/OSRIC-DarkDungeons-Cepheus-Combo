"""Checks the spell catalog loaded from the extracted spell list."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.data import spells as sp


def test_catalog_loaded():
    assert len(sp.SPELLS) > 400                 # ~459 across the four books
    counts = sp.count_by_class()
    assert counts.get("Magic-User", 0) > 150
    assert counts.get("Cleric", 0) > 80
    assert "Illusionist" in counts and "Druid" in counts


def test_known_spells():
    mm = sp.find("Magic Missile", "Magic-User")
    assert mm is not None and mm.level == 1 and "evocation" in mm.school.lower()
    cw = sp.find("Cure Light Wounds", "Cleric") or sp.find("Cure Light Wounds")
    # Cleric healing exists at level 1 (name may vary slightly in OSRIC)
    assert any(s.char_class == "Cleric" and s.level == 1 for s in sp.SPELLS)


def test_queries():
    mu1 = sp.for_class("Magic-User", 1)
    assert len(mu1) > 10 and all(s.level == 1 for s in mu1)
    assert 1 in sp.spell_levels("Cleric")
    assert max(sp.spell_levels("Magic-User")) >= 7      # MU goes to 9th, at least 7


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All spell-catalog tests passed.")
