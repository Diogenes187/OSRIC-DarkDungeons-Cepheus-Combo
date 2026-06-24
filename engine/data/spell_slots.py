"""spell_slots.py -- OSRIC 3.0 spell-slot progressions (caster advancement tables).

Transcribed from the LEVEL ADVANCEMENT tables (1.3.x.4A) in the Player Guide.
Each grid maps character level -> [slots for spell level 1, 2, 3, ...]. Clerics
gain bonus slots for high Wisdom (the cleric Bonus Spell Slots table).

Paladins and Rangers gain a little spellcasting at high level; that's deferred
(they cast nothing at the low levels Tier 1 cares about).
"""
from __future__ import annotations

from typing import Dict, List, Optional

# Cleric: spell levels 1-7, character levels 1-20.
CLERIC: Dict[int, List[int]] = {
    1: [1, 0, 0, 0, 0, 0, 0], 2: [2, 0, 0, 0, 0, 0, 0], 3: [2, 1, 0, 0, 0, 0, 0],
    4: [3, 2, 0, 0, 0, 0, 0], 5: [3, 3, 1, 0, 0, 0, 0], 6: [3, 3, 2, 0, 0, 0, 0],
    7: [3, 3, 2, 1, 0, 0, 0], 8: [3, 3, 3, 2, 0, 0, 0], 9: [4, 4, 3, 2, 1, 0, 0],
    10: [4, 4, 3, 3, 2, 0, 0], 11: [5, 4, 4, 3, 2, 1, 0], 12: [6, 5, 5, 3, 2, 2, 0],
    13: [6, 6, 6, 4, 2, 2, 0], 14: [6, 6, 6, 5, 3, 2, 0], 15: [7, 7, 7, 5, 4, 2, 0],
    16: [7, 7, 7, 6, 5, 3, 1], 17: [8, 8, 8, 6, 5, 3, 1], 18: [8, 8, 8, 7, 6, 4, 1],
    19: [9, 9, 9, 7, 6, 4, 2], 20: [9, 9, 9, 8, 7, 5, 2],
}

# Druid: spell levels 1-7, character levels 1-14.
DRUID: Dict[int, List[int]] = {
    1: [2, 0, 0, 0, 0, 0, 0], 2: [2, 1, 0, 0, 0, 0, 0], 3: [3, 2, 1, 0, 0, 0, 0],
    4: [4, 2, 2, 0, 0, 0, 0], 5: [4, 3, 2, 0, 0, 0, 0], 6: [4, 3, 2, 1, 0, 0, 0],
    7: [4, 4, 3, 1, 0, 0, 0], 8: [4, 4, 3, 2, 0, 0, 0], 9: [5, 4, 3, 2, 1, 0, 0],
    10: [5, 4, 3, 3, 2, 0, 0], 11: [5, 5, 3, 3, 2, 1, 0], 12: [5, 5, 4, 4, 3, 2, 1],
    13: [6, 5, 5, 5, 4, 3, 2], 14: [6, 6, 6, 6, 5, 4, 3],
}

# Magic-User: spell levels 1-9, character levels 1-20.
MAGIC_USER: Dict[int, List[int]] = {
    1: [1, 0, 0, 0, 0, 0, 0, 0, 0], 2: [2, 0, 0, 0, 0, 0, 0, 0, 0],
    3: [2, 1, 0, 0, 0, 0, 0, 0, 0], 4: [3, 2, 0, 0, 0, 0, 0, 0, 0],
    5: [4, 2, 1, 0, 0, 0, 0, 0, 0], 6: [4, 3, 2, 0, 0, 0, 0, 0, 0],
    7: [4, 3, 2, 1, 0, 0, 0, 0, 0], 8: [4, 3, 3, 2, 0, 0, 0, 0, 0],
    9: [4, 4, 3, 2, 1, 0, 0, 0, 0], 10: [4, 4, 3, 2, 2, 0, 0, 0, 0],
    11: [4, 4, 4, 3, 3, 0, 0, 0, 0], 12: [5, 4, 4, 3, 3, 1, 0, 0, 0],
    13: [5, 5, 4, 3, 3, 2, 0, 0, 0], 14: [5, 5, 5, 4, 4, 2, 1, 0, 0],
    15: [5, 5, 5, 4, 4, 3, 2, 0, 0], 16: [5, 5, 5, 4, 4, 3, 2, 1, 0],
    17: [5, 5, 5, 5, 5, 4, 3, 2, 0], 18: [5, 5, 5, 5, 5, 4, 3, 2, 1],
    19: [5, 5, 5, 5, 5, 5, 4, 3, 1], 20: [5, 5, 5, 5, 5, 5, 4, 3, 2],
}

# Illusionist: spell levels 1-7, character levels 1-20.
ILLUSIONIST: Dict[int, List[int]] = {
    1: [1, 0, 0, 0, 0, 0, 0], 2: [2, 0, 0, 0, 0, 0, 0], 3: [2, 1, 0, 0, 0, 0, 0],
    4: [3, 2, 0, 0, 0, 0, 0], 5: [4, 3, 1, 0, 0, 0, 0], 6: [4, 3, 2, 0, 0, 0, 0],
    7: [4, 3, 2, 1, 0, 0, 0], 8: [4, 3, 2, 2, 0, 0, 0], 9: [5, 3, 3, 2, 0, 0, 0],
    10: [5, 4, 3, 2, 1, 0, 0], 11: [5, 4, 3, 3, 2, 0, 0], 12: [5, 5, 4, 3, 2, 1, 0],
    13: [5, 5, 4, 3, 2, 2, 0], 14: [5, 5, 4, 3, 2, 2, 1], 15: [5, 5, 4, 4, 2, 2, 2],
    16: [5, 5, 5, 4, 3, 2, 2], 17: [6, 5, 5, 4, 3, 3, 2], 18: [6, 6, 5, 4, 4, 3, 2],
    19: [6, 6, 5, 5, 5, 3, 2], 20: [6, 6, 6, 5, 5, 4, 2],
}

_GRIDS = {"Cleric": CLERIC, "Druid": DRUID,
          "Magic-User": MAGIC_USER, "Illusionist": ILLUSIONIST}

CASTERS = tuple(_GRIDS.keys())


def _cleric_wisdom_bonus(wis: int) -> Dict[int, int]:
    """Bonus cleric spell slots by spell level for a Wisdom score (cumulative)."""
    return {
        1: (1 if wis >= 13 else 0) + (1 if wis >= 14 else 0),
        2: (1 if wis >= 15 else 0) + (1 if wis >= 16 else 0),
        3: (1 if wis >= 17 else 0),
        4: (1 if wis >= 18 else 0),
    }


def slots(char_class: str, char_level: int, wis: Optional[int] = None) -> List[int]:
    """Spells memorisable per spell level for a caster. Empty list for non-casters.

    For clerics, pass `wis` to fold in the high-Wisdom bonus slots (granted only
    for spell levels the cleric can already cast)."""
    grid = _GRIDS.get(char_class)
    if not grid:
        return []
    lvl = max(1, min(char_level, max(grid)))
    base = list(grid[lvl])
    if char_class == "Cleric" and wis:
        bonus = _cleric_wisdom_bonus(wis)
        for spell_level, extra in bonus.items():
            idx = spell_level - 1
            if extra and idx < len(base) and base[idx] > 0:   # only if castable
                base[idx] += extra
    return base


def is_caster(char_class: str) -> bool:
    return char_class in _GRIDS
