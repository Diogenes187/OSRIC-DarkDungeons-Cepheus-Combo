"""Tests for weapon specialisation and dual-classing."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import specialization as spec
from engine import leveling
from engine.data import advancement as adv
from engine.data import saves as saves_mod
from engine.data import attack as attack_mod
from state.repo import Repo
from referee.tools import RefereeTools


def test_attack_rate_and_bonuses():
    assert spec.melee_attack_rate(5) == "3/2"
    assert spec.melee_attack_rate(10) == "2/1"
    assert spec.melee_attack_rate(13) == "5/2"
    assert spec.bonuses(False) == {"to_hit": 1, "damage": 2}
    assert spec.bonuses(True) == {"to_hit": 1, "damage": 3}


def test_assess_matches_weapon():
    s = {"weapon": "Sword, long", "double": False}
    hit = spec.assess(s, "Sword, long", 7)
    assert hit["to_hit"] == 1 and hit["damage"] == 2 and hit["attack_rate"] == "2/1"
    assert spec.assess(s, "Dagger", 7) is None
    assert spec.assess(None, "Sword, long", 7) is None


def test_missile_rate():
    assert spec.missile_rate("Bow, long", 5) == "2"
    assert spec.missile_rate("Bow, long", 8) == "3"
    assert spec.missile_rate("Crossbow, light", 13) == "2"


def test_suppressed_class_excluded_from_best_of():
    classes = [{"class": "Fighter", "level": 6,
                "xp": adv.xp_for_level("Fighter", 6), "suppressed": True},
               {"class": "Magic-User", "level": 1, "xp": 0}]
    norm = leveling.normalize(classes)
    # Only the active (Magic-User) class counts while the fighter is suppressed.
    assert leveling.best_thac0(norm) == attack_mod.thac0("Magic-User", 1)
    assert leveling.active(norm)[0]["class"] == "Magic-User"


def test_dual_grant_routes_xp_and_regains():
    classes = [{"class": "Fighter", "level": 6,
                "xp": adv.xp_for_level("Fighter", 6), "suppressed": True},
               {"class": "Magic-User", "level": 1, "xp": 0}]
    # Enough XP to push Magic-User to level 7 (past the old fighter level 6).
    res = leveling.grant_xp_dual(Dice(seed=1), classes, adv.xp_for_level("Magic-User", 7),
                                 con=12, from_class="Fighter", from_level=6,
                                 to_class="Magic-User")
    mu = [c for c in res["classes"] if c["class"] == "Magic-User"][0]
    assert mu["level"] == 7
    assert res["regained_old_class"] is True
    # Old class no longer suppressed.
    assert all("suppressed" not in c for c in res["classes"])


def test_dual_grant_no_hp_until_past_old_level():
    classes = [{"class": "Fighter", "level": 6,
                "xp": adv.xp_for_level("Fighter", 6), "suppressed": True},
               {"class": "Magic-User", "level": 1, "xp": 0}]
    # Only to level 5 -- still under the old fighter level, so no HP yet.
    res = leveling.grant_xp_dual(Dice(seed=1), classes, adv.xp_for_level("Magic-User", 5),
                                 con=12, from_class="Fighter", from_level=6,
                                 to_class="Magic-User")
    assert res["hp_gained"] == 0 and res["regained_old_class"] is False


def _human_fighter(repo, cid, name="Aldric", level=6, **scores):
    base = {"str": 16, "dex": 12, "con": 12, "int": 17, "wis": 10, "cha": 10}
    base.update(scores)
    d = {"name": name, "race": "Human",
         "classes": [{"class": "Fighter", "level": level,
                      "xp": adv.xp_for_level("Fighter", level)}],
         "alignment": "N", "hp_max": 48, "hp_current": 48, "ac_descending": 2}
    d.update(base)
    return repo.save_character(cid, d)


def test_tool_specialisation_applies_in_attack():
    repo = Repo.memory()
    cid = repo.create_campaign("Spec Test")
    _human_fighter(repo, cid, "Aldric", level=5)
    repo.save_character(cid, {
        "name": "Dummy", "race": "Human", "classes": [{"class": "Fighter", "level": 1}],
        "alignment": "N", "str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10,
        "cha": 10, "hp_max": 100, "hp_current": 100, "ac_descending": 10})
    t = RefereeTools(repo, cid, dice=Dice(seed=2))
    setup = t.set_weapon_specialisation(name="Aldric", weapon="Sword, long")
    assert setup["to_hit"] == 1 and setup["damage"] == 2 and setup["attack_rate"] == "3/2"
    t.start_combat(combatants=[{"name": "Aldric", "side": "party"},
                               {"name": "Dummy", "side": "foes"}])
    res = t.attack(attacker="Aldric", defender="Dummy", weapon="Sword, long")
    assert res["weapon"] == "Sword, long" and res.get("specialised") is True
    assert res["attack_rate"] == "3/2"


def test_tool_specialisation_rejects_mage():
    repo = Repo.memory()
    cid = repo.create_campaign("Spec Reject")
    repo.save_character(cid, {
        "name": "Wizzo", "race": "Human", "classes": [{"class": "Magic-User", "level": 3}],
        "alignment": "N", "str": 9, "dex": 12, "con": 10, "int": 16, "wis": 10,
        "cha": 10, "hp_max": 8, "hp_current": 8, "ac_descending": 10})
    t = RefereeTools(repo, cid)
    assert "error" in t.set_weapon_specialisation(name="Wizzo", weapon="Dagger")


def test_tool_dual_class_flow_and_requirements():
    repo = Repo.memory()
    cid = repo.create_campaign("Dual Test")
    _human_fighter(repo, cid, "Aldric", level=6, str=16, int=17)
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    res = t.dual_class(name="Aldric", to_class="Magic-User")
    assert res["from"] == "Fighter" and res["to"] == "Magic-User"
    # While suppressed, saves as a 1st-level Magic-User, not a 6th-level Fighter.
    sv = t.saving_throw(name="Aldric", category="death")
    assert sv["target"] == saves_mod.save_target("Magic-User", 1, "death")
    # Granting XP routes it all to the Magic-User.
    t.grant_xp(amount=adv.xp_for_level("Magic-User", 2), name="Aldric")
    ch = [c for c in repo.list_characters(cid) if c["name"] == "Aldric"][0]
    import json
    classes = {c["class"]: c for c in json.loads(ch["classes_json"])}
    assert classes["Magic-User"]["level"] == 2 and classes["Fighter"]["level"] == 6


def test_tool_dual_class_requirement_failure():
    repo = Repo.memory()
    cid = repo.create_campaign("Dual Reject")
    # int 12 is too low to become a Magic-User (needs 17).
    _human_fighter(repo, cid, "Brute", level=6, str=16, int=12)
    t = RefereeTools(repo, cid)
    assert "error" in t.dual_class(name="Brute", to_class="Magic-User")
    # Non-humans can't dual-class at all.
    repo.save_character(cid, {
        "name": "Elwood", "race": "Elf", "classes": [{"class": "Fighter", "level": 6}],
        "alignment": "N", "str": 17, "dex": 16, "con": 12, "int": 17, "wis": 10,
        "cha": 10, "hp_max": 40, "hp_current": 40, "ac_descending": 4})
    assert "error" in t.dual_class(name="Elwood", to_class="Magic-User")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All specialisation/dual-class tests passed.")
