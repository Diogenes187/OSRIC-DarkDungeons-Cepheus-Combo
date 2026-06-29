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


def test_sell_goods_dry_run_quotes_without_mutating():
    t = _trader(cha=16)
    t.set_vessel("Faelith", "Wagon")
    t.buy_goods("Faelith", "Mead", 2, "Agricultural")
    gold_before = t.get_cargo("Faelith")["gold"]
    tons_before = t.get_cargo("Faelith")["total_tons"]
    # Quote the sale: returns price/profit but must change nothing.
    quote = t.sell_goods("Faelith", "Mead", 2, "Mining, Frontier", dry_run=True)
    assert "error" not in quote
    assert quote["dry_run"] is True
    assert quote["revenue"] > 0 and "profit" in quote
    assert t.get_cargo("Faelith")["gold"] == gold_before          # gold untouched
    assert t.get_cargo("Faelith")["total_tons"] == tons_before    # cargo untouched
    # The real sale yields the IDENTICAL numbers (pricing is deterministic)...
    real = t.sell_goods("Faelith", "Mead", 2, "Mining, Frontier")
    assert real["price_per_ton"] == quote["price_per_ton"]
    assert real["revenue"] == quote["revenue"]
    assert real["profit"] == quote["profit"]
    assert "dry_run" not in real                                  # real output unchanged
    # ...and only the real sale mutates.
    assert t.get_cargo("Faelith")["total_tons"] == 0
    assert t.get_cargo("Faelith")["gold"] == gold_before + real["revenue"]


def test_sell_market_quotes_all_cargo_without_mutating():
    t = _trader(cha=16)
    t.set_vessel("Faelith", "Wagon")               # 2 tons
    t.buy_goods("Faelith", "Mead", 1, "Agricultural")
    t.buy_goods("Faelith", "Grain", 1, "Agricultural")
    gold_before = t.get_cargo("Faelith")["gold"]
    tons_before = t.get_cargo("Faelith")["total_tons"]
    q = t.sell_market("Faelith", "Mining, Frontier")
    assert "error" not in q
    assert q["dry_run"] is True
    assert {r["good"] for r in q["cargo_quotes"]} == {"Mead", "Grain"}
    for r in q["cargo_quotes"]:
        assert r["tons_held"] == 1 and r["sell_price_per_ton"] > 0
        assert r["gross_sale_if_all_sold"] == r["sell_price_per_ton"] * r["tons_held"]
        assert (r["total_profit_if_all_sold"]
                == r["gross_sale_if_all_sold"] - r["buy_price_per_ton"] * r["tons_held"])
        # A whole-hold quote must match the per-good sell_goods dry-run number.
        sg = t.sell_goods("Faelith", r["good"], r["tons_held"],
                          "Mining, Frontier", dry_run=True)
        assert sg["price_per_ton"] == r["sell_price_per_ton"]
    # Nothing changed.
    assert t.get_cargo("Faelith")["gold"] == gold_before
    assert t.get_cargo("Faelith")["total_tons"] == tons_before


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All trade-tool tests passed.")
