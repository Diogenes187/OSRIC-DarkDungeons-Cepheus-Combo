"""Tests for combat conditions: poison, disease, drain, item saves, grappling."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import conditions as cond
from engine.data import conditions as cdata
from engine.data import advancement as adv
from state.repo import Repo
from referee.tools import RefereeTools


def test_item_save_table_values():
    assert cdata.item_save_target("metal", "fire_normal") == 1
    assert cdata.item_save_target("paper", "fire") == 20          # magical fire
    assert cdata.item_save_target("wood", "lightning") == 10
    assert cdata.item_save_target("stone", "acid") == 3
    assert cdata.item_save_target("nonsense", "fire") == 0


def test_item_save_magic_bonus():
    # A +1 item gets +2 (magical) plus its plus = +3 total.
    r = cond.item_save(Dice(seed=1), "metal", "lightning", magic_bonus=1)
    assert r["bonus"] == 3 and r["target"] == 11
    plain = cond.item_save(Dice(seed=1), "metal", "lightning", magic_bonus=0)
    assert plain["bonus"] == 0


def test_unarmed_tohit_targets():
    assert cdata.unarmed_tohit_target(10) == 2
    assert cdata.unarmed_tohit_target(6) == 10
    assert cdata.unarmed_tohit_target(0) == 22
    assert cdata.unarmed_tohit_target(-3) == 22         # capped


def test_poison_save_fatal_and_wounding():
    dead = cond.poison_save(Dice(seed=3), save_target=21)     # impossible save
    assert dead["saved"] is False and dead["result"] == "dead"
    wound = cond.poison_save(Dice(seed=3), save_target=21, on_fail_damage="2d4")
    assert wound["result"] == "wounded" and wound["damage"] >= 2
    safe = cond.poison_save(Dice(seed=3), save_target=1)      # auto-save (d20>=1)
    assert safe["saved"] and safe["result"] == "survived"


def test_disease_check_structure():
    r = cond.disease_check(Dice(seed=2), save_target=21)      # forced contraction
    assert r["contracted"] and r["penalty"] < 0
    assert r["onset"] >= 2 and r["duration"] >= 2
    assert isinstance(r["fatal"], bool)


def test_level_drain_single_and_slain():
    cls = [{"class": "Fighter", "level": 5, "xp": adv.xp_for_level("Fighter", 5)}]
    r = cond.drain_levels(cls, 1)
    assert r["classes"][0]["level"] == 4
    assert r["classes"][0]["xp"] == adv.xp_for_level("Fighter", 4)
    assert not r["slain"]
    low = cond.drain_levels([{"class": "Thief", "level": 1, "xp": 0}], 1)
    assert low["slain"]


def test_level_drain_hits_highest_class():
    cls = [{"class": "Fighter", "level": 3, "xp": adv.xp_for_level("Fighter", 3)},
           {"class": "Magic-User", "level": 6, "xp": adv.xp_for_level("Magic-User", 6)}]
    r = cond.drain_levels(cls, 1)
    levels = {c["class"]: c["level"] for c in r["classes"]}
    assert levels["Magic-User"] == 5 and levels["Fighter"] == 3


def test_grapple_and_overbear_resolve():
    atk = {"ac": 10, "dex": 16, "str": 17, "move": 120, "size": "medium"}
    dfn = {"ac": 10, "dex": 10, "str": 10, "move": 120, "size": "medium"}
    g = cond.unarmed_attack(Dice(seed=5), "grapple", atk, dfn)
    assert g["mode"] == "grapple" and isinstance(g["hit"], bool)
    if g["hit"]:
        assert "hold" in g and g["real_damage"] >= 0
    o = cond.unarmed_attack(Dice(seed=5), "overbear", atk, dfn)
    assert o["mode"] == "overbear"


def test_determinism():
    a = cond.unarmed_attack(Dice(seed=8), "grapple",
                            {"ac": 8, "dex": 15, "str": 16, "move": 90},
                            {"ac": 5, "dex": 12, "str": 12, "move": 60})
    b = cond.unarmed_attack(Dice(seed=8), "grapple",
                            {"ac": 8, "dex": 15, "str": 16, "move": 90},
                            {"ac": 5, "dex": 12, "str": 12, "move": 60})
    assert a == b


def _fighter(repo, cid, name, level=5, hp=40):
    return repo.save_character(cid, {
        "name": name, "race": "Human",
        "classes": [{"class": "Fighter", "level": level,
                     "xp": adv.xp_for_level("Fighter", level)}],
        "alignment": "N", "str": 16, "dex": 12, "con": 14, "int": 9, "wis": 9,
        "cha": 9, "hp_max": hp, "hp_current": hp, "ac_descending": 4})


def test_tool_drain_reduces_level_hp_and_logs():
    repo = Repo.memory()
    cid = repo.create_campaign("Drain Test")
    _fighter(repo, cid, "Sir Roland", level=5, hp=40)
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    res = t.drain_level(name="Sir Roland", levels=1)
    assert res["classes"][0]["level"] == 4
    assert res["hp_max"] == 32                       # 40 * 4/5
    ch = [c for c in repo.list_characters(cid) if c["name"] == "Sir Roland"][0]
    assert ch["hp_max"] == 32
    assert any(e["kind"] == "drain" for e in repo.recent_events(cid))


def test_tool_poison_kills():
    repo = Repo.memory()
    cid = repo.create_campaign("Poison Test")
    _fighter(repo, cid, "Doomed", level=1, hp=8)
    t = RefereeTools(repo, cid, dice=Dice(seed=99))
    # Force a fail with a huge negative modifier; default poison is fatal.
    res = t.poison_save(name="Doomed", modifier=-50)
    assert res["result"] == "dead"
    ch = [c for c in repo.list_characters(cid) if c["name"] == "Doomed"][0]
    assert ch["alive"] == 0 and ch["status"] == "dead"


def test_tool_grapple_applies_real_damage():
    repo = Repo.memory()
    cid = repo.create_campaign("Grapple Test")
    _fighter(repo, cid, "Bruiser", level=4, hp=30)
    _fighter(repo, cid, "Victim", level=2, hp=20)
    t = RefereeTools(repo, cid, dice=Dice(seed=4))
    t.start_combat(combatants=[{"name": "Bruiser", "side": "party"},
                               {"name": "Victim", "side": "foes"}])
    res = t.grapple(attacker="Bruiser", defender="Victim", mode="grapple")
    assert res["attacker"] == "Bruiser"
    assert any(e["kind"] == "grapple" for e in repo.recent_events(cid))


def test_tool_item_save():
    repo = Repo.memory()
    cid = repo.create_campaign("Item Test")
    t = RefereeTools(repo, cid, dice=Dice(seed=2))
    r = t.item_save(material="paper", attack="fire", magic_bonus=0)
    assert r["target"] == 20 and "saved" in r


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All conditions tests passed.")
