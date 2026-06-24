"""attack.py -- OSRIC 3.0 attack progressions (the class to-hit tables).

Derived from the per-class TO-HIT tables (1.3.x.4D / .4C) in the Player Guide.
Each table's "to hit AC 0" column is that class's THAC0 by level; the columns
step linearly, so we store THAC0 and use the ascending-AC identity:

    to hit:  d20 + attack_bonus + modifiers  >=  ascending AC
    where    attack_bonus = 20 - THAC0
    and      ascending AC  = 20 - descending AC

The four progressions match the four class groups (martial improves every level;
priests and rogues in steps; arcane slowest).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# class -> group
GROUP: Dict[str, str] = {
    "Fighter": "martial", "Paladin": "martial", "Ranger": "martial",
    "Cleric": "priest", "Druid": "priest", "Monk": "priest",
    "Magic-User": "arcane", "Illusionist": "arcane",
    "Thief": "rogue", "Assassin": "rogue",
}

# Step tables as (max_level, THAC0); the last entry's value extrapolates upward.
_STEPS: Dict[str, List[Tuple[int, int]]] = {
    # Cleric/Druid/Monk: 1-3:20, 4-6:18, 7-9:16, 10-12:14, 13-15:12, 16-18:10, 19+:9
    "priest": [(3, 20), (6, 18), (9, 16), (12, 14), (15, 12), (18, 10), (999, 9)],
    # Magic-User/Illusionist: 1-5:20, 6-10:18, 11-15:16, 16-20:14, 21+:12
    "arcane": [(5, 20), (10, 18), (15, 16), (20, 14), (999, 12)],
    # Thief/Assassin: 1-4:20, 5-8:19, 9-12:16, 13-15:14, 16+:12
    "rogue":  [(4, 20), (8, 19), (12, 16), (15, 14), (999, 12)],
}


def thac0(char_class: str, level: int) -> int:
    """THAC0 (the roll needed to hit descending AC 0) for a class at a level."""
    group = GROUP.get(char_class, "priest")
    level = max(1, level)
    if group == "martial":
        # Improves 1 per level: L1 -> 20, L2 -> 19, ... (21 - level).
        return 21 - level
    for max_level, value in _STEPS[group]:
        if level <= max_level:
            return value
    return _STEPS[group][-1][1]


def attack_bonus(char_class: str, level: int) -> int:
    """Ascending-AC attack bonus = 20 - THAC0."""
    return 20 - thac0(char_class, level)
