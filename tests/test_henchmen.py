"""Tests for loyalty, henchmen, morale, and reaction."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import henchmen
from engine.data import loyalty as L
from state.repo import Repo
from referee.tools import RefereeTools


def test_charisma_table_values():
    assert L.max_henchmen(9) == 4 and L.loyalty_modifier(9) == 0
    assert L.max_henchmen(18) == 15 and L.loyalty_modifier(18) == 40
    assert L.reaction_modifier(18) == 35
    assert L.max_henchmen(3) == 1 and L.loyalty_modifier(3) == -30
    assert L.loyalty_modifier(10) == 0      # 9-11 bracket


def test_alignment_axis_modifier():
    assert henchmen.pc_alignment_mod("LG") == 15
    assert henchmen.pc_alignment_mod("CE") == -15
    assert henchmen.pc_alignment_mod("N") == 0
    assert henchmen.pc_alignment_mod("LN") == 10
    assert henchmen.pc_alignment_mod("NG") == 5


def test_compute_loyalty_breakdown():
    # Cha 15 (+15), LG master (+15), henchman (+10), well-paid (+5), kind (+10):
    r = henchmen.compute_loyalty(15, alignment="LG", status="henchman",
                                 payment="good", treatment="kind")
    assert r["factors"]["charisma"] == 15
    assert r["factors"]["pc_alignment"] == 15
    assert r["loyalty"] == 50 + 15 + 15 + 0 + 10 + 0 + 0 + 5 + 10 + 0   # 105
    assert r["band"] == "Fanatical"


def test_loyalty_bands():
    assert L.loyalty_band(0) == "None"
    assert L.loyalty_band(40) == "Somewhat Loyal"
    assert L.loyalty_band(100) == "Loyal"
    assert L.loyalty_band(120) == "Fanatical"


def test_loyalty_test_holds_on_low_roll():
    # Loyalty 95 should hold on almost any roll; check determinism + logic.
    r = henchmen.loyalty_test(Dice(seed=1), 95)
    assert r["holds"] == (r["roll"] <= 95)
    a = henchmen.loyalty_test(Dice(seed=5), 60)
    b = henchmen.loyalty_test(Dice(seed=5), 60)
    assert a == b


def test_npc_morale_thresholds_and_outcomes():
    r = henchmen.npc_morale(Dice(seed=2), hit_dice=4, loyalty_mod=20)
    assert r["morale"] == 50 + 20 + 20            # 50 + 5*4 + 20
    assert r["outcome"] in ("holds", "retreats", "surrenders")
    # A heavy situation penalty makes holding far harder.
    weak = henchmen.npc_morale(Dice(seed=2), hit_dice=1, situational=60)
    assert weak["morale"] == 50 + 5 - 60


def test_reaction_uses_charisma_modifier():
    high = henchmen.reaction_roll(Dice(seed=3), cha_reaction_mod=35)
    low = henchmen.reaction_roll(Dice(seed=3), cha_reaction_mod=-25)
    assert high["total"] > low["total"]           # same roll, better modifier
    assert high["reaction"] in ("Very hostile", "Hostile", "Unfavorable",
                                "Neutral", "Favorable", "Friendly", "Very friendly")


def _make_master(repo, cid, cha=16, align="LG"):
    return repo.save_character(cid, {
        "name": "Lord Aric", "race": "Human",
        "classes": [{"class": "Fighter", "level": 5}], "alignment": align,
        "str": 15, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": cha,
        "hp_max": 40, "hp_current": 40, "ac_descending": 2})


def test_tool_hire_list_and_check():
    repo = Repo.memory()
    cid = repo.create_campaign("Hench Test")
    _make_master(repo, cid, cha=16)
    t = RefereeTools(repo, cid, dice=Dice(seed=4))
    hire = t.hire_henchman(master="Lord Aric", name="Sergeant Doru",
                           char_class="Fighter", level=2, hp=14,
                           status="henchman", payment="good", treatment="kind")
    # Cha16 +20, LG +15, henchman +10, good pay +5, kind +10 -> 50+60 = 110
    assert hire["loyalty"] == 110 and hire["band"] == "Fanatical"
    assert hire["henchman_limit"] == 8
    lst = t.list_henchmen(master="Lord Aric")
    assert lst["retainers"][0]["name"] == "Sergeant Doru"
    chk = t.loyalty_check(name="Sergeant Doru")
    assert "holds" in chk
    assert any(e["kind"] == "retainer" for e in repo.recent_events(cid))
    assert any(e["kind"] == "loyalty" for e in repo.recent_events(cid))


def test_tool_set_retainer_changes_loyalty():
    repo = Repo.memory()
    cid = repo.create_campaign("Pay Test")
    _make_master(repo, cid, cha=12, align="N")
    t = RefereeTools(repo, cid, dice=Dice(seed=4))
    t.hire_henchman(master="Lord Aric", name="Mook", status="hireling")
    before = t.list_henchmen(master="Lord Aric")["retainers"][0]["loyalty"]
    after = t.set_retainer(name="Mook", payment="unpaid", treatment="cruel")
    assert after["loyalty"] < before            # mistreatment lowers loyalty


def test_tool_henchman_limit_warning():
    repo = Repo.memory()
    cid = repo.create_campaign("Limit Test")
    repo.save_character(cid, {
        "name": "Weakly", "race": "Human",
        "classes": [{"class": "Magic-User", "level": 1}], "alignment": "N",
        "str": 8, "dex": 10, "con": 10, "int": 15, "wis": 10, "cha": 3,
        "hp_max": 4, "hp_current": 4, "ac_descending": 10})
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    t.hire_henchman(master="Weakly", name="A", status="henchman")
    second = t.hire_henchman(master="Weakly", name="B", status="henchman")
    assert "warning" in second                  # Cha 3 -> limit 1


def test_tool_reaction_and_morale():
    repo = Repo.memory()
    cid = repo.create_campaign("React Test")
    _make_master(repo, cid, cha=18)
    t = RefereeTools(repo, cid, dice=Dice(seed=7))
    rx = t.reaction_roll(negotiator="Lord Aric")
    assert rx["modifier"] == 35 and "reaction" in rx
    t.hire_henchman(master="Lord Aric", name="Pike", char_class="Fighter",
                    level=3, hp=20)
    mor = t.npc_morale(name="Pike")
    assert mor["morale"] == 50 + 5 * 3 + L.loyalty_modifier(18)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All henchmen tests passed.")
