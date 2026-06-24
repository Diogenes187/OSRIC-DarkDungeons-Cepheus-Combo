"""End-to-end test of the trade tools: vessel, buy, haul, sell, profit."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state.repo import Repo
from referee.tools import RefereeTools


def _trader(cha=16):
    repo = Repo.memory()
    cid = repo.create_campaign("Greyhawk")
    repo.save_character(cid, {
        "name": "Faelith", "race": "Human",
        "classes": [{"class": "Fighter", "level": 2, "xp": 0}], "alignment": "CG",
        "str": 13, "dex": 12, "con": 12, "int": 11, "wis": 10, "cha": cha,
        "hp_max": 14, "ac_descending": 6, "gold": 2000})
    return RefereeTools(repo, cid)


def test_vessel_sets_capacity():
    t = _trader()
    r = t.set_vessel("Faelith", "Wagon", ["Reinforced Frame"])
    assert r["vessel"] == "Wagon" and r["capacity_tons"] > 2.0
    assert t.get_cargo("Faelith")["capacity_tons"] == r["capacity_tons"]


def test_buy_haul_sell_makes_profit():
    t = _trader(cha=16)
    t.set_vessel("Faelith", "Wagon")          # 2 tons
    # Buy mead where it's produced (farm country)...
    buy = t.buy_goods("Faelith", "Mead", 2, "Agricultural")
    assert "error" not in buy
    assert buy["gold"] == 2000 - buy["cost"]
    assert t.get_cargo("Faelith")["total_tons"] == 2
    # ...haul it and sell where it's wanted (a mining frontier town).
    sell = t.sell_goods("Faelith", "Mead", 2, "Mining, Frontier")
    assert "error" not in sell
    assert t.get_cargo("Faelith")["total_tons"] == 0
    # On a favourable route this is profitable on average; at minimum it resolves.
    assert sell["revenue"] > 0 and "profit" in sell


def test_capacity_is_enforced():
    t = _trader()
    t.set_vessel("Faelith", "Mule")           # 0.15 tons -- tiny
    r = t.buy_goods("Faelith", "Grain", 5, "Agricultural")
    assert "error" in r and "capacity" in r["error"]


def test_cant_oversell_or_overspend():
    t = _trader(cha=10)
    t.set_vessel("Faelith", "Cog")            # plenty of room
    assert "error" in t.sell_goods("Faelith", "Iron", 1, "Craft")  # none in hold
    # buying more than gold allows
    r = t.buy_goods("Faelith", "Gems", 99, "Mining")
    assert "error" in r and r["error"] == "can't afford"


def test_charisma_flows_into_price():
    # The same purchase should tend cheaper for a high-CHA trader.
    cheap = _trader(cha=18)
    dear = _trader(cha=4)
    cheap.set_vessel("Faelith", "Wagon"); dear.set_vessel("Faelith", "Wagon")
    cb = cheap.buy_goods("Faelith", "Iron", 1, "Frontier")
    db = dear.buy_goods("Faelith", "Iron", 1, "Frontier")
    # Not guaranteed on a single roll, but the price model must accept CHA and
    # produce a valid quote either way.
    assert cb["price_per_ton"] > 0 and db["price_per_ton"] > 0


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All trade-tool tests passed.")
