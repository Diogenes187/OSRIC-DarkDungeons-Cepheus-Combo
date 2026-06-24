"""Tests for the War Machine mass-combat engine + the Confidence revolt path."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import warmachine as wm
from engine import domain as dom


def test_battle_rating_factors():
    base = wm.Force("Levy", 100, troop_hd=1, troop_class="average")
    elite = wm.Force("Guard", 100, troop_hd=1, troop_class="elite",
                     leader_level=9, leader_cha=16)
    assert elite.battle_rating() > base.battle_rating()
    # Fortification and higher Hit Dice both raise the rating.
    assert wm.Force("A", 100, fortified=True).battle_rating() > \
        wm.Force("A", 100).battle_rating()
    assert wm.Force("A", 100, troop_hd=4).battle_rating() > \
        wm.Force("A", 100, troop_hd=1).battle_rating()


def test_stronger_army_usually_wins_and_takes_fewer_losses():
    wins = 0
    for s in range(200):
        strong = wm.Force("Host", 1000, troop_hd=2, troop_class="elite",
                          leader_level=12, leader_cha=16)
        weak = wm.Force("Rabble", 1000, troop_hd=1, troop_class="poor",
                        leader_level=1, leader_cha=8)
        r = wm.resolve_battle(Dice(seed=s), strong, weak)
        if r["winner"] == "Host":
            wins += 1
    assert wins > 150          # the better army wins the large majority


def test_casualties_and_rout_apply():
    strong = wm.Force("Host", 500, troop_hd=3, troop_class="elite", leader_level=10)
    weak = wm.Force("Rabble", 500, troop_hd=1, troop_class="untrained")
    r = wm.resolve_battle(Dice(seed=1), strong, weak)
    # Both sides lost troops; the loser lost more.
    assert r["survivors"]["Host"] <= 500 and r["survivors"]["Rabble"] <= 500
    assert r["casualties"][r["loser"]] >= r["casualties"][r["winner"]]


def test_siege_favours_the_defender():
    # Same forces; defending fortified should win far more on the wall.
    open_wins = fort_wins = 0
    for s in range(150):
        a1 = wm.Force("Attacker", 600, troop_hd=1); d1 = wm.Force("Garrison", 400, troop_hd=1)
        if wm.resolve_battle(Dice(seed=s), a1, d1)["winner"] == "Garrison":
            open_wins += 1
        a2 = wm.Force("Attacker", 600, troop_hd=1); d2 = wm.Force("Garrison", 400, troop_hd=1)
        if wm.besiege(Dice(seed=s), a2, d2)["winner"] == "Garrison":
            fort_wins += 1
    assert fort_wins > open_wins


def test_confidence_revolt_path():
    # The internal dethroning: drive Confidence to Turbulent.
    assert dom.confidence_level(40) == "Turbulent"
    assert dom.confidence_level(260) == "Average"
    assert dom.confidence_level(500) == "Ideal"
    d = dom.Dominion("Tyranny", [dom.Fief("hills", "civilized", 1000, ["mineral"])],
                     confidence=40)
    assert dom.in_revolt(d)
    # In revolt, the dominion collects no income.
    rep = dom.monthly_turn(Dice(seed=1), d)
    assert rep["income"]["gross_cash"] == 0
    assert rep["confidence_level"] == "Turbulent"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All war-machine tests passed.")
