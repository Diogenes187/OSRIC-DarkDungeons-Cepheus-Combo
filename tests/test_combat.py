"""Tests for the attack progressions and combat resolution."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.dice import Dice
from engine.data import attack as atk
from engine import combat


def test_thac0_progressions():
    # Martial improves 1/level (to-hit AC0 column of the Fighter table).
    assert atk.thac0("Fighter", 1) == 20
    assert atk.thac0("Fighter", 11) == 10
    assert atk.thac0("Fighter", 14) == 7
    assert atk.attack_bonus("Fighter", 1) == 0
    assert atk.attack_bonus("Fighter", 11) == 10
    # Priests (Cleric/Druid/Monk) step by ranges.
    assert atk.thac0("Cleric", 1) == 20 and atk.thac0("Cleric", 4) == 18
    assert atk.thac0("Cleric", 16) == 10 and atk.thac0("Cleric", 19) == 9
    assert atk.thac0("Monk", 1) == 20
    # Arcane slowest.
    assert atk.thac0("Magic-User", 1) == 20 and atk.thac0("Magic-User", 6) == 18
    assert atk.thac0("Magic-User", 16) == 14
    # Rogues.
    assert atk.thac0("Thief", 1) == 20 and atk.thac0("Thief", 5) == 19
    assert atk.thac0("Thief", 9) == 16 and atk.thac0("Thief", 13) == 14


def test_ac_conversion():
    assert combat.asc_from_desc(10) == 10
    assert combat.asc_from_desc(0) == 20
    assert combat.asc_from_desc(2) == 18
    assert combat.desc_from_asc(combat.asc_from_desc(5)) == 5


def _mk(name, **kw):
    base = dict(hp=8, hp_max=8, ac_descending=10)
    base.update(kw)
    return combat.Combatant(name=name, **base)


def test_attack_hits_and_misses_by_bonus():
    d = Dice(seed=1)
    a = _mk("Sure", attack_bonus=100)
    b = _mk("Foe", ac_descending=2, hp=9999, hp_max=9999)
    nat1 = 0
    for _ in range(400):
        r = combat.resolve_attack(a, b, d)
        if r["natural"] == 1:
            nat1 += 1
            assert not r["hit"]          # natural 1 always misses
        else:
            assert r["hit"]              # huge bonus hits otherwise
    assert nat1 > 0

    d = Dice(seed=2)
    a = _mk("Weak", attack_bonus=-100)
    b = _mk("Foe", ac_descending=-5, hp=9999, hp_max=9999)
    for _ in range(400):
        r = combat.resolve_attack(a, b, d)
        assert r["hit"] == (r["natural"] == 20)   # only a natural 20 connects


def test_damage_and_death():
    d = Dice(seed=3)
    a = _mk("Hero", attack_bonus=100, damage_dice="1d6", damage_mod=2)
    b = _mk("Goblin", hp=4, hp_max=4)
    downed = False
    for _ in range(10):
        r = combat.resolve_attack(a, b, d)
        if r["hit"]:
            assert r["damage"] >= 1
        if r["defender_down"]:
            downed = True
            assert not b.alive and b.hp <= 0
            break
    assert downed


def test_determinism():
    def run():
        d = Dice(seed=77)
        a = _mk("A", attack_bonus=3, damage_dice="1d8")
        b = _mk("B", ac_descending=6, hp=50, hp_max=50)
        return [combat.resolve_attack(a, b, d) for _ in range(30)]
    assert run() == run()


def test_combatant_from_row():
    row = {
        "name": "Faelith", "classes_json": '[{"class":"Fighter","level":3,"xp":0}]',
        "str_score": 17, "str_pct": 0, "hp_current": 22, "hp_max": 24,
        "ac_descending": 4, "is_npc": 0,
    }
    c = combat.combatant_from_row(row)
    assert c.name == "Faelith" and c.hp == 22 and c.ac_descending == 4
    assert c.attack_bonus == atk.attack_bonus("Fighter", 3)
    assert c.to_hit_mod == 1 and c.damage_mod == 1     # STR 17
    assert c.ac_ascending == 16


def test_morale():
    d = Dice(seed=9)
    results = [combat.morale_check(d, 8)["holds"] for _ in range(200)]
    assert any(results) and not all(results)           # sometimes holds, sometimes breaks


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All combat tests passed.")
