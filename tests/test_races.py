"""Spot-checks of the OSRIC ancestry tables against the Player Guide (Ch. 2)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.data import races as R


def test_adjustments():
    assert R.get("Dwarf").adjustments == {"con": 1, "cha": -1}
    assert R.get("Elf").adjustments == {"dex": 1, "con": -1}
    assert R.get("Halfling").adjustments == {"dex": 1, "str": -1}
    assert R.get("Half-Orc").adjustments == {"str": 1, "con": 1, "cha": -2}
    assert R.get("Gnome").adjustments == {}
    assert R.get("Human").adjustments == {}


def test_requirements():
    # Table 1.2.0A
    assert R.get("Dwarf").requirements["con"] == (12, 19)
    assert R.get("Dwarf").requirements["cha"] == (3, 16)
    assert R.get("Half-Orc").requirements["cha"] == (3, 12)
    assert R.get("Elf").requirements["dex"] == (7, 19)
    assert R.get("Human").requirements["str"] == (3, 18)


def test_allowed_classes():
    assert set(R.eligible_classes("Halfling")) == {"Fighter", "Druid", "Thief"}
    assert "Paladin" in R.eligible_classes("Human")
    assert "Paladin" not in R.eligible_classes("Dwarf")
    assert "Magic-User" in R.eligible_classes("Elf")
    assert "Illusionist" in R.eligible_classes("Gnome")


def test_level_limits():
    # Dwarf fighter scales with Strength
    assert R.max_level("Dwarf", "Fighter", {"str": 18}) == 9
    assert R.max_level("Dwarf", "Fighter", {"str": 17}) == 8
    assert R.max_level("Dwarf", "Fighter", {"str": 14}) == 7
    assert R.max_level("Dwarf", "Thief", {"str": 18}) is None      # unlimited
    # Elf magic-user scales with Intelligence
    assert R.max_level("Elf", "Magic-User", {"int": 18}) == 11
    assert R.max_level("Elf", "Magic-User", {"int": 16}) == 9
    # Humans: unlimited except Assassin/Druid/Monk
    assert R.max_level("Human", "Fighter", {}) is None
    assert R.max_level("Human", "Monk", {}) == 17
    # Half-orc thief scales with Dexterity
    assert R.max_level("Half-Orc", "Thief", {"dex": 17}) == 7
    assert R.max_level("Half-Orc", "Thief", {"dex": 12}) == 6


def test_multiclass():
    assert ("Fighter", "Magic-User", "Thief") in R.get("Elf").multiclass
    assert R.get("Human").multiclass == ()           # humans dual-class instead
    assert R.get("Human").can_dual_class is True


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All ancestry-table tests passed.")
