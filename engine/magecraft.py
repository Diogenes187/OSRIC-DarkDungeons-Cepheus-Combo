"""magecraft.py -- the high-level magic economy (deterministic, seeded).

Learning spells into a spellbook, researching brand-new spells, scribing scrolls,
and brewing potions -- the OSRIC rules for what spellcasters do between
adventures, with real costs in gold and time.

  Arcane Spell Acquisition (Table 1.3.6.2A): chance to understand a spell by Int.
  Copying a spell: 100 gp and 1 hour per spell level.
  Spell Research (2.14.2): base 10% (+10% per 2000 gp/level, max +40%) + ability +
    caster level - 2x spell level; 1 week/level + 1 week; 200 gp/level + 1d4x100/wk.
  Eldritch/Divine/Druidic/Phantasmal Craft (level 7): scribe scrolls (50 gp & 1
    day/level, 20% failure -- 40% if overworked) and brew potions (half value,
    1 day per 50 gp).
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional

ARCANE_CLASSES = ("Magic-User", "Illusionist")
DIVINE_CLASSES = ("Cleric", "Druid")
CRAFT_LEVEL = 7

# Intelligence -> (chance to understand, max spells understood per level).
_ACQUIRE = [(10, 35, 6), (12, 45, 7), (14, 55, 9), (16, 65, 11),
            (17, 75, 14), (18, 85, 18), (19, 90, 22)]


def understand_chance(int_score: int) -> Dict[str, int]:
    i = int(int_score or 0)
    if i < 9:
        return {"chance": 0, "max_per_level": 0}
    for hi, chance, mx in _ACQUIRE:
        if i <= hi:
            return {"chance": chance, "max_per_level": mx}
    return {"chance": 90, "max_per_level": 22}


def learn_spell(dice, int_score: int, spell_level: int,
                divine: bool = False) -> Dict[str, Any]:
    """Try to learn a spell into a spellbook. Divine casters understand
    automatically; arcane casters roll vs their Intelligence chance. Copying
    costs 100 gp and one hour per spell level."""
    cost = 100 * int(spell_level)
    hours = int(spell_level)
    if divine:
        return {"understood": True, "roll": None, "chance": 100,
                "cost_gp": cost, "hours": hours}
    ch = understand_chance(int_score)["chance"]
    roll = dice.d100()
    return {"understood": roll <= ch, "roll": roll, "chance": ch,
            "cost_gp": cost, "hours": hours}


def research_spell(dice, ability_score: int, caster_level: int, spell_level: int,
                   increments: int = 0, has_facility: bool = True) -> Dict[str, Any]:
    """Research a brand-new spell. increments (0-4) each cost 2000 gp/level and
    add 10% to the base chance."""
    inc = max(0, min(int(increments), 4))
    base = 10 + 10 * inc
    chance = base + int(ability_score) + int(caster_level) - 2 * int(spell_level)
    eff = max(1, min(chance, 99))
    weeks = int(spell_level) + 1
    facility_cost = (200 if has_facility else 2000) * int(spell_level)
    weekly = sum(dice.d4() * 100 for _ in range(weeks))
    cost = facility_cost + inc * 2000 * int(spell_level) + weekly
    roll = dice.d100()
    return {"base_chance": base, "chance": chance, "effective_chance": eff,
            "roll": roll, "success": roll <= eff, "weeks": weeks,
            "cost_gp": cost, "increments": inc}


def scribe_scroll(dice, spell_level: int, overworked: bool = False) -> Dict[str, Any]:
    """Scribe a spell onto a scroll: 50 gp and 1 day per level, 20% failure
    (40% if the scribe has overworked this year)."""
    cost = 50 * int(spell_level)
    days = int(spell_level)
    fail_on = 40 if overworked else 20
    roll = dice.d100()
    return {"cost_gp": cost, "days": days, "failure_chance": fail_on,
            "roll": roll, "success": roll > fail_on}


def brew_potion(dice, potion_value_gp: int) -> Dict[str, Any]:
    """Brew a potion: costs half its market value, one day per 50 gp of cost.
    (Needs a lab and an alchemist -- ongoing expenses the GM tracks.)"""
    cost = int(potion_value_gp) // 2
    days = max(1, math.ceil(cost / 50))
    return {"cost_gp": cost, "days": days,
            "note": "Requires a laboratory and an alchemist."}
