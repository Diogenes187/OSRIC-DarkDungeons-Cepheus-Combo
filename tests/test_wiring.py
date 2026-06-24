"""Tests for Phase 7 wiring: encumbrance-driven travel and ready-made encounters."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from state.repo import Repo
from referee.tools import RefereeTools


def _traveller(repo, cid, name, race="Human", str_score=12, gold=0):
    return repo.save_character(cid, {
        "name": name, "race": race, "classes": [{"class": "Fighter", "level": 2}],
        "alignment": "N", "str": str_score, "dex": 12, "con": 12, "int": 9,
        "wis": 9, "cha": 12, "hp_max": 18, "hp_current": 18, "gold": gold,
        "ac_descending": 4})


def test_journey_uses_party_slowest_move():
    repo = Repo.memory()
    cid = repo.create_campaign("Travel Test", current_date="Reaping 1, 576 CY")
    # A nimble human and a slow, heavily-laden dwarf.
    _traveller(repo, cid, "Scout", race="Human", str_score=12, gold=0)
    _traveller(repo, cid, "Tank", race="Dwarf", str_score=12, gold=0)
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    # Load the dwarf past their Strength allowance with heavy plate + coin.
    t.add_equipment(name="Tank", item="Plate mail")
    t.set_gold(name="Tank", amount=500)          # 50 lbs of coin
    res = t.journey(terrain="plains", days=2, party=["Scout", "Tank"])
    assert res["movement_from"] == "party encumbrance"
    # The party can't move faster than the encumbered dwarf (slower than the
    # unburdened human scout's 120).
    assert res["movement_rate"] < 120 and res["movement_rate"] <= 90
    # Without a party, the manual base_move is used.
    res2 = t.journey(terrain="plains", days=1, base_move=120)
    assert res2["movement_from"] == "base_move" and res2["movement_rate"] == 120


def test_random_encounter_brings_surprise_and_reaction():
    repo = Repo.memory()
    cid = repo.create_campaign("Enc Test")
    repo.save_character(cid, {
        "name": "Aria", "race": "Human", "classes": [{"class": "Fighter", "level": 3}],
        "alignment": "CG", "str": 14, "dex": 17, "con": 12, "int": 12, "wis": 12,
        "cha": 16, "hp_max": 24, "hp_current": 24, "ac_descending": 4})
    t = RefereeTools(repo, cid, dice=Dice(seed=2))
    res = t.random_encounter(terrain="forest", party=["Aria"])
    assert "surprise" in res and "reaction" in res
    assert "party_surprised_segments" in res["surprise"]
    # Aria's Charisma 16 (+25 reaction) shifts the monster's reaction roll.
    assert res["reaction"]["modifier"] == 25
    assert res["reaction"]["reaction"] in (
        "Very hostile", "Hostile", "Unfavorable", "Neutral", "Favorable",
        "Friendly", "Very friendly")


def test_random_encounter_without_party_still_works():
    repo = Repo.memory()
    cid = repo.create_campaign("Enc2 Test")
    t = RefereeTools(repo, cid, dice=Dice(seed=5))
    res = t.random_encounter(terrain="hills")
    assert res["reaction"]["modifier"] == 0       # no negotiator -> neutral
    assert "surprise" in res


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All wiring tests passed.")
