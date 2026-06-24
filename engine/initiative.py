"""initiative.py -- OSRIC combat initiative and round order (seeded).

OSRIC resolves a round by segments: you roll 1d6 and act in that segment (lower =
earlier). On top of the roll:
  * Missile attacks shift by the attacker's Dexterity initiative adjustment
    (Table 1.1.3A) -- quick hands shoot sooner.
  * A spell completes its casting time in segments AFTER the caster's roll, so a
    slow spell lands late (and can be spoiled if the caster is hit first).
  * Weapon speed factor breaks ties (the faster weapon strikes first); Dexterity
    breaks any remaining tie, so the nimble character wins a dead heat.

This module just computes the order; the combat tracker stores and re-rolls it
each round (OSRIC re-rolls initiative every round).
"""
from __future__ import annotations

from typing import Any, Dict, List

from .data import abilities as ab


def dex_initiative(dex: int) -> int:
    """The Dexterity initiative segment adjustment (negative = acts earlier)."""
    return ab.dexterity_mods(int(dex or 10))["initiative"]


def combatant_segment(dice, c: Dict[str, Any]) -> Dict[str, Any]:
    """Roll one combatant's initiative for the round."""
    roll = dice.d6()
    action = (c.get("action") or "melee").lower()
    dexmod = dex_initiative(c.get("dex", 10))
    seg = roll + dexmod                      # Dexterity shifts EVERYONE's initiative
                                             # (negative = quicker), melee/missile/spell
    if action == "spell":
        seg += int(c.get("casting_time", 0) or 0)   # spell still lands after casting time
    return {
        "name": c.get("name", "?"), "side": c.get("side", "party"),
        "action": action, "roll": roll, "segment": seg,
        "weapon_speed": int(c.get("weapon_speed", 5) or 5),
        "dex_init": dexmod,
    }


def roll_order(dice, combatants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Roll initiative for everyone and return them ordered for the round
    (earliest segment first; ties go to the faster weapon, then higher Dex)."""
    rolled = [combatant_segment(dice, c) for c in combatants]
    rolled.sort(key=lambda r: (r["segment"], r["weapon_speed"], r["dex_init"]))
    for i, r in enumerate(rolled, 1):
        r["order"] = i
    return rolled


def surprise_segments(dice, party_dex_best: int = 10,
                      foe_dex_best: int = 10) -> Dict[str, Any]:
    """A simple surprise check: each side rolls 1d6 and is surprised on a 1-2,
    shifted by the best Dexterity surprise modifier on that side. Returns how
    many segments of free action each side gets (0 = not surprised)."""
    def check(roll, dexmod):
        # surprised if roll (minus the side's Dex surprise bonus) is 1-2
        eff = roll - dexmod
        return max(0, 3 - eff) if eff <= 2 else 0
    pr, fr = dice.d6(), dice.d6()
    p_surprised = check(pr, ab.dexterity_mods(party_dex_best)["surprise"])
    f_surprised = check(fr, ab.dexterity_mods(foe_dex_best)["surprise"])
    return {"party_surprised_segments": p_surprised,
            "foes_surprised_segments": f_surprised}
