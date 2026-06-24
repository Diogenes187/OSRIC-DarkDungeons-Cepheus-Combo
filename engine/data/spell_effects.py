"""spell_effects.py -- the mechanical guts of spells that change hit points.

The engine owns spell numbers, not the AI. Every spell here carries its exact
OSRIC dice, save type, and scaling, transcribed from the spellbooks. cast_spell
rolls them, applies saving throws, and changes target HP. Spells WITHOUT hard
numbers (charm, knock, fly, light...) aren't listed; for those cast_spell hands
the AI the authoritative rules text to narrate, but there's no number to invent.

Spec keys:
  level, classes, kind ('damage'|'heal'|'sleep'|'incapacitate')
  dice              fixed roll, e.g. '2d8+1'
  dice_per_level    roll this once per caster level (e.g. fireball '1d6')
  per_level_flat    flat points per caster level (burning hands = 1)
  per_level_plus    add this x level to a fixed dice roll (shocking grasp = 1)
  missiles          magic-missile style: (level+1)//2 darts of 'dice' each
  save              'none' | 'half' | 'negate'
  save_cat          which saving-throw column applies
"""
from __future__ import annotations

from typing import Any, Dict, Optional

SPELL_EFFECTS: Dict[str, Dict[str, Any]] = {
    # --- arcane damage ---
    "Magic Missile": {"level": 1, "classes": ["Magic-User"], "kind": "damage",
                      "missiles": True, "dice": "1d4+1", "save": "none"},
    "Burning Hands": {"level": 1, "classes": ["Magic-User"], "kind": "damage",
                      "per_level_flat": 1, "save": "none"},
    "Shocking Grasp": {"level": 1, "classes": ["Magic-User"], "kind": "damage",
                       "dice": "1d8", "per_level_plus": 1, "save": "none",
                       "touch": True},
    "Fireball": {"level": 3, "classes": ["Magic-User"], "kind": "damage",
                 "dice_per_level": "1d6", "save": "half", "save_cat": "spells"},
    "Lightning Bolt": {"level": 3, "classes": ["Magic-User"], "kind": "damage",
                       "dice_per_level": "1d6", "save": "half", "save_cat": "spells"},
    "Cone of Cold": {"level": 5, "classes": ["Magic-User"], "kind": "damage",
                     "dice_per_level": "1d4+1", "save": "half", "save_cat": "spells"},
    "Sleep": {"level": 1, "classes": ["Magic-User"], "kind": "sleep", "save": "none"},
    "Stinking Cloud": {"level": 2, "classes": ["Magic-User"], "kind": "incapacitate",
                       "dice": "1d4+1", "save": "negate", "save_cat": "death"},
    # --- divine heal / harm ---
    "Cure Light Wounds": {"level": 1, "classes": ["Cleric"], "kind": "heal",
                          "dice": "1d8"},
    "Cause Light Wounds": {"level": 1, "classes": ["Cleric"], "kind": "damage",
                           "dice": "1d8", "save": "none", "touch": True},
    "Cure Serious Wounds": {"level": 4, "classes": ["Cleric"], "kind": "heal",
                            "dice": "2d8+1"},
    "Cure Critical Wounds": {"level": 5, "classes": ["Cleric"], "kind": "heal",
                             "dice": "3d8+3"},
    "Flame Strike": {"level": 5, "classes": ["Cleric"], "kind": "damage",
                     "dice": "6d8", "save": "half", "save_cat": "spells"},
}

# lower-case alias -> canonical name
_ALIASES = {k.lower(): k for k in SPELL_EFFECTS}
_ALIASES.update({"fire ball": "Fireball", "cure light": "Cure Light Wounds",
                 "cure serious": "Cure Serious Wounds",
                 "cure critical": "Cure Critical Wounds",
                 "magic missiles": "Magic Missile"})

# Sleep effectiveness (HD category -> dice for number affected).
SLEEP_TABLE = [("1 HD or less", "4d4"), ("1+ to 2 HD", "2d4"),
               ("2+ to 3 HD", "1d4"), ("3+ to 4 HD", "1d2"),
               ("4+1 to 4+4 HD", "1d2-1"), ("above 4+4 HD", "0")]


def lookup(name: str) -> Optional[Dict[str, Any]]:
    spec = _ALIASES.get((name or "").strip().lower())
    if not spec:
        return None
    return dict(SPELL_EFFECTS[spec], name=spec)


def roll_amount(dice, spec: Dict[str, Any], level: int) -> Dict[str, Any]:
    """Roll a spell's base amount (before saves), with a breakdown."""
    level = max(1, int(level))
    if spec.get("missiles"):
        n = max(1, (level + 1) // 2)
        rolls = [dice.notation(spec["dice"]).total for _ in range(n)]
        return {"amount": sum(rolls), "detail": "{} missiles: {}".format(n, rolls)}
    if spec.get("per_level_flat"):
        amt = int(spec["per_level_flat"]) * level
        return {"amount": amt, "detail": "{}/level x {}".format(spec["per_level_flat"], level)}
    if spec.get("dice_per_level"):
        rolls = [dice.notation(spec["dice_per_level"]).total for _ in range(level)]
        return {"amount": sum(rolls),
                "detail": "{} x {} = {}".format(level, spec["dice_per_level"], rolls)}
    base = dice.notation(spec["dice"]).total
    if spec.get("per_level_plus"):
        bonus = int(spec["per_level_plus"]) * level
        return {"amount": base + bonus,
                "detail": "{}+{} ({}/level)".format(base, bonus, spec["per_level_plus"])}
    return {"amount": base, "detail": spec["dice"]}


def sleep_affected(dice) -> Dict[str, Any]:
    """Roll the number of creatures affected in each HD band (no save)."""
    out = {}
    for label, d in SLEEP_TABLE:
        out[label] = 0 if d == "0" else max(0, dice.notation(d).total)
    return out
