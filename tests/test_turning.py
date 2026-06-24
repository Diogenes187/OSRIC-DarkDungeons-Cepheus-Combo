"""Tests for Turn Undead: table lookup, outcomes, paladins, and the tool."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import turning
from engine.data import undead
from state.repo import Repo
from referee.tools import RefereeTools


def test_table_lookup_and_columns():
    assert undead.level_column(1) == 0
    assert undead.level_column(8) == 7
    assert undead.level_column(9) == 8 and undead.level_column(13) == 8
    assert undead.level_column(14) == 9 and undead.level_column(19) == 10
    assert undead.cell(1, 1) == "10"          # cleric 1 vs skeleton
    assert undead.cell(1, 5) == "T"           # cleric 5 vs skeleton: auto-turn
    assert undead.cell(1, 6) == "D"           # cleric 6 vs skeleton: destroy
    assert undead.cell(7, 1) == "-"           # cleric 1 vs wraith: no chance


def test_resolve_type_by_name_and_number():
    assert undead.resolve_type("skeleton") == 1
    assert undead.resolve_type("Vampire") == 10
    assert undead.resolve_type("Type 7") == 7
    assert undead.resolve_type(3) == 3
    assert undead.resolve_type("banana") is None


def test_no_chance_returns_no_effect():
    r = turning.turn_undead(Dice(seed=1), 1, "wraith", alignment="LG")
    assert r["code"] == "-" and r["outcome"] == "no_effect" and r["affected"] == 0


def test_auto_turn_and_destroy():
    # Cleric 5 vs skeleton: col 4 == "T" -> auto turned.
    t = turning.turn_undead(Dice(seed=2), 5, "skeleton", alignment="N")
    assert t["code"] == "T" and t["success"] and t["outcome"] == "turned"
    assert t["affected"] >= 2 and t["flee_rounds"] is not None
    # Cleric 8 vs skeleton: col 7 == "D*" -> destroyed (good/neutral), 1d6+6.
    d = turning.turn_undead(Dice(seed=2), 8, "skeleton", alignment="LG")
    assert d["code"] == "D*" and d["outcome"] == "destroyed"
    assert 7 <= d["affected"] <= 12


def test_numbered_result_rolls_d20():
    r = turning.turn_undead(Dice(seed=4), 3, "skeleton", alignment="N")
    assert r["code"] == "4" and r["needed"] == 4 and r["roll"] is not None
    assert isinstance(r["success"], bool)


def test_number_present_caps_affected():
    r = turning.turn_undead(Dice(seed=2), 5, "skeleton", alignment="N",
                            number_present=3)
    assert r["affected"] <= 3


def test_evil_cleric_controls_or_cows():
    r = turning.turn_undead(Dice(seed=6), 8, "skeleton", alignment="NE")
    assert r["outcome"] in ("controlled", "cowed")
    assert r["control_roll"] is not None
    assert r["controlled"] == (r["control_roll"] >= 61)


def test_paladin_turns_as_cleric_two_levels_lower():
    assert turning.turning_level("Paladin", 3) == 1
    assert turning.turning_level("Paladin", 2) == 0
    assert turning.turning_level("Cleric", 5) == 5


def test_determinism():
    a = turning.turn_undead(Dice(seed=11), 3, "ghoul", alignment="N")
    b = turning.turn_undead(Dice(seed=11), 3, "ghoul", alignment="N")
    assert a == b


def test_tool_flow_and_chronicle():
    repo = Repo.memory()
    cid = repo.create_campaign("Turn Test")
    repo.save_character(cid, {
        "name": "Brother Cael", "race": "Human",
        "classes": [{"class": "Cleric", "level": 5}], "alignment": "LG",
        "str": 12, "dex": 10, "con": 12, "int": 10, "wis": 16, "cha": 12,
        "hp_max": 24, "hp_current": 24, "ac_descending": 3})
    t = RefereeTools(repo, cid, dice=Dice(seed=2))
    res = t.turn_undead(name="Brother Cael", undead="skeleton")
    assert res["outcome"] == "turned" and res["affected"] >= 2
    assert any(e["kind"] == "turning" for e in repo.recent_events(cid))
    # A fighter can't turn.
    repo.save_character(cid, {
        "name": "Grit", "race": "Human", "classes": [{"class": "Fighter", "level": 4}],
        "alignment": "N", "str": 16, "dex": 12, "con": 14, "int": 9, "wis": 9,
        "cha": 9, "hp_max": 30, "hp_current": 30, "ac_descending": 2})
    bad = t.turn_undead(name="Grit", undead="skeleton")
    assert "error" in bad


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All turning tests passed.")
