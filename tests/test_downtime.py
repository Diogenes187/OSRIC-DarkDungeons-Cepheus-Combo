"""Tests for the calendar, natural healing, rest, and training."""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import calendar as cal
from engine import downtime
from engine.data import advancement as adv
from state.repo import Repo
from referee.tools import RefereeTools


def test_calendar_parse_and_advance():
    assert cal.parse("Reaping 4, 576 CY") == (9, 4, 576)
    # 28-day month rolls into the next.
    assert cal.advance("Reaping 28, 576 CY", 1) == "Goodmonth 1, 576 CY"
    # Festivals are only 7 days.
    assert cal.advance("Needfest 7, 576 CY", 1) == "Fireseek 1, 576 CY"
    # A full year returns to the same date a year on.
    assert cal.advance("Fireseek 1, 576 CY", cal.YEAR_DAYS) == "Fireseek 1, 577 CY"


def test_natural_healing_rates():
    # 1 hp per day.
    assert downtime.natural_healing(3, 10, 30, 12)["healed"] == 3
    # Four weeks restores full regardless.
    assert downtime.natural_healing(28, 1, 40, 12)["hp"] == 40
    # Already full heals nothing.
    assert downtime.natural_healing(5, 20, 20, 12)["healed"] == 0
    # High Constitution adds its bonus from the second week.
    base = downtime.natural_healing(10, 0, 99, 7)["healed"]      # +0 con
    boon = downtime.natural_healing(10, 0, 99, 16)["healed"]     # +2 con
    assert boon > base


def test_training_cost():
    assert downtime.training_cost(1) == 1500       # to reach 2nd
    assert downtime.training_cost(4) == 6000       # to reach 5th


def _pc(repo, cid, name="Hero", level=1, hp=8, gold=5000, con=12):
    return repo.save_character(cid, {
        "name": name, "race": "Human",
        "classes": [{"class": "Fighter", "level": level,
                     "xp": adv.xp_for_level("Fighter", level)}],
        "alignment": "N", "str": 16, "dex": 12, "con": con, "int": 9, "wis": 9,
        "cha": 9, "hp_max": hp, "hp_current": hp, "gold": gold, "ac_descending": 4})


def test_tool_advance_time_and_rest():
    repo = Repo.memory()
    cid = repo.create_campaign("Time Test", current_date="Reaping 1, 576 CY")
    _pc(repo, cid, "Hero", hp=20)
    repo.save_character(cid, {  # set Hero wounded
        "name": "X", "race": "Human", "classes": [{"class": "Fighter", "level": 1}],
        "alignment": "N", "str": 10, "dex": 10, "con": 10, "int": 9, "wis": 9,
        "cha": 9, "hp_max": 10, "hp_current": 10, "ac_descending": 8})
    t = RefereeTools(repo, cid)
    t.set_hp(name="Hero", hp_current=12)
    res = t.rest(days=5, name="Hero")
    assert res["date"] == "Reaping 6, 576 CY"
    assert res["rested"][0]["healed"] == 5 and res["rested"][0]["hp"] == 17
    # advance_time moves the date without healing.
    adv_out = t.advance_time(days=28)
    assert adv_out["date"] == "Goodmonth 6, 576 CY"


def test_tool_training_gate_banks_then_levels():
    repo = Repo.memory()
    cid = repo.create_campaign("Train Test", current_date="Fireseek 1, 576 CY")
    _pc(repo, cid, "Cadet", level=1, hp=9, gold=5000)
    t = RefereeTools(repo, cid, dice=Dice(seed=2))
    t.set_training_required(on=True)
    # Enough XP for level 2, but it should NOT level up automatically.
    g = t.grant_xp(amount=adv.xp_for_level("Fighter", 2), name="Cadet")
    assert g["level_ups"] == [] and g["ready_to_train"]
    cadet = [c for c in repo.list_characters(cid) if c["name"] == "Cadet"][0]
    assert json.loads(cadet["classes_json"])[0]["level"] == 1     # still level 1
    # Now train: pays gold, advances time, gains the level + HP.
    tr = t.train(name="Cadet")
    assert tr["to"] == 2 and tr["cost_gp"] == 1500
    cadet = [c for c in repo.list_characters(cid) if c["name"] == "Cadet"][0]
    assert json.loads(cadet["classes_json"])[0]["level"] == 2
    assert cadet["gold"] == 5000 - 1500 and cadet["hp_max"] > 9


def test_training_off_still_auto_levels():
    repo = Repo.memory()
    cid = repo.create_campaign("Auto Test")
    _pc(repo, cid, "Auto", level=1, hp=9)
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    g = t.grant_xp(amount=adv.xp_for_level("Fighter", 2), name="Auto")
    assert any(lu["to"] == 2 for lu in g["level_ups"])            # auto-levels


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All downtime tests passed.")
