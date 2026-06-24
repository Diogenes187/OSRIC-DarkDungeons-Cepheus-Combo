"""Tests for spell slots and Vancian memorise/cast."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.data import spell_slots as ss
from engine import spellcasting as sc


def test_slot_tables():
    assert ss.slots("Magic-User", 1) == [1, 0, 0, 0, 0, 0, 0, 0, 0]
    assert ss.slots("Magic-User", 5)[:3] == [4, 2, 1]      # 4/2/1 at level 5
    assert ss.slots("Cleric", 1) == [1, 0, 0, 0, 0, 0, 0]
    assert ss.slots("Druid", 1)[0] == 2                    # druids get 2 at L1
    assert ss.slots("Illusionist", 5)[:3] == [4, 3, 1]
    assert ss.slots("Fighter", 1) == []                    # non-caster


def test_cleric_wisdom_bonus():
    # WIS 14 gives +2 first-level slots (base 1 -> 3).
    assert ss.slots("Cleric", 1, wis=14)[0] == 3
    assert ss.slots("Cleric", 1, wis=12)[0] == 1           # no bonus below 13
    # The 2nd-level WIS bonus only applies once the cleric can cast 2nd level.
    assert ss.slots("Cleric", 1, wis=16)[1] == 0           # can't cast 2nd yet
    assert ss.slots("Cleric", 3, wis=16)[1] == 1 + 2       # base 1 + WIS 15/16


def test_memorize_and_cast():
    mem = []
    # A level-1 Magic-User has one 1st-level slot.
    mem = sc.memorize("Magic-User", 1, mem, "Magic Missile")
    assert mem == ["Magic Missile"]
    assert not sc.can_memorize("Magic-User", 1, mem, "Sleep")   # slot full
    # Cast it -> slot frees.
    mem = sc.cast(mem, "magic missile")
    assert mem == []
    assert sc.can_memorize("Magic-User", 1, mem, "Sleep")


def test_invalid_memorize():
    try:
        sc.memorize("Magic-User", 1, [], "Cure Light Wounds")   # cleric spell
        assert False, "should have raised"
    except ValueError:
        pass


def test_remaining_slots():
    mem = sc.memorize("Cleric", 3, [], "Bless") if sc.catalog.find("Bless", "Cleric") else []
    rem = sc.remaining_slots("Cleric", 1, [], wis=14)
    assert rem[0] == 3        # three free 1st-level slots with WIS 14


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All spellcasting tests passed.")
