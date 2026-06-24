"""henchmen.py -- loyalty, morale, and reaction for hirelings and henchmen.

Loyalty starts at 50% (OSRIC Section 2.2.4), shifted by the master's Charisma
loyalty modifier and by the circumstance tables (status, training, payment,
treatment, discipline, length of service, alignment). A loyalty TEST rolls
d100: a result higher than the adjusted loyalty means the retainer gives in to
temptation. NPC morale in battle is 50% + 5%/HD, helped by the leader's loyalty
bonus and hurt by the situation. Reaction rolls add the Charisma reaction
modifier to d100 on the NPC reaction table.

All rolls go through the seeded Dice, so a recruiting or loyalty moment replays
identically.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .data import loyalty as L


def pc_alignment_mod(alignment: str) -> int:
    """Loyalty shift from the master's alignment: each axis contributes (Lawful
    +10 / Chaotic -10; Good +5 / Evil -5; Neutral 0). So LG = +15, CE = -15."""
    a = (alignment or "").upper().strip()
    if a in ("N", "TN", "NEUTRAL"):
        return 0
    mod = 0
    law = a[0] if a else ""
    moral = a[-1] if len(a) >= 2 else ""
    if law == "L":
        mod += 10
    elif law == "C":
        mod -= 10
    if moral == "G":
        mod += 5
    elif moral == "E":
        mod -= 5
    return mod


def compute_loyalty(cha: int, alignment: str = "N", relationship: str = "similar",
                    status: str = "follower", service: str = "0-1 years",
                    training: str = "trained", payment: str = "standard",
                    treatment: str = "normal", discipline: str = "indifferent"
                    ) -> Dict[str, Any]:
    """Return the adjusted loyalty score and its band, with a factor breakdown."""
    factors = {
        "base": L.INITIAL_LOYALTY,
        "charisma": L.loyalty_modifier(cha),
        "pc_alignment": pc_alignment_mod(alignment),
        "relationship": L.RELATIONSHIP.get(relationship.lower(), 0),
        "status": L.STATUS.get(status.lower(), 0),
        "service": L.SERVICE.get(service.lower(), 0),
        "training": L.TRAINING.get(training.lower(), 0),
        "payment": L.PAYMENT.get(payment.lower(), 0),
        "treatment": L.TREATMENT.get(treatment.lower(), 0),
        "discipline": L.DISCIPLINE.get(discipline.lower(), 0),
    }
    score = sum(factors.values())
    return {"loyalty": score, "band": L.loyalty_band(score), "factors": factors}


def loyalty_test(dice, adjusted_loyalty: int) -> Dict[str, Any]:
    """Roll d100; the retainer holds true on a roll <= the adjusted loyalty."""
    roll = dice.d100()
    return {"roll": roll, "loyalty": adjusted_loyalty,
            "band": L.loyalty_band(adjusted_loyalty),
            "holds": roll <= adjusted_loyalty}


def npc_morale(dice, hit_dice: float, loyalty_mod: int = 0,
               situational: int = 0) -> Dict[str, Any]:
    """NPC/hireling morale check. Morale = 50 + 5/HD + leader's loyalty bonus -
    the situation penalty. Holds on d100 <= morale; a big failure surrenders."""
    morale = int(50 + 5 * float(hit_dice) + loyalty_mod - situational)
    roll = dice.d100()
    holds = roll <= morale
    fail_by = roll - morale
    if holds:
        outcome = "holds"
    elif fail_by >= 51:
        outcome = "surrenders"
    else:
        outcome = "retreats"
    return {"morale": morale, "roll": roll, "holds": holds,
            "outcome": outcome}


def reaction_roll(dice, cha_reaction_mod: int = 0,
                  situational: int = 0) -> Dict[str, Any]:
    """NPC reaction (Table 1.6.2.8A): d100 + Charisma reaction modifier."""
    nat = dice.d100()
    total = max(1, min(nat + int(cha_reaction_mod) + int(situational), 100))
    return {"natural": nat, "modifier": int(cha_reaction_mod) + int(situational),
            "total": total, "reaction": L.reaction_band(total)}
