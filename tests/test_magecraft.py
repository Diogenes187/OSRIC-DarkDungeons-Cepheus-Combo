"""Tests for the magic economy: learning, research, scribing, brewing."""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import magecraft as mc
from state.repo import Repo
from referee.tools import RefereeTools


def test_understand_chance_table():
    assert mc.understand_chance(9) == {"chance": 35, "max_per_level": 6}
    assert mc.understand_chance(14) == {"chance": 55, "max_per_level": 9}
    assert mc.understand_chance(18) == {"chance": 85, "max_per_level": 18}
    assert mc.understand_chance(19)["chance"] == 90
    assert mc.understand_chance(8)["chance"] == 0


def test_learn_spell_cost_and_divine_auto():
    arc = mc.learn_spell(Dice(seed=1), int_score=18, spell_level=3)
    assert arc["cost_gp"] == 300 and arc["hours"] == 3
    assert arc["chance"] == 85 and isinstance(arc["understood"], bool)
    div = mc.learn_spell(Dice(seed=1), int_score=9, spell_level=2, divine=True)
    assert div["understood"] is True and div["cost_gp"] == 200


def test_research_formula_and_cost():
    r = mc.research_spell(Dice(seed=2), ability_score=18, caster_level=12,
                          spell_level=3, increments=2)
    assert r["base_chance"] == 30                      # 10 + 2*10
    assert r["chance"] == 30 + 18 + 12 - 6             # = 54
    assert r["weeks"] == 4                             # level + 1
    # facility 200*3 + increments 2*2000*3 + weekly(>=4*100)
    assert r["cost_gp"] >= 600 + 12000 + 400
    assert isinstance(r["success"], bool)


def test_research_without_facility_is_dearer():
    cheap = mc.research_spell(Dice(seed=5), 16, 9, 2, has_facility=True)
    dear = mc.research_spell(Dice(seed=5), 16, 9, 2, has_facility=False)
    assert dear["cost_gp"] > cheap["cost_gp"]          # 2000 vs 200 per level


def test_scribe_scroll_cost_and_failure_band():
    s = mc.scribe_scroll(Dice(seed=3), spell_level=4)
    assert s["cost_gp"] == 200 and s["days"] == 4 and s["failure_chance"] == 20
    over = mc.scribe_scroll(Dice(seed=3), spell_level=4, overworked=True)
    assert over["failure_chance"] == 40


def test_brew_potion_cost_and_time():
    b = mc.brew_potion(Dice(seed=1), potion_value_gp=400)
    assert b["cost_gp"] == 200 and b["days"] == 4      # ceil(200/50)


def _mage(repo, cid, name="Mordmain", level=12, int_score=18, gold=50000):
    return repo.save_character(cid, {
        "name": name, "race": "Human",
        "classes": [{"class": "Magic-User", "level": level}], "alignment": "N",
        "str": 9, "dex": 12, "con": 12, "int": int_score, "wis": 10, "cha": 10,
        "hp_max": 24, "hp_current": 24, "ac_descending": 10, "gold": gold})


def test_tool_learn_spell_charges_ink_and_books_on_success():
    repo = Repo.memory()
    cid = repo.create_campaign("Learn Test")
    _mage(repo, cid, "Mordain", int_score=19, gold=1000)
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    res = t.learn_spell(name="Mordain", spell="Fireball", spell_level=3)
    ch = [c for c in repo.list_characters(cid) if c["name"] == "Mordain"][0]
    assert ch["gold"] == 1000 - 300                    # ink charged either way
    if res["understood"]:
        assert "Fireball" in json.loads(ch["spellbook_json"])
    assert any(e["kind"] == "magic" for e in repo.recent_events(cid))


def test_tool_research_adds_on_success():
    repo = Repo.memory()
    cid = repo.create_campaign("Research Test")
    _mage(repo, cid, "Mordain", level=14, int_score=18, gold=100000)
    t = RefereeTools(repo, cid, dice=Dice(seed=4))
    res = t.research_spell(name="Mordain", spell="Mordain's Murk",
                           spell_level=2, increments=4)
    assert "success" in res and res["cost_gp"] > 0
    ch = [c for c in repo.list_characters(cid) if c["name"] == "Mordain"][0]
    assert ch["gold"] == 100000 - res["cost_gp"]


def test_tool_scribe_requires_level_7():
    repo = Repo.memory()
    cid = repo.create_campaign("Scribe Test")
    _mage(repo, cid, "Apprentice", level=5, gold=10000)
    t = RefereeTools(repo, cid, dice=Dice(seed=2))
    assert "error" in t.scribe_scroll(name="Apprentice", spell="Light", spell_level=1)
    _mage(repo, cid, "Archmage", level=9, gold=10000)
    ok = t.scribe_scroll(name="Archmage", spell="Lightning Bolt", spell_level=3)
    assert ok["cost_gp"] == 150
    if ok["success"]:
        ch = [c for c in repo.list_characters(cid) if c["name"] == "Archmage"][0]
        gear = json.loads(ch["gear_json"])
        assert any("Scroll" in (g.get("item") if isinstance(g, dict) else g)
                   for g in gear)


def test_tool_brew_potion_adds_gear():
    repo = Repo.memory()
    cid = repo.create_campaign("Brew Test")
    _mage(repo, cid, "Alchemmaster", level=8, gold=10000)
    t = RefereeTools(repo, cid, dice=Dice(seed=3))
    res = t.brew_potion(name="Alchemmaster", potion="Healing", value_gp=400)
    assert res["cost_gp"] == 200
    ch = [c for c in repo.list_characters(cid) if c["name"] == "Alchemmaster"][0]
    assert any("Potion: Healing" in (g.get("item") if isinstance(g, dict) else g)
               for g in json.loads(ch["gear_json"]))


def test_tool_non_caster_rejected():
    repo = Repo.memory()
    cid = repo.create_campaign("NonCaster")
    repo.save_character(cid, {
        "name": "Grunt", "race": "Human", "classes": [{"class": "Fighter", "level": 9}],
        "alignment": "N", "str": 17, "dex": 12, "con": 14, "int": 9, "wis": 9,
        "cha": 9, "hp_max": 60, "hp_current": 60, "ac_descending": 2, "gold": 5000})
    t = RefereeTools(repo, cid)
    assert "error" in t.learn_spell(name="Grunt", spell="Sleep", spell_level=1)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All magecraft tests passed.")
