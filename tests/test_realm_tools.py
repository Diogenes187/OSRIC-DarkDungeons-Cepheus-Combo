"""End-to-end test of the realm tools: found a dominion, run it, fight a war."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state.repo import Repo
from referee.tools import RefereeTools


def _campaign():
    repo = Repo.memory()
    cid = repo.create_campaign("Greyhawk")
    repo.save_character(cid, {
        "name": "Faelith", "race": "Human",
        "classes": [{"class": "Fighter", "level": 9, "xp": 250000}],
        "alignment": "CG", "str": 16, "dex": 13, "con": 15, "int": 11,
        "wis": 12, "cha": 15, "hp_max": 60, "ac_descending": 2, "gold": 50000})
    return RefereeTools(repo, cid)


def test_found_and_run_dominion():
    t = _campaign()
    f = t.found_dominion("Faelith", "Mistmoor", "hills", "borderlands",
                         title="Baron")
    assert f["dominion"] == "Mistmoor" and f["families"] > 0
    assert f["confidence"] > 150            # ability total + 150 + d100
    # It persists and lists.
    doms = t.list_dominions()["dominions"]
    assert any(d["name"] == "Mistmoor" for d in doms)
    # Run a month -> banks net into the ruler's purse.
    gold0 = t.get_character("Faelith")["gold"]
    rep = t.domain_turn("Mistmoor", festivals=1)
    assert rep["banked_to"] == "Faelith"
    assert "net_cash" in rep and "income" in rep
    assert t.get_character("Faelith")["gold"] != gold0 or rep["net_cash"] == 0


def test_taxes_shift_confidence():
    t = _campaign()
    t.found_dominion("Faelith", "Mistmoor", "hills", "borderlands")
    r1 = t.set_dominion_tax("Mistmoor", 3.0)      # heavy taxes
    assert r1["confidence_shift"] == -25
    r2 = t.set_dominion_tax("Mistmoor", 1.0)      # ease off
    assert r2["confidence_shift"] == 10


def test_stronghold_quote_tool():
    t = _campaign()
    q = t.build_stronghold({"Keep, Square": 1, "Wall, Castle": 4}, "normal")
    assert q["total_cost"] == 75000 + 4 * 5000
    assert q["engineers"] >= 1 and q["build_days"] > 0


def test_resolve_battle_tool():
    t = _campaign()
    res = t.resolve_battle(
        {"name": "Faelith's Host", "troops": 800, "hit_dice": 1,
         "troop_class": "good", "leader_level": 9, "leader_cha": 15},
        {"name": "Tyrant's Levy", "troops": 600, "hit_dice": 1,
         "troop_class": "poor", "leader_level": 2})
    assert res["winner"] in ("Faelith's Host", "Tyrant's Levy")
    assert "casualties" in res and "survivors" in res
    # A siege variant resolves too.
    s = t.resolve_battle(
        {"name": "Besiegers", "troops": 1000, "hit_dice": 1},
        {"name": "Garrison", "troops": 300, "hit_dice": 1, "fortified": True},
        siege=True)
    assert s.get("siege") is True


def test_list_titles_tool():
    t = _campaign()
    titles = t.list_titles()["titles"]
    assert {x["name"] for x in titles} >= {"Baron", "Duke", "King"}


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All realm-tool tests passed.")
