"""thief_skills.py -- resolve a thief skill check (deterministic, seeded).

The chance is the class base (by the character's thief/assassin level), plus the
Dexterity adjustment, plus the ancestry adjustment, clamped to 1..99 for most
skills (Open Locks can exceed 100 in the book, but the roll still needs a 1-100,
so anything >= 100 simply succeeds). A check succeeds on d100 <= chance.

Assassins use the thief table at their assassin level. Multi-class thieves use
their thief (or assassin) class level.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .data import thieving

THIEF_CLASSES = ("Thief", "Assassin")


def thief_level(classes: List[Dict[str, Any]]) -> Optional[int]:
    """The character's level in a skill-using class (Thief preferred), or None."""
    best = None
    for c in classes or []:
        if c.get("class") in THIEF_CLASSES:
            lvl = int(c.get("level", 1) or 1)
            if best is None or c.get("class") == "Thief":
                best = lvl if best is None else max(best, lvl)
    return best


def chance(skill: str, level: int, dex: int, race: str) -> int:
    """The adjusted percent chance for a skill (not yet clamped to a roll)."""
    s = thieving.canon_skill(skill)
    return (thieving.base_chance(s, level)
            + thieving.dex_adjust(s, dex)
            + thieving.ancestry_adjust(s, race))


def check(dice, skill: str, level: int, dex: int, race: str,
          modifier: int = 0) -> Dict[str, Any]:
    """Roll a thief skill check. `modifier` is a situational +/- the GM applies."""
    s = thieving.canon_skill(skill)
    raw = chance(s, level, dex, race) + int(modifier)
    eff = max(1, min(raw, 100))
    roll = dice.d100()
    return {
        "skill": s, "label": thieving.SKILL_LABELS.get(s, s),
        "level": level, "chance": raw, "effective_chance": eff,
        "roll": roll, "success": roll <= eff,
    }
