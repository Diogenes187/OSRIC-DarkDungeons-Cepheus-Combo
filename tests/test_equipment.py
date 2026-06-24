"""Tests for the equipment catalog and encumbrance."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.data import equipment as eq
from engine import encumbrance as enc
from state.repo import Repo
from referee.tools import RefereeTools


def test_catalog_values_match_source():
    s = eq.WEAPONS["Sword, long"]
    assert s["damage_sm"] == "1d8" and s["weight"] == 7
    assert eq.cost_string(s["cost_cp"]) == "15 gp"
    p = eq.ARMOUR["Plate mail"]
    assert p["ac_desc"] == 3 and p["ac_asc"] == 17 and p["move_cap"] == 60
    assert eq.cost_string(p["cost_cp"]) == "400 gp"
    assert eq.WEAPONS["Dagger"]["cost_cp"] == 200            # 2 gp
    assert eq.cost_string(eq.GEAR["Torch"]["cost_cp"]) == "1 cp"


def test_lookup_is_case_insensitive_and_tagged():
    assert eq.lookup("plate mail")["category"] == "armour"
    assert eq.lookup("SWORD, LONG")["name"] == "Sword, long"
    assert eq.lookup("nonsense") is None


def test_strength_allowance():
    assert eq.carry_allowance(9) == 35
    assert eq.carry_allowance(16) == 70
    assert eq.carry_allowance(18, 0) == 110
    assert eq.carry_allowance(18, 50) == 135
    assert eq.carry_allowance(18, 75) == 160
    assert eq.carry_allowance(18, 99) == 235
    assert eq.carry_allowance(19) == 300


def test_encumbrance_steps():
    assert eq.encumbrance_step(50, 70)[0] == 1.0          # under allowance
    assert eq.encumbrance_step(100, 70)[0] == 0.75        # 30 over
    assert eq.encumbrance_step(140, 70)[0] == 0.5         # 70 over
    assert eq.encumbrance_step(180, 70)[0] == 0.25        # 110 over
    assert eq.encumbrance_step(300, 70)[0] == 0.0         # 230 over -> stuck


def test_adjusted_move_and_armour_cap():
    # Unencumbered, no armour: full base.
    assert eq.adjusted_move(120, 50, 70) == 120
    # Lightly encumbered: 3/4 of 120 = 90.
    assert eq.adjusted_move(120, 100, 70) == 90
    # Plate cap (60) overrides a higher weight-based move.
    assert eq.adjusted_move(120, 50, 70, armour_cap=60) == 60


def test_coin_and_gear_weight():
    assert enc.coin_weight(100) == 10.0                  # ten coins to the pound
    gear = ["Sword, long", {"item": "Plate mail", "qty": 1}]
    assert enc.gear_weight(gear) == 52.0                 # 7 + 45
    # An unknown free-text item weighs nothing.
    assert enc.gear_weight(["a lock of hair"]) == 0.0


def test_assess_full_readout():
    gear = [{"item": "Plate mail", "qty": 1}, "Sword, long"]
    r = enc.assess(gear, gold=200, str_score=16, str_pct=0, race="Human")
    assert r["total_weight"] == 45 + 7 + 20              # +coins
    assert r["allowance"] == 70
    assert r["armour"] == "Plate mail" and r["armour_cap"] == 60
    assert r["movement_rate"] == 60                      # capped by plate


def test_tool_add_equipment_and_encumbrance():
    repo = Repo.memory()
    cid = repo.create_campaign("Gear Test")
    repo.save_character(cid, {
        "name": "Garrad", "race": "Human",
        "classes": [{"class": "Fighter", "level": 2}], "alignment": "N",
        "str": 16, "dex": 12, "con": 14, "int": 9, "wis": 9, "cha": 9,
        "hp_max": 16, "hp_current": 16, "ac_descending": 10, "gold": 500})
    t = RefereeTools(repo, cid)
    buy = t.add_equipment(name="Garrad", item="plate mail", pay=True)
    assert buy["charged_gp"] == 400 and buy["gold"] == 100
    t.add_equipment(name="Garrad", item="Sword, long")
    enc_out = t.encumbrance(name="Garrad")
    # 45 (plate) + 7 (sword) + 10 (100 gp) = 62; allowance 70 -> unencumbered,
    # but plate caps movement at 60.
    assert enc_out["total_weight"] == 62
    assert enc_out["encumbrance"] == "Unencumbered"
    assert enc_out["movement_rate"] == 60


def test_tool_pay_rejects_when_broke():
    repo = Repo.memory()
    cid = repo.create_campaign("Broke Test")
    repo.save_character(cid, {
        "name": "Pauper", "race": "Human", "classes": [{"class": "Thief", "level": 1}],
        "alignment": "N", "str": 10, "dex": 14, "con": 10, "int": 10, "wis": 10,
        "cha": 10, "hp_max": 6, "hp_current": 6, "ac_descending": 8, "gold": 5})
    t = RefereeTools(repo, cid)
    res = t.add_equipment(name="Pauper", item="plate mail", pay=True)
    assert "error" in res and res["needed_gp"] == 400


def test_list_equipment_categories():
    repo = Repo.memory()
    cid = repo.create_campaign("List Test")
    t = RefereeTools(repo, cid)
    allcat = t.list_equipment()
    assert "weapons" in allcat and "armour" in allcat
    just_armour = t.list_equipment(category="armour")
    assert all("ac" in i for i in just_armour["items"])


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All equipment tests passed.")
