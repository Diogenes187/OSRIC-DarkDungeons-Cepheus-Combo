"""Checks the magic-item catalog and the roll_magic_item flow."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine.data import magic_items as mi


def test_catalog_loaded():
    assert len(mi.ITEMS) > 200, "run scripts/extract_magic_items.py"
    cats = mi.categories()
    for c in ("potion", "ring", "rod/staff/wand", "sword", "misc", "armour"):
        assert c in cats


def test_noise_filtered():
    names = {i.name.lower() for i in mi.ITEMS}
    assert "acid" not in names and "undead" not in names      # wand-target fragments
    assert not any(n.endswith(" of") for n in names)          # truncated names


def test_known_items_present():
    assert mi.find("Wand of Fire") is not None
    assert mi.find("Frost Brand") is not None
    assert any("Healing" in i.name for i in mi.by_category("potion"))


def test_random_by_category_and_determinism():
    d = Dice(seed=1)
    p = mi.random_item(d, "potion")
    assert p.category == "potion"
    w = mi.random_item(d, "wand")          # alias -> rod/staff/wand
    assert w.category == "rod/staff/wand"
    # determinism
    a = [mi.random_item(Dice(seed=5)).name for _ in range(1)]
    b = [mi.random_item(Dice(seed=5)).name for _ in range(1)]
    assert a == b


def test_roll_magic_item_tool():
    from state.repo import Repo
    from referee.tools import RefereeTools
    repo = Repo.memory()
    cid = repo.create_campaign("X")
    t = RefereeTools(repo, cid)
    out = t.roll_magic_item("ring", count=3)
    assert len(out["items"]) == 3
    assert all(i["category"] == "ring" for i in out["items"])


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All magic-item tests passed.")
