"""Tests for ship-to-ship naval combat."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import naval


def test_hull_scales_with_tonnage():
    cog = naval.from_vessel("Cog", "Cog", crew=18)
    barge = naval.from_vessel("Barge", "River Barge", crew=4)
    assert cog.hull > barge.hull            # 100t vs 12t
    assert cog.hull == max(2, round(100 / 5))


def test_battle_resolves_with_a_fate():
    d = Dice(seed=1)
    a = naval.Warship("Reaver", tonnage=30, crew=40, crew_hd=1, crew_class="good",
                      ram=True, leader_level=6)
    b = naval.Warship("Merchant", tonnage=100, crew=18, crew_hd=1,
                      crew_class="poor")
    res = naval.naval_battle(d, a, b)
    assert res["winner"] in ("Reaver", "Merchant")
    assert res["loser_fate"] in ("sunk", "captured", "afloat")
    assert res["rounds"] >= 1 and res["log"]


def test_artillery_and_ram_breach_hulls():
    # A heavy warship with artillery and a ram vs an unarmed merchant.
    wins = 0
    for s in range(100):
        war = naval.Warship("Galley", tonnage=60, crew=70, crew_hd=1,
                            crew_class="elite", ram=True, artillery=2,
                            leader_level=8)
        prey = naval.Warship("Trader", tonnage=40, crew=10, crew_hd=1,
                             crew_class="poor")
        res = naval.naval_battle(Dice(seed=s), war, prey)
        if res["winner"] == "Galley":
            wins += 1
    assert wins > 75                        # the warship dominates


def test_determinism():
    def run():
        d = Dice(seed=7)
        a = naval.Warship("A", 60, 50, ram=True, artillery=1)
        b = naval.Warship("B", 60, 50, ram=True, artillery=1)
        return naval.naval_battle(d, a, b)
    assert run() == run()


def test_naval_tool():
    from state.repo import Repo
    from referee.tools import RefereeTools
    repo = Repo.memory()
    cid = repo.create_campaign("X")
    t = RefereeTools(repo, cid)
    res = t.naval_battle(
        {"name": "Sea Wolf", "vessel_type": "Longship", "crew": 40,
         "crew_class": "good", "ram": True, "leader_level": 6},
        {"name": "Fat Cog", "vessel_type": "Cog", "crew": 18, "crew_class": "poor"})
    assert res["winner"] in ("Sea Wolf", "Fat Cog")
    assert res["loser_fate"] in ("sunk", "captured", "afloat")
    # The battle was recorded to the chronicle.
    evs = repo.recent_events(cid)
    assert any(e["kind"] == "naval" for e in evs)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All naval tests passed.")
