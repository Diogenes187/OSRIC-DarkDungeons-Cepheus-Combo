"""Tests for the premade dominion (yearly) events."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import dominion_events as de
from engine.data import dominion_events as deck
from state.repo import Repo
from referee.tools import RefereeTools


def test_type_table_bands():
    assert deck.category_for(1) == "major_positive"
    assert deck.category_for(5) == "major_positive"
    assert deck.category_for(24) == "minor_positive"
    assert deck.category_for(25) == "neutral"
    assert deck.category_for(40) == "neutral"
    assert deck.category_for(41) == "minor_negative"
    assert deck.category_for(76) == "major_negative"
    assert deck.category_for(96) == "disaster"
    assert deck.category_for(100) == "disaster"


def test_deck_is_well_formed():
    for cat, pool in deck.EVENTS.items():
        assert pool, cat
        for name, conf, income, pop, desc in pool:
            assert name and desc
            assert -25 <= conf <= 25
            assert -100 <= income <= 100
            assert -25 <= pop <= 25
        # positives lift confidence, disasters never do
        if cat.endswith("positive"):
            assert all(c >= 0 for _, c, _, _, _ in pool)
        if cat in ("major_negative", "disaster"):
            assert all(c <= 0 for _, c, _, _, _ in pool)


def test_roll_yearly_structure_and_determinism():
    a = de.roll_yearly(Dice(seed=7), count=3)
    b = de.roll_yearly(Dice(seed=7), count=3)
    assert a == b
    assert a["count"] == 3
    for e in a["events"]:
        assert {"category", "event", "confidence", "income_pct",
                "population_pct"} <= set(e)
    assert a["total_confidence"] == sum(e["confidence"] for e in a["events"])


def test_roll_yearly_defaults_to_1d4():
    r = de.roll_yearly(Dice(seed=2))
    assert 1 <= r["count"] <= 4


def test_tool_applies_confidence_and_population_and_logs():
    repo = Repo.memory()
    cid = repo.create_campaign("Realm Test")
    repo.create_dominion(
        cid, "Marchland", ruler="Baron Kord", title="Baron", confidence=100,
        fiefs=[{"terrain": "plains", "civ_level": "civilized", "families": 400,
                "resources": ["animal"]}])
    t = RefereeTools(repo, cid, dice=Dice(seed=4))
    res = t.dominion_events(dominion="Marchland", count=4)
    assert res["count"] == 4
    expected = max(0, 100 + sum(e["confidence"] for e in res["events"]))
    assert res["confidence_after"] == expected
    # The dominion record was updated.
    row = repo.get_dominion(cid, "Marchland")
    assert row["confidence"] == expected
    # Events are written to the chronicle as realm events.
    assert sum(1 for e in repo.recent_events(cid) if e["kind"] == "realm") == 4


def test_tool_confidence_floored_at_zero():
    repo = Repo.memory()
    cid = repo.create_campaign("Doom Realm")
    repo.create_dominion(
        cid, "Bleakhold", ruler="Lord Vane", confidence=10,
        fiefs=[{"terrain": "hills", "civ_level": "wilderness", "families": 100,
                "resources": ["mineral"]}])
    t = RefereeTools(repo, cid, dice=Dice(seed=1))
    # Many events can't push confidence below zero.
    res = t.dominion_events(dominion="Bleakhold", count=4)
    assert res["confidence_after"] >= 0


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All dominion-events tests passed.")
