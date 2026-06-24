"""Tests for random encounters and weather (and their referee tools)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine.data import encounters as enc
from engine.data import weather as wx
from engine.data import monsters as mon
from engine import travel as tv
from state.repo import Repo
from referee.tools import RefereeTools


def test_encounter_tables_reference_real_monsters():
    # Every monster in every terrain table should exist in the bestiary
    # (so a rolled encounter can actually be spawned).
    missing = []
    for terrain, names in enc.TABLES.items():
        for n in names:
            if mon.get(n) is None and not mon.search(n):
                missing.append("{}: {}".format(terrain, n))
    assert not missing, "encounter names not in bestiary: {}".format(missing)


def test_encounter_roll():
    d = Dice(seed=1)
    name = enc.roll(d, "forest")
    assert name in enc.TABLES["forest"]
    assert enc.roll(d, "nope") is None


def test_weather_shape_and_determinism():
    a = wx.generate(Dice(seed=7), "winter")
    b = wx.generate(Dice(seed=7), "winter")
    assert a == b
    assert a["season"] == "winter"
    assert -20 <= a["temperature_f"] <= 110
    assert a["sky"] in ("clear", "partly cloudy", "overcast")
    assert a["wind"] in ("calm", "breezy", "strong winds", "gale")


def test_travel_distance_and_lost():
    # Roads are faster than open terrain; mountains slower.
    assert tv.miles_per_day(120, "road") > tv.miles_per_day(120, "plains")
    assert tv.miles_per_day(120, "mountains") < tv.miles_per_day(120, "plains")
    # A guide prevents getting lost.
    d = Dice(seed=1)
    assert all(not tv.travel_day(d, 120, "swamp", has_guide=True)["lost"]
               for _ in range(50))


def test_tools():
    repo = Repo.memory()
    cid = repo.create_campaign("X")
    t = RefereeTools(repo, cid)
    e = t.random_encounter("dungeon-1")
    assert e["monster"] in enc.TABLES["dungeon-1"]
    assert e["number_appearing"] >= 1
    bad = t.random_encounter("space")
    assert "error" in bad and "terrains" in bad
    w = t.generate_weather("summer")
    assert w["season"] == "summer"
    j = t.journey("forest", days=5, season="autumn")
    assert j["days"] == 5 and len(j["log"]) == 5 and j["total_miles"] > 0


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All exploration tests passed.")
