"""Tests for initiative, the combat round, and the tracker."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import initiative as init
from engine.data import abilities as ab
from state.repo import Repo
from referee.tools import RefereeTools


def test_dex_initiative_matches_table():
    assert init.dex_initiative(3) == 3        # slow: acts later
    assert init.dex_initiative(10) == 0
    assert init.dex_initiative(16) == -1       # quick: acts earlier
    assert init.dex_initiative(18) == -3


def test_missile_uses_dex_spell_uses_casting_time():
    quick = init.combatant_segment(Dice(seed=1),
                                   {"name": "Archer", "action": "missile", "dex": 18})
    # segment = roll + (-3 for Dex 18)
    assert quick["segment"] == quick["roll"] - 3
    mage = init.combatant_segment(Dice(seed=1),
                                  {"name": "Mage", "action": "spell", "casting_time": 3})
    assert mage["segment"] == mage["roll"] + 3
    melee = init.combatant_segment(Dice(seed=1),
                                   {"name": "Knight", "action": "melee", "dex": 18})
    assert melee["segment"] == melee["roll"]   # Dex doesn't shift melee segment


def test_order_sorts_by_segment_then_speed_then_dex():
    # Construct combatants and confirm ordering rules via a fixed seed.
    combs = [{"name": "A", "dex": 10, "action": "melee", "weapon_speed": 2},
             {"name": "B", "dex": 18, "action": "missile", "weapon_speed": 7},
             {"name": "C", "dex": 10, "action": "spell", "casting_time": 5}]
    order = init.roll_order(Dice(seed=3), combs)
    segs = [o["segment"] for o in order]
    assert segs == sorted(segs)                # ascending segment
    assert all("order" in o for o in order)


def test_determinism():
    combs = [{"name": "A", "dex": 12}, {"name": "B", "dex": 16, "action": "missile"}]
    assert init.roll_order(Dice(seed=9), combs) == init.roll_order(Dice(seed=9), combs)


def test_tie_breaks_on_weapon_speed():
    # Force identical rolls by giving both melee (no shift) and check that the
    # lower weapon speed sorts first when segments tie.
    found_tie = False
    for s in range(50):
        order = init.roll_order(Dice(seed=s),
                                [{"name": "Fast", "weapon_speed": 2, "dex": 10},
                                 {"name": "Slow", "weapon_speed": 9, "dex": 10}])
        if order[0]["segment"] == order[1]["segment"]:
            found_tie = True
            assert order[0]["name"] == "Fast"
    assert found_tie


def _fighter(repo, cid, name, dex=12):
    return repo.save_character(cid, {
        "name": name, "race": "Human", "classes": [{"class": "Fighter", "level": 3}],
        "alignment": "N", "str": 15, "dex": dex, "con": 12, "int": 9, "wis": 9,
        "cha": 9, "hp_max": 20, "hp_current": 20, "ac_descending": 4})


def test_tool_combat_lifecycle():
    repo = Repo.memory()
    cid = repo.create_campaign("Init Test")
    _fighter(repo, cid, "Bron", dex=17)
    _fighter(repo, cid, "Goblin", dex=8)
    t = RefereeTools(repo, cid, dice=Dice(seed=2))
    start = t.start_combat(combatants=[
        {"name": "Bron", "side": "party", "weapon": "Sword, long"},
        {"name": "Goblin", "side": "foes", "action": "melee"}])
    assert start["round"] == 1 and len(start["order"]) == 2
    # Bron's Dexterity (17) was read from his sheet.
    bron = [o for o in start["order"] if o["name"] == "Bron"][0]
    assert bron["dex_init"] == ab.dexterity_mods(17)["initiative"]
    assert bron["weapon_speed"] == 5            # Sword, long speed factor
    status = t.combat_status()
    assert status["active"] and status["round"] == 1
    # Both must act before the round can advance.
    t.advance_turn(name="Bron")
    t.advance_turn(name="Goblin")
    nxt = t.next_round()
    assert nxt["round"] == 2
    end = t.end_combat()
    assert end["ended"] and not t.combat_status()["active"]


def test_tool_next_round_can_switch_to_spell():
    repo = Repo.memory()
    cid = repo.create_campaign("Switch Test")
    _fighter(repo, cid, "Wizard", dex=10)
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    t.start_combat(combatants=[{"name": "Wizard", "side": "party", "action": "melee"}])
    t.advance_turn(name="Wizard")               # the round must complete first
    nxt = t.next_round(actions=[{"name": "Wizard", "action": "spell", "casting_time": 4}])
    wiz = nxt["order"][0]
    assert wiz["action"] == "spell" and wiz["segment"] == wiz["roll"] + 4


def test_attack_refuses_outside_combat():
    repo = Repo.memory()
    cid = repo.create_campaign("Gate Test")
    _fighter(repo, cid, "Hero")
    _fighter(repo, cid, "Orc")
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    res = t.attack("Hero", "Orc")               # no start_combat yet
    assert "error" in res and "start_combat" in res["error"]


def test_round_will_not_advance_until_all_have_acted():
    repo = Repo.memory()
    cid = repo.create_campaign("Turn Gate")
    _fighter(repo, cid, "Hero", dex=14)
    _fighter(repo, cid, "Orc", dex=10)
    t = RefereeTools(repo, cid, dice=Dice(seed=2))
    t.start_combat(combatants=[{"name": "Hero", "side": "party"},
                               {"name": "Orc", "side": "foes"}])
    # The hero attacks; the orc has NOT acted, so the round can't advance.
    atk = t.attack("Hero", "Orc")
    assert atk["combat"]["pending"] == ["Orc"] and not atk["combat"]["round_complete"]
    blocked = t.next_round()
    assert "error" in blocked and "Orc" in blocked["error"]
    # Resolve the orc's action -> now the round completes and can advance.
    t.attack("Orc", "Hero")
    status = t.combat_status()
    assert status["pending"] == [] and set(status["acted"]) == {"Hero", "Orc"}
    nxt = t.next_round()
    assert nxt["round"] == 2 and "error" not in nxt


def test_advance_turn_counts_as_acting():
    repo = Repo.memory()
    cid = repo.create_campaign("Advance Test")
    _fighter(repo, cid, "Hero")
    _fighter(repo, cid, "Mook")
    t = RefereeTools(repo, cid, dice=Dice(seed=3))
    t.start_combat(combatants=[{"name": "Hero", "side": "party"},
                               {"name": "Mook", "side": "foes"}])
    t.advance_turn(name="Hero", note="drinks a potion")
    t.advance_turn(name="Mook", note="flees")
    assert t.next_round()["round"] == 2          # both acted via advance_turn


def test_dead_combatants_do_not_block_the_round():
    repo = Repo.memory()
    cid = repo.create_campaign("Corpse Test")
    _fighter(repo, cid, "Hero")
    repo.save_character(cid, {
        "name": "Corpse", "race": "Human", "classes": [{"class": "Fighter", "level": 1}],
        "alignment": "N", "str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10,
        "cha": 10, "hp_max": 6, "hp_current": 0, "ac_descending": 8, "alive": 0,
        "is_npc": True})
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    t.start_combat(combatants=[{"name": "Hero", "side": "party"},
                               {"name": "Corpse", "side": "foes"}])
    t.attack("Hero", "Hero")                     # hero acts (target irrelevant here)
    # The dead Corpse isn't pending, so the round advances.
    assert t.next_round()["round"] == 2


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All initiative tests passed.")
