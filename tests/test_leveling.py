"""Tests for XP, leveling, multi-class best-of, and the grant_xp tool."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import leveling
from engine.data import advancement as adv
from engine.data import attack as attack_mod
from engine.data import saves as saves_mod
from state.repo import Repo
from referee.tools import RefereeTools


def test_xp_thresholds_match_source():
    # Spot-check published OSRIC 3.0 numbers.
    assert adv.xp_for_level("Fighter", 2) == 2000
    assert adv.xp_for_level("Fighter", 9) == 250000
    assert adv.xp_for_level("Magic-User", 4) == 10250
    assert adv.xp_for_level("Thief", 11) == 220000
    assert adv.xp_for_level("Cleric", 1) == 0


def test_level_for_xp_boundaries():
    assert leveling.normalize([{"class": "Fighter", "xp": 0}])[0]["level"] == 1
    assert adv.level_for_xp("Fighter", 1999) == 1
    assert adv.level_for_xp("Fighter", 2000) == 2
    assert adv.level_for_xp("Fighter", 2001) == 2
    # Extrapolate past the printed table (Fighter +250k/level past 20).
    assert adv.level_for_xp("Fighter", 3250000) == 21


def test_assassin_ceiling():
    assert adv.level_for_xp("Assassin", 99_000_000) == 15   # hard cap


def test_single_class_levels_and_gains_hp():
    classes = [{"class": "Fighter", "level": 1, "xp": 0}]
    res = leveling.grant_xp(Dice(seed=1), classes, 2000, con=12)
    assert res["classes"][0]["level"] == 2
    assert res["hp_gained"] >= 1
    assert res["level_ups"] == [{"class": "Fighter", "from": 1, "to": 2}]


def test_prime_bonus_speeds_advancement():
    # 1900 XP is short of 2000; the +10% bonus (->2090) tips Fighter to level 2.
    plain = leveling.grant_xp(Dice(seed=2), [{"class": "Fighter", "xp": 0}],
                              1900, con=10, prime_bonus=False)
    bonus = leveling.grant_xp(Dice(seed=2), [{"class": "Fighter", "xp": 0}],
                              1900, con=10, prime_bonus=True)
    assert plain["classes"][0]["level"] == 1
    assert bonus["classes"][0]["level"] == 2


def test_multiclass_splits_xp_and_levels_independently():
    classes = [{"class": "Fighter", "xp": 0}, {"class": "Magic-User", "xp": 0}]
    # 8000 total -> 4000 each. Fighter(4000)=lvl3, Magic-User(4000)=lvl2.
    res = leveling.grant_xp(Dice(seed=3), classes, 8000, con=12)
    levels = {c["class"]: c["level"] for c in res["classes"]}
    assert levels["Fighter"] == 3 and levels["Magic-User"] == 2
    assert res["xp_each"] == 4000


def test_best_of_class_combat_and_saves():
    # Fighter 5 / Magic-User 9: best attack bonus is the fighter's, best saves
    # mix the better of each column.
    classes = [{"class": "Fighter", "level": 5, "xp": adv.xp_for_level("Fighter", 5)},
               {"class": "Magic-User", "level": 9, "xp": adv.xp_for_level("Magic-User", 9)}]
    norm = leveling.normalize(classes)
    assert leveling.best_thac0(norm) == min(attack_mod.thac0("Fighter", 5),
                                            attack_mod.thac0("Magic-User", 9))
    # Magic-Users save better vs spells; fighters better vs death.
    s_spell = leveling.best_save_target(norm, "spells")
    assert s_spell == min(saves_mod.save_target("Fighter", 5, "spells"),
                          saves_mod.save_target("Magic-User", 9, "spells"))


def test_determinism():
    a = leveling.grant_xp(Dice(seed=9), [{"class": "Cleric", "xp": 0}], 30000, con=15)
    b = leveling.grant_xp(Dice(seed=9), [{"class": "Cleric", "xp": 0}], 30000, con=15)
    assert a == b


def test_grant_xp_tool_party_and_chronicle():
    repo = Repo.memory()
    cid = repo.create_campaign("XP Test")
    repo.save_character(cid, {
        "name": "Brak", "race": "Human", "classes": [{"class": "Fighter", "xp": 0}],
        "str": 16, "dex": 12, "con": 15, "int": 9, "wis": 9, "cha": 9,
        "hp_max": 8, "hp_current": 8, "ac_descending": 4})
    t = RefereeTools(repo, cid, dice=Dice(seed=5))
    res = t.grant_xp(amount=2000)            # party award
    char = res["characters"][0]
    assert char["hp_max"] > 8                # gained hp on level-up
    assert any(lu["to"] == 2 for lu in char["level_ups"])
    # Level-up written to the chronicle.
    assert any(e["kind"] == "level" for e in repo.recent_events(cid))
    # And advancement reporting works.
    adv_out = t.get_advancement(name="Brak")
    assert adv_out["effective_level"] == 2
    assert adv_out["classes"][0]["to_next"] > 0


def test_tool_multiclass_saving_throw_uses_best():
    repo = Repo.memory()
    cid = repo.create_campaign("Save Test")
    repo.save_character(cid, {
        "name": "Mix", "race": "Elf",
        "classes": [{"class": "Fighter", "level": 6, "xp": adv.xp_for_level("Fighter", 6)},
                    {"class": "Magic-User", "level": 6, "xp": adv.xp_for_level("Magic-User", 6)}],
        "str": 15, "dex": 15, "con": 12, "int": 15, "wis": 10, "cha": 10,
        "hp_max": 20, "hp_current": 20, "ac_descending": 5})
    t = RefereeTools(repo, cid, dice=Dice(seed=4))
    r = t.saving_throw(name="Mix", category="spells")
    expected = min(saves_mod.save_target("Fighter", 6, "spells"),
                   saves_mod.save_target("Magic-User", 6, "spells"))
    assert r["target"] == expected


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All leveling tests passed.")
