"""Spot-checks of the OSRIC class tables against the Player Guide (Ch. 3)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.data import classes as C


def test_headers():
    assert C.get("Fighter").hit_die == 10 and C.get("Fighter").gold_dice == "5d4"
    assert C.get("Magic-User").hit_die == 4
    assert C.get("Paladin").minimums["cha"] == 17           # the iconic requirement
    assert C.get("Ranger").first_level_hd == 2              # rangers start with 2 HD
    assert C.get("Monk").gold_mult == 1                     # 5d4, NOT x10
    assert C.get("Druid").minimums["cha"] == 15


def test_minimums():
    fighter_ok = {"str": 9, "dex": 6, "con": 7, "int": 3, "wis": 6, "cha": 6}
    assert C.meets_minimums("Fighter", fighter_ok)
    weak = dict(fighter_ok, str=8)
    assert not C.meets_minimums("Fighter", weak)
    assert C.failed_minimums("Fighter", weak) == ("str",)
    # Paladin needs CHA 17
    pal = {"str": 13, "dex": 10, "con": 10, "int": 10, "wis": 14, "cha": 16}
    assert "cha" in C.failed_minimums("Paladin", pal)


def test_alignment():
    assert C.alignment_allowed("Paladin", "LG")
    assert not C.alignment_allowed("Paladin", "LN")
    assert C.alignment_allowed("Druid", "N")
    assert not C.alignment_allowed("Druid", "LG")
    assert C.alignment_allowed("Assassin", "CE")
    assert not C.alignment_allowed("Assassin", "LG")


def test_xp_bonus():
    assert C.xp_bonus("Fighter", {"str": 16}) is True
    assert C.xp_bonus("Fighter", {"str": 15}) is False
    assert C.xp_bonus("Paladin", {"str": 16, "wis": 16}) is True
    assert C.xp_bonus("Paladin", {"str": 16, "wis": 15}) is False
    assert C.xp_bonus("Ranger", {"str": 16, "int": 16, "wis": 16}) is True
    assert C.xp_bonus("Assassin", {"dex": 18}) is False     # assassin has no bonus


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All class-table tests passed.")
