"""Tests for base multiple attacks and damage-vs-Large."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import specialization as spec
from engine.data import equipment as eq
from state.repo import Repo
from referee.tools import RefereeTools


def test_base_melee_rate_progression():
    assert spec.base_melee_rate("Fighter", 6) == "1/1"
    assert spec.base_melee_rate("Fighter", 7) == "3/2"
    assert spec.base_melee_rate("Fighter", 13) == "2/1"
    assert spec.base_melee_rate("Ranger", 7) == "1/1"     # ranger lags
    assert spec.base_melee_rate("Ranger", 8) == "3/2"
    assert spec.base_melee_rate("Ranger", 15) == "2/1"
    assert spec.base_melee_rate("Magic-User", 12) == "1/1"


def test_attacks_this_round_pattern():
    assert spec.attacks_this_round("1/1", 1) == 1
    assert spec.attacks_this_round("2/1", 2) == 2
    assert spec.attacks_this_round("3/2", 1) == 2          # 2 in odd rounds
    assert spec.attacks_this_round("3/2", 2) == 1          # 1 in even rounds
    assert spec.attacks_this_round("5/2", 1) == 3
    assert spec.attacks_this_round("5/2", 2) == 2


def test_best_base_rate_multiclass():
    assert spec.best_base_rate([{"class": "Fighter", "level": 7},
                                {"class": "Magic-User", "level": 9}]) == "3/2"


def _fighter(repo, cid, name, level):
    return repo.save_character(cid, {
        "name": name, "race": "Human",
        "classes": [{"class": "Fighter", "level": level}], "alignment": "N",
        "str": 16, "dex": 12, "con": 14, "int": 9, "wis": 9, "cha": 9,
        "hp_max": 60, "hp_current": 60, "ac_descending": 2})


def test_tool_reports_attack_rate_in_combat():
    repo = Repo.memory()
    cid = repo.create_campaign("Rate Test")
    _fighter(repo, cid, "Veteran", 8)
    _fighter(repo, cid, "Recruit", 1)
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    t.start_combat(combatants=[{"name": "Veteran", "side": "party"},
                               {"name": "Recruit", "side": "foes"}])
    res = t.attack(attacker="Veteran", defender="Recruit")
    assert res["attack_rate"] == "3/2"
    assert res["attacks_this_round"] == 2                  # round 1, odd
    res2 = t.attack(attacker="Recruit", defender="Veteran")
    assert res2["attack_rate"] == "1/1" and res2["attacks_this_round"] == 1


def test_tool_damage_vs_large_uses_lg_die():
    repo = Repo.memory()
    cid = repo.create_campaign("Large Test")
    _fighter(repo, cid, "Hero", 5)
    # Spawn a real Large monster (Ogre) so its size drives the damage column.
    t = RefereeTools(repo, cid, dice=Dice(seed=3))
    t.spawn_monster("Ogre", label="Ogre", count=1)
    t.start_combat(combatants=[{"name": "Hero", "side": "party"},
                               {"name": "Ogre", "side": "foes"}])
    # Two-handed sword: 1d10 vs M, 3d6 vs L+.
    res = t.attack(attacker="Hero", defender="Ogre", weapon="Sword, two-handed")
    assert res["vs_large"] is True
    # A Medium target uses the small die.
    res2 = t.attack(attacker="Hero", defender="Hero", weapon="Sword, two-handed")
    assert res2["vs_large"] is False


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All attack-rate tests passed.")
