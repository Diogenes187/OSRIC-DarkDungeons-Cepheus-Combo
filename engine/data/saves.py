"""saves.py -- OSRIC 3.0 saving-throw tables (per-class SAVING THROW tables).

Transcribed from the Player Guide class sections. Five distinct progressions:
  fighter  (Fighter, Ranger)        paladin  (Paladin -- saves a touch better)
  priest   (Cleric, Druid)          arcane   (Magic-User, Illusionist)
  rogue    (Thief, Assassin, Monk)

Five save categories, in column order:
  aimed_magic | breath | death | petrify | spells
(= aimed magic items, breath weapons, death/paralysis/poison,
   petrifaction/polymorph, spells for unlisted categories)

A save SUCCEEDS on  d20 + modifier >= target.  (Some high-level brackets in the
book run past what's transcribed here; the top bracket carries forward until we
extend them -- fine for low-level play.)
"""
from __future__ import annotations

from typing import Dict, List, Tuple

CATEGORIES = ("aimed_magic", "breath", "death", "petrify", "spells")
_IDX = {c: i for i, c in enumerate(CATEGORIES)}

SAVE_GROUP: Dict[str, str] = {
    "Fighter": "fighter", "Ranger": "fighter",
    "Paladin": "paladin",
    "Cleric": "priest", "Druid": "priest",
    "Magic-User": "arcane", "Illusionist": "arcane",
    "Thief": "rogue", "Assassin": "rogue", "Monk": "rogue",
}

# group -> list of (max_level, [aimed, breath, death, petrify, spells])
_TABLES: Dict[str, List[Tuple[int, List[int]]]] = {
    "fighter": [
        (0,  [18, 20, 16, 17, 19]),
        (2,  [16, 17, 14, 15, 17]),
        (4,  [15, 16, 13, 14, 16]),
        (6,  [13, 13, 11, 12, 14]),
        (8,  [12, 12, 10, 11, 13]),
        (999, [10, 9, 8, 9, 11]),
    ],
    "paladin": [
        (2,  [14, 15, 12, 13, 15]),
        (4,  [13, 14, 11, 12, 14]),
        (6,  [11, 11, 9, 10, 12]),
        (8,  [10, 10, 8, 9, 11]),
        (999, [8, 7, 6, 7, 9]),
    ],
    "priest": [
        (3,  [14, 16, 10, 13, 15]),
        (6,  [13, 15, 9, 12, 14]),
        (9,  [11, 13, 7, 10, 12]),
        (12, [10, 12, 6, 9, 11]),
        (999, [9, 11, 5, 8, 10]),
    ],
    "arcane": [
        (5,  [11, 15, 14, 13, 12]),
        (10, [9, 13, 13, 11, 10]),
        (15, [7, 11, 11, 9, 8]),
        (999, [5, 9, 10, 7, 6]),
    ],
    "rogue": [
        (4,  [14, 16, 13, 12, 15]),
        (8,  [12, 15, 12, 11, 13]),
        (12, [10, 14, 11, 10, 11]),
        (16, [8, 13, 10, 9, 9]),
        (999, [6, 12, 9, 8, 7]),
    ],
}


def save_target(char_class: str, level: int, category: str) -> int:
    """The d20 number a class must meet or beat to save vs a category."""
    if category not in _IDX:
        raise ValueError("unknown save category: {}".format(category))
    group = SAVE_GROUP.get(char_class, "fighter")
    level = max(0, level)
    for max_level, values in _TABLES[group]:
        if level <= max_level:
            return values[_IDX[category]]
    return _TABLES[group][-1][1][_IDX[category]]
