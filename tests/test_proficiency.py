"""Tests for weapon proficiency and dungeon exploration procedures."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import exploration as ex
from engine.data import proficiency as prof
from state.repo import Repo
from referee.tools import RefereeTools


def test_proficiency_slots_and_penalty():
    assert prof.slots("Fighter", 1) == 4
    assert prof.slots("Fighter", 3) == 5            # gains one at 3rd
    assert prof.slots("Magic-User", 1) == 1
    assert prof.slots("Magic-User", 6) == 2
    assert prof.penalty("Fighter") == -2
    assert prof.penalty("Magic-User") == -5
    assert prof.best_penalty([{"class": "Fighter", "level": 1},
                              {"class": "Magic-User", "level": 1}]) == -2


def test_search_and_listen_by_ancestry():
    assert ex.search_secret_doors(Dice(seed=1), "Elf")["chance_in_6"] == 2
    assert ex.search_secret_doors(Dice(seed=1), "Human")["chance_in_6"] == 1
    assert ex.search_traps(Dice(seed=1), "Dwarf")["chance_in_6"] == 3
    assert ex.search_traps(Dice(seed=1), "Human")["chance_in_6"] == 2
    assert ex.listen_at_door(Dice(seed=1), "Gnome")["chance_in_6"] == 2


def test_strength_feats():
    fd = ex.force_door(Dice(seed=1), 18, 76)        # Str 18/76 -> open doors 4 in 6
    assert fd["target_in_6"] == 4 and isinstance(fd["success"], bool)
    bb = ex.bend_bars(Dice(seed=1), 18, 76)         # -> 30% bend bars
    assert bb["chance_pct"] == 30 and isinstance(bb["success"], bool)


def test_surprise_returns_segments():
    s = ex.surprise(Dice(seed=2), party_best_dex=16, foe_best_dex=10)
    assert "party_surprised_segments" in s and "foes_surprised_segments" in s


def test_light_durations():
    assert ex.light_duration("torch")["turns"] == 6
    assert ex.light_duration("lantern, hooded")["turns"] == 24


def _fighter(repo, cid, name="Brand", str_score=15, pct=0):
    return repo.save_character(cid, {
        "name": name, "race": "Human", "classes": [{"class": "Fighter", "level": 2}],
        "alignment": "N", "str": str_score, "str_pct": pct, "dex": 12, "con": 12,
        "int": 9, "wis": 9, "cha": 9, "hp_max": 20, "hp_current": 20,
        "ac_descending": 4})


def test_tool_nonproficiency_penalty_in_attack():
    repo = Repo.memory()
    cid = repo.create_campaign("Prof Test")
    _fighter(repo, cid, "Brand")
    _fighter(repo, cid, "Target")
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    t.set_proficiencies(name="Brand", weapons=["Dagger"])
    t.start_combat(combatants=[{"name": "Brand", "side": "party"},
                               {"name": "Target", "side": "foes"}])
    res = t.attack(attacker="Brand", defender="Target", weapon="Sword, long")
    assert res["non_proficiency_penalty"] == -2
    res2 = t.attack(attacker="Brand", defender="Target", weapon="Dagger")
    assert "non_proficiency_penalty" not in res2


def test_tool_no_penalty_without_proficiency_list():
    repo = Repo.memory()
    cid = repo.create_campaign("NoProf Test")
    _fighter(repo, cid, "Brand")
    _fighter(repo, cid, "Target")
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    t.start_combat(combatants=[{"name": "Brand", "side": "party"},
                               {"name": "Target", "side": "foes"}])
    res = t.attack(attacker="Brand", defender="Target", weapon="Sword, long")
    assert "non_proficiency_penalty" not in res     # no list -> assume proficient


def test_tool_exploration_flow():
    repo = Repo.memory()
    cid = repo.create_campaign("Explore Test")
    repo.save_character(cid, {
        "name": "Legolas", "race": "Elf", "classes": [{"class": "Fighter", "level": 3}],
        "alignment": "CG", "str": 16, "dex": 18, "con": 12, "int": 12, "wis": 12,
        "cha": 12, "hp_max": 22, "hp_current": 22, "ac_descending": 4})
    t = RefereeTools(repo, cid, dice=Dice(seed=3))
    assert t.search(name="Legolas", what="secret doors")["chance_in_6"] == 2
    assert "success" in t.listen_at_door(name="Legolas")
    assert "success" in t.force_door(name="Legolas")
    surp = t.surprise_check(party=["Legolas"], foe_dex=10)
    assert "party_surprised_segments" in surp


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All proficiency/exploration tests passed.")
