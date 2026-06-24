"""Tests for thief skills: base values, adjustments, checks, and the tool."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import thief_skills as ts
from engine.data import thieving
from state.repo import Repo
from referee.tools import RefereeTools


def test_base_values_match_source():
    assert thieving.base_chance("climb", 1) == 85
    assert thieving.base_chance("pick_pockets", 1) == 30
    assert thieving.base_chance("read_languages", 1) == 1
    assert thieving.base_chance("move_quietly", 7) == 55
    assert thieving.base_chance("pick_locks", 12) == 77


def test_alias_resolution():
    assert thieving.canon_skill("Open Locks") == "pick_locks"
    assert thieving.canon_skill("move silently") == "move_quietly"
    assert thieving.canon_skill("hear noise") == "listen"
    assert thieving.canon_skill("find/remove traps") == "traps"


def test_dex_and_ancestry_adjustments():
    # A halfling thief with Dex 17: hide base 10 +ancestry15 +dex5 = 30.
    c = ts.chance("hide", 1, dex=17, race="Halfling")
    assert c == 10 + 15 + 5
    # Dwarf climbs worse: 85 base -10 ancestry, no dex effect on climb.
    assert ts.chance("climb", 1, dex=18, race="Dwarf") == 85 - 10
    # Low Dex penalises move silently.
    assert ts.chance("move_quietly", 1, dex=9, race="Human") == 15 - 20


def test_check_clamps_and_rolls():
    res = ts.check(Dice(seed=1), "open locks", level=12, dex=19, race="Elf")
    # 77 base +20 dex +(-5 elf) = 92 -> needs a roll <= 92.
    assert res["skill"] == "pick_locks" and res["chance"] == 92
    assert res["effective_chance"] == 92
    assert isinstance(res["success"], bool)
    # Chances over 100 clamp to a 99/100 effective.
    big = ts.check(Dice(seed=1), "pick_locks", level=20, dex=19, race="Human")
    assert big["chance"] >= 100 and big["effective_chance"] == 100


def test_determinism():
    a = ts.check(Dice(seed=7), "hide", 5, 16, "Elf")
    b = ts.check(Dice(seed=7), "hide", 5, 16, "Elf")
    assert a == b


def test_thief_level_picks_thief_over_other():
    classes = [{"class": "Fighter", "level": 8}, {"class": "Thief", "level": 5}]
    assert ts.thief_level(classes) == 5
    assert ts.thief_level([{"class": "Magic-User", "level": 4}]) is None


def test_tool_flow():
    repo = Repo.memory()
    cid = repo.create_campaign("Thief Test")
    repo.save_character(cid, {
        "name": "Sly", "race": "Halfling",
        "classes": [{"class": "Thief", "level": 6}],
        "str": 9, "dex": 17, "con": 12, "int": 10, "wis": 9, "cha": 12,
        "hp_max": 18, "hp_current": 18, "ac_descending": 6})
    t = RefereeTools(repo, cid, dice=Dice(seed=3))
    res = t.thief_skill(name="Sly", skill="move silently")
    assert res["skill"] == "move_quietly"
    # base 47 (L6) + halfling 15 + dex17 5 = 67
    assert res["chance"] == 47 + 15 + 5
    # A non-thief is rejected.
    repo.save_character(cid, {
        "name": "Pug", "race": "Human", "classes": [{"class": "Fighter", "level": 3}],
        "str": 15, "dex": 12, "con": 12, "int": 9, "wis": 9, "cha": 9,
        "hp_max": 20, "hp_current": 20, "ac_descending": 4})
    bad = t.thief_skill(name="Pug", skill="hide")
    assert "error" in bad


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All thief-skill tests passed.")
