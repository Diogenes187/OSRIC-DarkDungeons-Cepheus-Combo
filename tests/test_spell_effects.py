"""Tests for engine-resolved spell effects (damage, healing, saves)."""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine.data import spell_effects as fx
from state.repo import Repo
from referee.tools import RefereeTools


def test_lookup_and_aliases():
    assert fx.lookup("fireball")["name"] == "Fireball"
    assert fx.lookup("Fire Ball")["name"] == "Fireball"
    assert fx.lookup("cure light")["name"] == "Cure Light Wounds"
    assert fx.lookup("knock") is None             # no hard numbers


def test_roll_amount_scaling():
    # Magic Missile: (level+1)//2 darts of 1d4+1.
    r5 = fx.roll_amount(Dice(seed=1), fx.lookup("Magic Missile"), 5)
    assert "3 missiles" in r5["detail"]
    # Fireball: one 1d6 per level.
    r6 = fx.roll_amount(Dice(seed=1), fx.lookup("Fireball"), 6)
    assert 6 <= r6["amount"] <= 36
    # Burning Hands: 1 point per level, flat.
    assert fx.roll_amount(Dice(seed=1), fx.lookup("Burning Hands"), 4)["amount"] == 4
    # Shocking Grasp: 1d8 + 1/level.
    sg = fx.roll_amount(Dice(seed=1), fx.lookup("Shocking Grasp"), 5)
    assert 6 <= sg["amount"] <= 13                 # 1-8 + 5


def test_sleep_affected_bands():
    out = fx.sleep_affected(Dice(seed=2))
    assert out["above 4+4 HD"] == 0
    assert out["1 HD or less"] >= 1                # 4d4


def _mage(repo, cid, name="Mage", level=6):
    return repo.save_character(cid, {
        "name": name, "race": "Human",
        "classes": [{"class": "Magic-User", "level": level}], "alignment": "N",
        "str": 9, "dex": 14, "con": 12, "int": 16, "wis": 10, "cha": 10,
        "hp_max": 18, "hp_current": 18, "ac_descending": 10,
        "memorized": ["Magic Missile", "Fireball", "Fireball", "Fly"]})


def _target(repo, cid, name, hp=40):
    return repo.save_character(cid, {
        "name": name, "race": "Human", "classes": [{"class": "Fighter", "level": 1}],
        "alignment": "N", "str": 12, "dex": 10, "con": 12, "int": 9, "wis": 9,
        "cha": 9, "hp_max": hp, "hp_current": hp, "ac_descending": 7, "is_npc": True}, is_npc=True)


def test_cast_magic_missile_auto_damage():
    repo = Repo.memory()
    cid = repo.create_campaign("MM Test")
    _mage(repo, cid, "Mage")
    _target(repo, cid, "Orc", hp=40)
    t = RefereeTools(repo, cid, dice=Dice(seed=3))
    res = t.cast_spell(name="Mage", spell="Magic Missile", targets=["Orc"])
    assert res["effect"] == "damage" and res["save"] == "none"
    hit = res["targets"][0]
    assert hit["saved"] is None and hit["damage"] >= 2   # 3 missiles min 2 each? >=2
    orc = [c for c in repo.list_characters(cid) if c["name"] == "Orc"][0]
    assert orc["hp_current"] == 40 - hit["damage"]


def test_cast_fireball_save_for_half():
    repo = Repo.memory()
    cid = repo.create_campaign("FB Test")
    _mage(repo, cid, "Mage", level=6)
    _target(repo, cid, "A", hp=60)
    _target(repo, cid, "B", hp=60)
    t = RefereeTools(repo, cid, dice=Dice(seed=4))
    # Force A to fail (full) and resolve B normally; use save_mod extremes per cast.
    full = t.cast_spell(name="Mage", spell="Fireball", targets=["A"], save_mod=-50)
    a = full["targets"][0]
    assert a["saved"] is False and a["damage"] == full["rolled"]
    half = t.cast_spell(name="Mage", spell="Fireball", targets=["B"], save_mod=50)
    b = half["targets"][0]
    assert b["saved"] is True and b["damage"] == half["rolled"] // 2


def test_cast_cure_light_wounds_heals_to_cap():
    repo = Repo.memory()
    cid = repo.create_campaign("Heal Test")
    repo.save_character(cid, {
        "name": "Priest", "race": "Human", "classes": [{"class": "Cleric", "level": 3}],
        "alignment": "LG", "str": 12, "dex": 10, "con": 12, "int": 10, "wis": 16,
        "cha": 10, "hp_max": 22, "hp_current": 22, "ac_descending": 4,
        "memorized": ["Cure Light Wounds", "Cure Light Wounds"]})
    repo.save_character(cid, {
        "name": "Hurt", "race": "Human", "classes": [{"class": "Fighter", "level": 2}],
        "alignment": "N", "str": 15, "dex": 12, "con": 12, "int": 9, "wis": 9,
        "cha": 9, "hp_max": 16, "hp_current": 2, "ac_descending": 4})
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    res = t.cast_spell(name="Priest", spell="Cure Light Wounds", targets=["Hurt"])
    assert res["effect"] == "heal" and res["target"] == "Hurt"
    assert 3 <= res["target_hp"] <= 16                 # healed, capped at max
    # Heal never exceeds max.
    res2 = t.cast_spell(name="Priest", spell="Cure Light Wounds", targets=["Hurt"])
    assert res2["target_hp"] <= 16


def test_cast_sleep_and_unknown_spell():
    repo = Repo.memory()
    cid = repo.create_campaign("Misc Test")
    repo.save_character(cid, {
        "name": "Mage", "race": "Human",
        "classes": [{"class": "Magic-User", "level": 5}], "alignment": "N",
        "str": 9, "dex": 14, "con": 12, "int": 16, "wis": 10, "cha": 10,
        "hp_max": 12, "hp_current": 12, "ac_descending": 10,
        "memorized": ["Sleep", "Fly"]})
    t = RefereeTools(repo, cid, dice=Dice(seed=2))
    slp = t.cast_spell(name="Mage", spell="Sleep")
    assert slp["effect"] == "sleep" and "1 HD or less" in slp["affected_by_hd"]
    fly = t.cast_spell(name="Mage", spell="Fly")
    assert fly["resolved_by"] == "narration"           # no numbers invented


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All spell-effects tests passed.")
