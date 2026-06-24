"""Tier 1 foundation tests: seeded dice + state round-trip.

Run from the project root (greyhawk/):  python -m pytest tests/  -- or just
``python tests/test_foundations.py`` for a plain-stdlib smoke run.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from state.repo import Repo


def test_dice_is_deterministic():
    a = Dice(seed=12345)
    b = Dice(seed=12345)
    seq_a = [a.d20() for _ in range(50)] + [a.roll(3, 6) for _ in range(20)]
    seq_b = [b.d20() for _ in range(50)] + [b.roll(3, 6) for _ in range(20)]
    assert seq_a == seq_b
    # A different seed should (essentially always) diverge.
    c = Dice(seed=999)
    assert [c.d20() for _ in range(50)] != seq_a[:50]


def test_dice_ranges_and_notation():
    d = Dice(seed=7)
    for _ in range(500):
        assert 1 <= d.d20() <= 20
        assert 1 <= d.d100() <= 100
    r = d.notation("3d6+2")
    assert len(r.dice) == 3 and r.modifier == 2
    assert 5 <= r.total <= 20


def test_ability_methods():
    d = Dice(seed=42)
    for _ in range(1000):
        r4 = d.ability_4d6_drop_lowest()
        assert len(r4.dice) == 3 and len(r4.dropped) == 1
        assert 3 <= r4.natural <= 18
        # the dropped die is never larger than any kept die
        assert all(r4.dropped[0] <= k for k in r4.dice)
        r5 = d.ability_5d6_drop_two()
        assert len(r5.dice) == 3 and len(r5.dropped) == 2
        assert 3 <= r5.natural <= 18
    # hero mode skews higher on average than 4d6
    h = Dice(seed=1); s = Dice(seed=1)
    avg5 = sum(h.ability_5d6_drop_two().natural for _ in range(5000)) / 5000
    avg4 = sum(s.ability_4d6_drop_lowest().natural for _ in range(5000)) / 5000
    assert avg5 > avg4


def test_repo_round_trip():
    repo = Repo.memory()
    cid = repo.create_campaign("The Greyhawk Wars", current_date="Reaping 1, 576 CY",
                               allow_race_overrides=True)
    camp = repo.get_campaign(cid)
    assert camp["name"] == "The Greyhawk Wars"
    assert camp["allow_race_overrides"] == 1
    assert camp["setting"] == "World of Greyhawk"

    chid = repo.save_character(cid, {
        "name": "Faelith", "player": "Ray", "race": "Human",
        "classes": [{"class": "Fighter", "level": 3, "xp": 9000}],
        "alignment": "CG",
        "str": 17, "str_pct": 0, "dex": 14, "con": 15,
        "int": 10, "wis": 12, "cha": 13,
        "hp_max": 24, "ac_descending": 4, "ac_ascending": 15,
        "gold": 150, "gear": ["longsword", "chain mail", "wagon of mead"],
    })
    ch = repo.get_character(chid)
    assert ch["name"] == "Faelith"
    assert ch["str_score"] == 17 and ch["hp_current"] == 24   # defaulted to hp_max
    assert "mead" in ch["gear_json"]

    repo.record_event(cid, "trade", "Sold mead in Safeton at a tidy markup.",
                      detail={"profit": 40}, in_game_date="Reaping 9, 576 CY")
    evs = repo.recent_events(cid)
    assert len(evs) == 1 and evs[0]["kind"] == "trade"

    assert len(repo.list_characters(cid)) == 1
    assert repo.delete_character(chid) is True
    assert len(repo.list_characters(cid)) == 0
    repo.close()


if __name__ == "__main__":
    test_dice_is_deterministic()
    test_dice_ranges_and_notation()
    test_ability_methods()
    test_repo_round_trip()
    print("All Tier 1 foundation tests passed.")
