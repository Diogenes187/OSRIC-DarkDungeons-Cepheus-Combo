"""advancement.py -- OSRIC 3.0 level-advancement data (XP and Hit Dice).

Transcribed verbatim from the per-class LEVEL ADVANCEMENT tables in the OSRIC
3.0 Player Guide (Tables 1.3.1.4A through 1.3.10.4A). For each class:

  XP_NEEDED  -- cumulative XP to reach each level (index 0 = level 1 = 0 XP).
  hd_max_level -- the last level at which you roll a Hit Die; beyond it you gain
                  a fixed number of hp per level (hp_after) with NO Con bonus.
  hp_after   -- the fixed hp per level past hd_max_level (from each table's "*"
                footnote).
  max_level  -- a hard ceiling where the book caps the class (None = no cap;
                extrapolate XP upward by the table's final increment).

These are the published numbers; nothing here is invented. Where a class table
stops before 20th, levels beyond the last printed row extend by the final
XP increment (and gain hp_after per level).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# Cumulative XP thresholds, index 0 == level 1.
XP_NEEDED: Dict[str, List[int]] = {
    "Assassin": [0, 1500, 3000, 6000, 12000, 25000, 50000, 100000, 200000,
                 300000, 450000, 600000, 750000, 1000000, 1500000],
    "Cleric": [0, 1500, 3000, 6000, 13000, 27000, 55000, 110000, 220000,
               450000, 675000, 900000, 1125000, 1350000, 1575000, 1800000,
               2050000, 2300000, 2550000, 2700000],
    "Druid": [0, 2000, 4000, 8000, 12000, 20000, 35000, 60000, 90000, 125000,
              200000, 300000, 750000, 1500000],
    "Fighter": [0, 2000, 4000, 8000, 17000, 35000, 70000, 125000, 250000,
                500000, 750000, 1000000, 1250000, 1500000, 1750000, 2000000,
                2250000, 2500000, 2750000, 3000000],
    "Illusionist": [0, 2500, 4750, 9000, 18000, 35000, 60000, 95000, 145000,
                    220000, 440000, 660000, 880000, 1100000, 1320000, 1540000,
                    1760000, 1980000, 2200000, 2420000],
    "Magic-User": [0, 2400, 4800, 10250, 22000, 40000, 60000, 80000, 140000,
                   250000, 375000, 750000, 1125000, 1500000, 1875000, 2250000,
                   2625000, 3000000, 3375000, 3750000],
    "Monk": [0, 2000, 5000, 10000, 21250, 45000, 100000, 200000, 350000,
             500000, 700000, 950000, 1250000, 1750000, 2250000, 2750000,
             3250000],
    "Paladin": [0, 2550, 5500, 12500, 25000, 45000, 95000, 175000, 325000,
                600000, 1000000, 1350000, 1700000, 2050000, 2400000, 2750000,
                3100000, 3450000, 3800000, 4150000],
    "Ranger": [0, 2250, 4500, 9500, 20000, 40000, 90000, 150000, 225000,
               325000, 650000, 975000, 1300000, 1625000, 1950000, 2275000,
               2600000, 2925000, 3250000, 3575000],
    "Thief": [0, 1250, 2500, 5000, 10000, 20000, 40000, 70000, 110000, 160000,
              220000, 440000, 660000, 880000, 1100000, 1320000, 1540000,
              1760000, 1980000, 2200000],
}

# class -> (hd_max_level, hp_after, max_level)
_ADV: Dict[str, Tuple[int, int, Optional[int]]] = {
    "Assassin":   (15, 2, 15),   # ceiling: 1,500,000 XP per the text
    "Cleric":     (9, 2, None),
    "Druid":      (14, 2, 14),   # hierarchic class; capped at 14 in OSRIC
    "Fighter":    (9, 3, None),
    "Illusionist": (10, 1, None),
    "Magic-User": (11, 1, None),  # rolls d4 HD through 11, +1/level after
    "Monk":       (17, 2, 17),
    "Paladin":    (9, 3, None),
    "Ranger":     (10, 2, None),
    "Thief":      (10, 2, None),
}


def hd_max_level(cls: str) -> int:
    return _ADV[cls][0]


def hp_after(cls: str) -> int:
    return _ADV[cls][1]


def max_level(cls: str) -> Optional[int]:
    return _ADV[cls][2]


def xp_for_level(cls: str, level: int) -> int:
    """Cumulative XP needed to BE a given level. Extrapolates past the printed
    table by its final increment."""
    table = XP_NEEDED[cls]
    if level <= 1:
        return 0
    if level <= len(table):
        return table[level - 1]
    step = table[-1] - table[-2]
    return table[-1] + step * (level - len(table))


def level_for_xp(cls: str, xp: int) -> int:
    """The level a character of this class has earned with `xp` experience."""
    cap = max_level(cls)
    table = XP_NEEDED[cls]
    lvl = 1
    for i, need in enumerate(table):
        if xp >= need:
            lvl = i + 1
        else:
            break
    if lvl >= len(table):                       # extrapolate beyond the table
        step = table[-1] - table[-2]
        while xp >= table[-1] + step * (lvl - len(table) + 1):
            lvl += 1
    if cap is not None:
        lvl = min(lvl, cap)
    return lvl
