"""Tests for the caravan/shipping trade engine (and the Charisma haggle)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import trade


def test_charisma_helps_haggling():
    assert trade.haggle_dm(18) > trade.haggle_dm(10) > trade.haggle_dm(4)
    # Over many deals, an 18-CHA trader pays less to buy than a 4-CHA trader.
    def avg_purchase(cha):
        tot = 0
        for s in range(300):
            tot += trade.purchase_price(Dice(seed=s), "Iron",
                                        ["Frontier"], cha).price_per_ton
        return tot / 300
    assert avg_purchase(18) < avg_purchase(4)


def test_arbitrage_buy_low_sell_high():
    # Grain is abundant in Agricultural land, demanded on the Frontier.
    def avg(fn, econ):
        tot = 0
        for s in range(300):
            tot += fn(Dice(seed=s), "Grain", econ, 12).price_per_ton
        return tot / 300
    buy_at_farm = avg(trade.purchase_price, ["Agricultural"])
    sell_at_frontier = avg(trade.sale_price, ["Frontier"])
    # The whole point: you can sell on the frontier for more than you paid at the farm.
    assert sell_at_frontier > buy_at_farm


def test_quote_shape_and_determinism():
    q1 = trade.purchase_price(Dice(seed=5), "Mead", ["Agricultural"], 13)
    q2 = trade.purchase_price(Dice(seed=5), "Mead", ["Agricultural"], 13)
    assert q1 == q2 and q1.good == "Mead" and q1.price_per_ton > 0
    assert trade.purchase_price(Dice(seed=1), "Unobtanium", ["Rich"]) is None


def test_available_goods_features_local_produce():
    d = Dice(seed=3)
    market = trade.available_goods(d, ["Mining"])
    names = {m["good"] for m in market}
    # A mining town's market should usually offer iron and/or gems.
    assert names & {"Iron", "Gems", "Salt"}
    assert all(m["tons_available"] >= 1 for m in market)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All trade-engine tests passed.")
