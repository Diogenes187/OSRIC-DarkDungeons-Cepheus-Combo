"""turning.py -- resolve a Turn Undead attempt (deterministic, seeded).

A cleric (or paladin as a cleric two levels lower) makes one d20 turning attempt
against a type of undead. The OSRIC table (engine.data.undead) gives the result
code; this resolves how many are affected and what happens to them:

  good / neutral cleric -- undead are TURNED (flee 3d4 rounds) or DESTROYED.
  evil cleric           -- undead are commanded: cowed, or (61-00 on d100)
                           brought under the cleric's control.

Numbers affected: 2d6 for a normal result, 1d6+6 for a "D*" mass result; only
1d2 for fiends or paladins. Paladins can be turned but never destroyed.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .data import undead as undead_data

TURN_CLASSES = ("Cleric", "Druid")   # Druids don't turn in OSRIC; kept for clarity


def turning_level(char_class: str, level: int) -> int:
    """Effective cleric level for turning. Paladins turn as a cleric two levels
    lower (so a 3rd-level paladin = 1st-level cleric)."""
    if char_class == "Paladin":
        return max(0, level - 2)
    return level


def turn_undead(dice, level: int, undead, alignment: str = "N",
                number_present: Optional[int] = None,
                is_paladin_target: bool = False) -> Dict[str, Any]:
    utype = undead_data.resolve_type(undead)
    if utype is None:
        return {"error": "unknown undead type: {}".format(undead)}
    if level < 1:
        return {"undead_type": utype, "example": undead_data.TYPE_EXAMPLE[utype],
                "code": "-", "affected": 0, "outcome": "no_effect",
                "note": "Too low level to turn undead."}

    code = undead_data.cell(utype, level)
    evil = str(alignment or "").upper().endswith("E")
    fiend_or_pal = (utype == 13) or is_paladin_target

    out: Dict[str, Any] = {
        "undead_type": utype, "example": undead_data.TYPE_EXAMPLE[utype],
        "cleric_level": level, "code": code, "alignment": alignment,
        "roll": None, "needed": None, "success": None, "affected": 0,
        "outcome": "no_effect", "flee_rounds": None,
        "control_roll": None, "controlled": None,
    }

    if code == "-":
        out["note"] = "No chance to affect this type at this level."
        return out

    # Determine success.
    if code in ("T", "D", "D*"):
        out["success"] = True
    else:                                    # a number: roll d20 >= it
        needed = int(code)
        roll = dice.d20()
        out["roll"] = roll
        out["needed"] = needed
        out["success"] = roll >= needed
        if not out["success"]:
            out["outcome"] = "failed"
            return out

    # How many are affected.
    if fiend_or_pal:
        affected = dice.d(2)                 # 1d2
    elif code == "D*":
        affected = dice.d6() + 6             # 1d6+6
    else:
        affected = dice.d6() + dice.d6()     # 2d6
    if number_present is not None:
        affected = min(affected, int(number_present))
    out["affected"] = affected

    # Outcome.
    destroys = code in ("D", "D*")
    if evil:
        if is_paladin_target:
            out["outcome"] = "turned"        # paladins are only ever turned
            out["flee_rounds"] = dice.d4() + dice.d4() + dice.d4()
        else:
            ctrl = dice.d100()
            out["control_roll"] = ctrl
            out["controlled"] = ctrl >= 61
            out["outcome"] = "controlled" if ctrl >= 61 else "cowed"
    else:
        if destroys and not is_paladin_target:
            out["outcome"] = "destroyed"
        else:
            out["outcome"] = "turned"
            out["flee_rounds"] = dice.d4() + dice.d4() + dice.d4()  # 3d4
    return out
