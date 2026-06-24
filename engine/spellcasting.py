"""spellcasting.py -- Vancian spell memorisation and casting.

A caster memorises spells into their per-level slots (engine.data.spell_slots),
chosen from the spells available to their class (engine.data.spells), then
"spends" a memorised spell to cast it. These are pure functions over a character's
memorised list (stored as memorized_json) so the web/referee layers stay thin.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .data import spells as catalog
from .data import spell_slots as slots_mod


def available_slots(char_class: str, char_level: int,
                    wis: Optional[int] = None) -> List[int]:
    """Slots per spell level for this caster (index 0 == 1st-level spells)."""
    return slots_mod.slots(char_class, char_level, wis)


def slot_usage(char_class: str, memorized: List[str]) -> Dict[int, int]:
    """How many memorised spells occupy each spell level."""
    counts: Dict[int, int] = {}
    for name in memorized:
        sp = catalog.find(name, char_class)
        if sp:
            counts[sp.level] = counts.get(sp.level, 0) + 1
    return counts


def can_memorize(char_class: str, char_level: int, memorized: List[str],
                 spell_name: str, wis: Optional[int] = None) -> bool:
    sp = catalog.find(spell_name, char_class)
    if not sp:
        return False
    avail = available_slots(char_class, char_level, wis)
    if sp.level - 1 >= len(avail):
        return False
    used = slot_usage(char_class, memorized).get(sp.level, 0)
    return used < avail[sp.level - 1]


def memorize(char_class: str, char_level: int, memorized: List[str],
             spell_name: str, wis: Optional[int] = None) -> List[str]:
    """Return a new memorised list with the spell added, or raise ValueError."""
    sp = catalog.find(spell_name, char_class)
    if not sp:
        raise ValueError("{} is not a {} spell".format(spell_name, char_class))
    if not can_memorize(char_class, char_level, memorized, spell_name, wis):
        raise ValueError("no free level-{} slot for {}".format(sp.level, sp.name))
    return list(memorized) + [sp.name]


def cast(memorized: List[str], spell_name: str) -> List[str]:
    """Spend one memorised copy of the spell; return the new list or raise."""
    out = list(memorized)
    for i, name in enumerate(out):
        if name.lower() == spell_name.lower():
            del out[i]
            return out
    raise ValueError("{} is not memorised".format(spell_name))


def remaining_slots(char_class: str, char_level: int, memorized: List[str],
                    wis: Optional[int] = None) -> List[int]:
    """Free slots per spell level after current memorisations."""
    avail = available_slots(char_class, char_level, wis)
    used = slot_usage(char_class, memorized)
    return [avail[i] - used.get(i + 1, 0) for i in range(len(avail))]
