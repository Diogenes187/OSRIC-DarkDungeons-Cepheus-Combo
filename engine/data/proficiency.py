"""proficiency.py -- OSRIC weapon-proficiency slots and the non-proficiency penalty.

Each class starts with a number of weapon proficiencies and gains more at set
levels; using a weapon you're NOT proficient with takes a per-class penalty to
hit (transcribed from the class stat blocks).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# class -> (initial slots, [levels that grant another], non-proficiency penalty)
PROFICIENCY: Dict[str, Tuple[int, List[int], int]] = {
    "Assassin":    (3, [4, 8, 12], -3),
    "Cleric":      (2, [4, 7, 10, 13], -3),
    "Druid":       (2, [4, 7, 10, 13], -4),
    "Fighter":     (4, [3, 5, 7, 9, 11, 13, 15, 17, 19], -2),
    "Illusionist": (1, [6, 11, 16], -5),
    "Magic-User":  (1, [6, 11, 16], -5),
    "Monk":        (1, [3, 5, 7, 9, 11, 13], -3),
    "Paladin":     (3, [5, 8, 11, 14, 17], -2),
    "Ranger":      (3, [5, 8, 11, 14, 17], -2),
    "Thief":       (2, [6, 10, 14, 18], -3),
}


def slots(char_class: str, level: int) -> int:
    data = PROFICIENCY.get(char_class)
    if not data:
        return 1
    initial, gains, _ = data
    return initial + sum(1 for g in gains if level >= g)


def penalty(char_class: str) -> int:
    data = PROFICIENCY.get(char_class)
    return data[2] if data else -3


def best_penalty(classes) -> int:
    """The least-bad non-proficiency penalty across a character's classes (a
    fighter/mage swings a strange weapon at the fighter's -2, not the mage's -5)."""
    pens = [penalty(c.get("class")) for c in classes or []
            if c.get("class") in PROFICIENCY]
    return max(pens) if pens else -3            # max = closest to zero
