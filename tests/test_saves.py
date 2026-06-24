"""Spot-checks of the OSRIC saving-throw tables + the combat saving_throw roll."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine.data import saves as sv
from engine import combat


def test_save_targets():
    # Cleric (priest) 1-3: aimed 14, breath 16, death 10, petrify 13, spells 15
    assert sv.save_target("Cleric", 1, "death") == 10
    assert sv.save_target("Cleric", 1, "spells") == 15
    assert sv.save_target("Druid", 2, "death") == 10        # Druid shares priest
    # Magic-User (arcane) 1-5: spells 12 (mages save well vs spells)
    assert sv.save_target("Magic-User", 1, "spells") == 12
    assert sv.save_target("Illusionist", 3, "spells") == 12
    # Fighter (fighter) 1-2: death 14 ; Ranger shares it
    assert sv.save_target("Fighter", 1, "death") == 14
    assert sv.save_target("Ranger", 2, "death") == 14
    # Paladin saves a touch better than fighters (1-2 death 12)
    assert sv.save_target("Paladin", 1, "death") == 12
    # Rogue group (Thief/Assassin/Monk identical) 1-4: death 13
    assert sv.save_target("Thief", 1, "death") == 13
    assert sv.save_target("Assassin", 4, "death") == 13
    assert sv.save_target("Monk", 2, "death") == 13


def test_higher_brackets():
    # priest improves with level
    assert sv.save_target("Cleric", 13, "death") == 5
    # arcane top bracket carries forward past the table
    assert sv.save_target("Magic-User", 99, "spells") == 6


def test_saving_throw_roll():
    d = Dice(seed=5)
    # A Magic-User vs spells (target 12). With a +100 modifier it always saves;
    # with -100 it never does.
    assert all(combat.saving_throw(d, "Magic-User", 1, "spells", 100)["success"]
               for _ in range(50))
    assert not any(combat.saving_throw(d, "Magic-User", 1, "spells", -100)["success"]
                   for _ in range(50))
    # Determinism + meets-or-beats semantics.
    r = combat.saving_throw(Dice(seed=1), "Fighter", 1, "death")
    r2 = combat.saving_throw(Dice(seed=1), "Fighter", 1, "death")
    assert r == r2
    assert r["success"] == (r["total"] >= r["target"])


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All saving-throw tests passed.")
