"""Tests for the dominion economy (Dark Dungeons strongholds & dominions)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine import domain as dom


def test_found_fief():
    d = Dice(seed=1)
    f = dom.found_fief(d, "hills", "wilderness")
    assert 10 <= f.families <= 100        # 1d10 x10
    assert 1 <= len(f.resources) <= 4
    assert all(r in ("animal", "vegetable", "mineral") for r in f.resources)
    assert f.max_families == 1500


def test_resource_income_by_type():
    # 300 families, one mineral resource -> 300 * 3 = 900 gp.
    f = dom.Fief("hills", "borderlands", 300, ["mineral"])
    assert f.resource_income() == 900
    # split evenly across mineral(3) + vegetable(1): 150*3 + 150*1 = 600.
    f2 = dom.Fief("hills", "borderlands", 300, ["mineral", "vegetable"])
    assert f2.resource_income() == 600
    assert f.service_income() == 3000 and f.poll_tax(1.0) == 300


def test_monthly_turn_balances():
    d = Dice(seed=2)
    f = dom.Fief("hills", "borderlands", 447, ["mineral", "mineral", "vegetable"])
    dn = dom.Dominion("Gretchenhold", [f], has_liege=True,
                      troops=[dom.Troop("Dwarven Infantry", 300, 5)])
    rep = d and dom.monthly_turn(d, dn, festivals=1)
    # Income lines present and gross cash = resources + poll tax.
    assert rep["income"]["gross_cash"] == rep["income"]["resources"] + rep["income"]["poll_tax"]
    # Tithe is 10% of gross (cash + service).
    gross_total = rep["income"]["gross_cash"] + rep["income"]["service"]
    assert rep["expenses"]["tithe"] == round(0.10 * gross_total)
    assert rep["expenses"]["salt_tax"] == round(0.20 * gross_total)
    # XP equals gross cash income.
    assert rep["xp"] == rep["income"]["gross_cash"]
    # Population grew this month.
    assert rep["population_after"] >= rep["families"] - 10


def test_population_growth_scales_with_size():
    d = Dice(seed=3)
    small = dom.Fief("plains", "civilized", 80, ["vegetable"])
    big = dom.Fief("plains", "civilized", 5000, ["vegetable"])
    dom._grow(d, small); dom._grow(d, big)
    # Small fiefs grow fast (~25%), big ones crawl (~1%) and are capped.
    assert small.families >= 90
    assert big.families <= big.max_families


def test_tax_changes_confidence():
    dn = dom.Dominion("Test", [dom.Fief("hills", "wilderness", 100, ["animal"])],
                      confidence=50, tax_rate_gp=1.0)
    assert dom.set_tax_rate(dn, 2.0) == -25 and dn.confidence == 25    # raising
    assert dom.set_tax_rate(dn, 1.0) == 10 and dn.confidence == 35     # lowering


def test_stronghold_cost_time_engineers():
    # A keep + 4 castle walls + a gatehouse, in a remote (normal) region.
    spec = {"Keep, Square": 1, "Wall, Castle": 4, "Gatehouse": 1}
    b = dom.build_stronghold(spec)
    assert b["total_cost"] == 75000 + 4 * 5000 + 6500    # 101,500 gp
    assert b["build_days"] == -(-b["total_cost"] // 500)  # 1 day / 500 gp
    assert b["engineers"] == 2                            # 1 per 100,000 gp
    # Inaccessible doubles, heavily settled halves.
    assert dom.build_stronghold(spec, "inaccessible")["total_cost"] == 2 * 101500
    assert dom.build_stronghold(spec, "settled")["total_cost"] == 101500 // 2
    # Unknown elements are reported, not silently dropped.
    assert dom.build_stronghold({"Moon Base": 1})["unknown"] == ["Moon Base"]


def test_titles_ladder():
    assert [t.name for t in dom.TITLES][:3] == ["Knight", "Baron", "Viscount"]
    assert dom.title("Duke").entertain_cost_day == 600
    assert dom.title("Baron").dominions.startswith("1 dominion")
    assert dom.title("nonsense").name == "Knight"        # default floor


def test_extra_expenses_in_turn():
    dn = dom.Dominion("Test", [dom.Fief("hills", "civilized", 1000, ["mineral"])])
    # Entertaining a duke for 3 days = 1,800 gp of extra expense.
    rep = dom.monthly_turn(Dice(seed=1), dn,
                           extra_expenses=dom.title("Duke").entertain_cost_day * 3)
    assert rep["expenses"]["other"] == 1800
    assert rep["expenses"]["total"] >= 1800


def test_determinism():
    def run():
        d = Dice(seed=9)
        dn = dom.Dominion("X", [dom.found_fief(d, "forest", "borderlands")])
        return dom.monthly_turn(d, dn)
    assert run() == run()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All domain tests passed.")
