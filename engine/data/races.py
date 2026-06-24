"""races.py -- OSRIC 3.0 ancestry ("race") data (Chapter Two).

Transcribed from OSRIC 3.0 Player Guide, sections 1.2.0-1.2.7 (Table 1.2.0A for
required ability ranges, plus each ancestry's adjustments, allowed classes,
multi-class combos, and level limits).

Ability keys: str, dex, con, int, wis, cha.

Level limits: a value is an int (cap), None (unlimited), or a callable taking a
scores dict and returning the cap (used where the cap depends on an ability).
Use ``max_level(race, cls, scores)`` to resolve.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Union

ABILITIES = ("str", "dex", "con", "int", "wis", "cha")
LevelLimit = Union[int, None, Callable[[Dict[str, int]], int]]


@dataclass
class Race:
    name: str
    adjustments: Dict[str, int] = field(default_factory=dict)   # applied at creation
    requirements: Dict[str, tuple] = field(default_factory=dict)  # ability -> (min, max)
    allowed_classes: tuple = ()                                  # single-class options
    multiclass: tuple = ()                                       # tuples of class names
    can_dual_class: bool = False
    level_limits: Dict[str, LevelLimit] = field(default_factory=dict)  # missing = unlimited
    size: str = "Medium"
    movement: int = 120
    infravision: int = 0
    languages: tuple = ()


# Conditional level-limit helpers (resolve against a scores dict) ------------
def _by_str(high18: int, at17: int, low: int) -> Callable[[Dict[str, int]], int]:
    def f(s):
        st = s.get("str", 0)
        return high18 if st >= 18 else (at17 if st == 17 else low)
    return f


def _by_int(high18: int, at17: int, low: int) -> Callable[[Dict[str, int]], int]:
    def f(s):
        i = s.get("int", 0)
        return high18 if i >= 18 else (at17 if i == 17 else low)
    return f


_ALL_3_18 = {a: (3, 18) for a in ABILITIES}


RACES: Dict[str, Race] = {
    "Human": Race(
        name="Human",
        adjustments={},
        requirements=dict(_ALL_3_18),
        allowed_classes=("Assassin", "Cleric", "Druid", "Fighter", "Illusionist",
                         "Magic-User", "Monk", "Paladin", "Ranger", "Thief"),
        multiclass=(),
        can_dual_class=True,
        # Only these are capped (no one advances past them); all else unlimited.
        level_limits={"Assassin": 15, "Druid": 14, "Monk": 17},
        size="Medium", movement=120, infravision=0,
        languages=("Common",),
    ),
    "Dwarf": Race(
        name="Dwarf",
        adjustments={"con": 1, "cha": -1},
        requirements={"str": (8, 18), "dex": (3, 17), "con": (12, 19),
                      "int": (3, 18), "wis": (3, 18), "cha": (3, 16)},
        allowed_classes=("Assassin", "Cleric", "Fighter", "Thief"),
        multiclass=(("Fighter", "Thief"),),
        level_limits={"Assassin": 9, "Cleric": 8,
                      "Fighter": _by_str(9, 8, 7), "Thief": None},
        size="Small", movement=90, infravision=60,
        languages=("Common", "Dwarfish", "Gnomish", "Goblin", "Kobold", "Orcish"),
    ),
    "Elf": Race(
        name="Elf",
        adjustments={"dex": 1, "con": -1},
        requirements={"str": (3, 18), "dex": (7, 19), "con": (6, 18),
                      "int": (8, 18), "wis": (3, 18), "cha": (8, 18)},
        allowed_classes=("Assassin", "Cleric", "Fighter", "Magic-User", "Thief"),
        multiclass=(("Fighter", "Magic-User"), ("Fighter", "Thief"),
                    ("Magic-User", "Thief"), ("Fighter", "Magic-User", "Thief")),
        level_limits={"Assassin": 10, "Cleric": 7,
                      "Fighter": _by_str(7, 6, 5), "Magic-User": _by_int(11, 10, 9),
                      "Thief": None},
        size="Medium", movement=120, infravision=60,
        languages=("Common", "Elven", "Gnoll", "Gnomish", "Goblin", "Halfling",
                   "Hobgoblin", "Orcish"),
    ),
    "Gnome": Race(
        name="Gnome",
        adjustments={},
        requirements={"str": (6, 18), "dex": (3, 18), "con": (8, 18),
                      "int": (7, 18), "wis": (3, 18), "cha": (3, 18)},
        allowed_classes=("Assassin", "Cleric", "Fighter", "Illusionist", "Thief"),
        multiclass=(("Fighter", "Illusionist"), ("Fighter", "Thief"),
                    ("Illusionist", "Thief")),
        level_limits={"Assassin": 8, "Cleric": 7,
                      "Fighter": (lambda s: 6 if s.get("str", 0) >= 18 else 5),
                      "Illusionist": (lambda s: 7 if (s.get("int", 0) + s.get("dex", 0)) >= 35
                                      else (6 if s.get("int", 0) >= 17 and s.get("dex", 0) >= 17 else 5)),
                      "Thief": None},
        size="Small", movement=90, infravision=60,
        languages=("Common", "Dwarfish", "Gnomish", "Goblin", "Halfling", "Kobold"),
    ),
    "Half-Elf": Race(
        name="Half-Elf",
        adjustments={},
        requirements={"str": (3, 18), "dex": (6, 18), "con": (6, 18),
                      "int": (4, 18), "wis": (3, 18), "cha": (3, 18)},
        allowed_classes=("Assassin", "Cleric", "Druid", "Fighter", "Magic-User",
                         "Ranger", "Thief"),
        multiclass=(("Cleric", "Fighter"), ("Cleric", "Ranger"), ("Cleric", "Magic-User"),
                    ("Fighter", "Magic-User"), ("Fighter", "Thief"),
                    ("Cleric", "Fighter", "Magic-User"), ("Fighter", "Magic-User", "Thief")),
        level_limits={"Assassin": 11, "Cleric": 5, "Druid": 14,
                      "Fighter": _by_str(8, 7, 6), "Magic-User": _by_int(8, 7, 6),
                      "Ranger": _by_str(8, 7, 6), "Thief": None},
        size="Medium", movement=120, infravision=60,
        languages=("Common", "Elven", "Gnoll", "Gnomish", "Goblin", "Halfling",
                   "Hobgoblin", "Orcish"),
    ),
    "Halfling": Race(
        name="Halfling",
        adjustments={"dex": 1, "str": -1},
        requirements={"str": (6, 17), "dex": (8, 18), "con": (10, 19),
                      "int": (6, 18), "wis": (3, 17), "cha": (3, 18)},
        allowed_classes=("Fighter", "Druid", "Thief"),
        multiclass=(("Fighter", "Thief"),),
        level_limits={"Druid": 6, "Fighter": 4, "Thief": None},
        size="Small", movement=90, infravision=60,
        languages=("Common", "Dwarfish", "Gnomish", "Goblin", "Halfling", "Orcish"),
    ),
    "Half-Orc": Race(
        name="Half-Orc",
        adjustments={"str": 1, "con": 1, "cha": -2},
        requirements={"str": (6, 18), "dex": (3, 17), "con": (13, 19),
                      "int": (3, 17), "wis": (3, 14), "cha": (3, 12)},
        allowed_classes=("Assassin", "Cleric", "Fighter", "Thief"),
        multiclass=(("Cleric", "Fighter"), ("Cleric", "Thief"), ("Cleric", "Assassin"),
                    ("Fighter", "Thief"), ("Fighter", "Assassin")),
        level_limits={"Assassin": 15, "Cleric": 4, "Fighter": 10,
                      "Thief": (lambda s: 7 if s.get("dex", 0) >= 17 else 6)},
        size="Medium", movement=120, infravision=60,
        languages=("Common", "Orcish"),
    ),
}


def get(race: str) -> Race:
    return RACES[race]


def max_level(race: str, cls: str, scores: Dict[str, int]) -> Optional[int]:
    """Resolve a race+class level cap. None means unlimited."""
    r = RACES[race]
    if cls not in r.level_limits:
        return None
    lim = r.level_limits[cls]
    if callable(lim):
        return lim(scores)
    return lim


def eligible_classes(race: str) -> tuple:
    return RACES[race].allowed_classes
