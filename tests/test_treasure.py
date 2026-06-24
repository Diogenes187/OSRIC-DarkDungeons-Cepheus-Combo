"""Tests for OSRIC loot-class treasure generation."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine.data import treasure as tr


def test_all_classes_roll_without_error():
    d = Dice(seed=1)
    for name in tr.LOOT_CLASSES:
        t = tr.generate(d, name)
        assert t.total_gp >= 0


def test_individual_is_flat():
    # Individual classes always give coins (no percentage gate).
    d = Dice(seed=2)
    t = tr.generate(d, "Individual 4")          # 2d4 gp each
    assert "gp" in t.coins and 2 <= t.coins["gp"] <= 8


def test_hoard_has_structure():
    # A big hoard usually yields a mix; total value should be substantial often.
    d = Dice(seed=3)
    # Roll a few Hoard 8s and confirm coins/gems/jewellery appear and value adds up.
    saw_value = False
    for _ in range(20):
        t = tr.generate(d, "Hoard 8")
        if t.total_gp > 0:
            saw_value = True
        # gem entries carry a value; jewellery carries an item + value
        for g in t.gems:
            assert g["value"] > 0
        for j in t.jewellery:
            assert j["value"] > 0 and j["item"]
    assert saw_value


def test_magic_results_report_counts():
    d = Dice(seed=4)
    # Hoard 1 magic line is 3 items; with a forced-low d100 it should appear.
    saw_magic = False
    for _ in range(40):
        t = tr.generate(d, "Hoard 1")
        for m in t.magic:
            assert m["count"] >= 1 and m["detail"]
            saw_magic = True
    assert saw_magic


def test_parse_loot_field():
    assert tr.loot_classes_in("Hoard 3, Cache 4") == ["Hoard 3", "Cache 4"]
    assert tr.loot_classes_in("Individual 4 and Cache 3 each") == \
        ["Individual 4", "Cache 3"]
    assert tr.loot_classes_in("Nil") == []


def test_determinism():
    a = tr.generate(Dice(seed=99), "Hoard 5", "Cache 7")
    b = tr.generate(Dice(seed=99), "Hoard 5", "Cache 7")
    assert a.coins == b.coins and a.total_gp == b.total_gp


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All treasure tests passed.")
