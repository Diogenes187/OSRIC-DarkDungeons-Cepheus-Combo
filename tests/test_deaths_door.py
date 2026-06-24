"""Tests for death's door: 0 = down & bleeding, -10 = dead."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from state.repo import Repo
from referee.tools import RefereeTools


def _pc(repo, cid, name="Hero", hp=8):
    return repo.save_character(cid, {
        "name": name, "race": "Human", "classes": [{"class": "Fighter", "level": 2}],
        "alignment": "N", "str": 15, "dex": 12, "con": 12, "int": 9, "wis": 9,
        "cha": 9, "hp_max": hp, "hp_current": hp, "ac_descending": 4})


def _by(repo, cid, name):
    return [c for c in repo.list_characters(cid) if c["name"] == name][0]


def test_pc_at_zero_is_dying_not_dead():
    repo = Repo.memory(); cid = repo.create_campaign("DD")
    _pc(repo, cid, "Hero")
    t = RefereeTools(repo, cid)
    st = t.set_hp(name="Hero", hp_current=0)
    assert st["status"] == "dying" and st["alive"] is True and st["hp"] == 0


def test_pc_dies_at_minus_ten():
    repo = Repo.memory(); cid = repo.create_campaign("DD")
    _pc(repo, cid, "Hero")
    t = RefereeTools(repo, cid)
    st = t.set_hp(name="Hero", hp_current=-10)
    assert st["status"] == "dead" and st["alive"] is False


def test_monster_dies_at_zero():
    repo = Repo.memory(); cid = repo.create_campaign("DD")
    repo.save_character(cid, {
        "name": "Goblin", "race": "Goblin", "classes": [{"class": "Fighter", "level": 1}],
        "alignment": "NE", "str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10,
        "cha": 10, "hp_max": 6, "hp_current": 6, "ac_descending": 6}, is_npc=True)
    t = RefereeTools(repo, cid)
    st = t.set_hp(name="Goblin", hp_current=0)
    assert st["status"] == "dead" and st["alive"] is False


def test_fresh_wound_while_down_is_instant_death():
    repo = Repo.memory(); cid = repo.create_campaign("DD")
    _pc(repo, cid, "Hero")
    t = RefereeTools(repo, cid)
    t.set_hp(name="Hero", hp_current=0)          # down, dying
    res = t._apply_damage(dict(_by(repo, cid, "Hero")), 4)   # struck while down
    assert res["status"] == "dead" and res["alive"] is False


def test_bleeding_each_round_until_death():
    repo = Repo.memory(); cid = repo.create_campaign("DD")
    _pc(repo, cid, "Hero")
    _pc(repo, cid, "Foe")
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    t.set_hp(name="Hero", hp_current=-8)         # dying near the edge
    t.start_combat(combatants=[{"name": "Hero", "side": "party"},
                               {"name": "Foe", "side": "foes"}])
    t.advance_turn(name="Foe")                   # Hero is down, doesn't act
    r2 = t.next_round()
    assert r2["round"] == 2
    assert any(b["name"] == "Hero" and b["hp"] == -9 for b in r2["bleeding"])
    t.advance_turn(name="Foe")
    r3 = t.next_round()
    assert any(b["name"] == "Hero" and b["dead"] for b in r3["bleeding"])
    assert _by(repo, cid, "Hero")["status"] == "dead"


def test_stabilize_stops_the_bleeding():
    repo = Repo.memory(); cid = repo.create_campaign("DD")
    _pc(repo, cid, "Hero")
    _pc(repo, cid, "Foe")
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    t.set_hp(name="Hero", hp_current=-3)
    s = t.stabilize(name="Hero")
    assert s["status"] == "stable"
    t.start_combat(combatants=[{"name": "Hero", "side": "party"},
                               {"name": "Foe", "side": "foes"}])
    t.advance_turn(name="Foe")
    r2 = t.next_round()
    assert "bleeding" not in r2                   # stable -> no blood loss
    assert _by(repo, cid, "Hero")["hp_current"] == -3


def test_heal_revives_a_dying_character():
    repo = Repo.memory(); cid = repo.create_campaign("DD")
    _pc(repo, cid, "Hero", hp=16)
    repo.save_character(cid, {
        "name": "Priest", "race": "Human", "classes": [{"class": "Cleric", "level": 3}],
        "alignment": "LG", "str": 12, "dex": 10, "con": 12, "int": 10, "wis": 16,
        "cha": 10, "hp_max": 20, "hp_current": 20, "ac_descending": 4,
        "memorized": ["Cure Light Wounds"]})
    t = RefereeTools(repo, cid, dice=Dice(seed=2))
    t.set_hp(name="Hero", hp_current=0)          # down
    t.cast_spell(name="Priest", spell="Cure Light Wounds", targets=["Hero"])
    hero = _by(repo, cid, "Hero")
    assert hero["hp_current"] > 0 and hero["status"] == "ok" and hero["alive"] == 1


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All death's-door tests passed.")
