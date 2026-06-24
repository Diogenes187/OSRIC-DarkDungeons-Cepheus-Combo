"""specialization.py -- OSRIC weapon specialisation (optional rule, 1.3.13).

Single-classed fighters, rangers, and paladins may specialise in one exact
weapon, gaining +1 to hit and +2 damage (or +3/+3 with double specialisation
for melee weapons that aren't pole arms or two-handed swords), plus an improved
attack rate that REPLACES the normal melee-attack-combination progression.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

SPECIALIST_CLASSES = ("Fighter", "Ranger", "Paladin")
NO_DOUBLE = ("Pole arm", "Sword, two-handed")


def melee_attack_rate(level: int) -> str:
    """Attacks per round with a specialised melee weapon (Table 1.3.13A)."""
    if level <= 6:
        return "3/2"
    if level <= 12:
        return "2/1"
    return "5/2"


# Base (unspecialised) melee attack progression -- the "Melee Attack Combination"
# class abilities. Fighters/paladins improve at 7th and 13th; rangers at 8th/15th.
_WARRIOR_RATE = {
    "Fighter": [(6, "1/1"), (12, "3/2"), (99, "2/1")],
    "Paladin": [(6, "1/1"), (12, "3/2"), (99, "2/1")],
    "Ranger":  [(7, "1/1"), (14, "3/2"), (99, "2/1")],
}
_RATE_VALUE = {"1/1": 2, "3/2": 3, "2/1": 4, "5/2": 5}   # attacks per 2 rounds


def base_melee_rate(char_class: str, level: int) -> str:
    table = _WARRIOR_RATE.get(char_class)
    if not table:
        return "1/1"
    for cap, rate in table:
        if level <= cap:
            return rate
    return "2/1"


def best_base_rate(classes) -> str:
    """The best base melee rate across a (possibly multi-class) character."""
    best = "1/1"
    for c in classes or []:
        r = base_melee_rate(c.get("class"), int(c.get("level", 1) or 1))
        if _RATE_VALUE.get(r, 2) > _RATE_VALUE.get(best, 2):
            best = r
    return best


def attacks_this_round(rate: str, round_no: int) -> int:
    """How many attacks the rate grants in a given round (3/2 = 2 then 1; 5/2 =
    3 then 2; 2/1 = 2 every round)."""
    if rate == "2/1":
        return 2
    if rate == "3/2":
        return 2 if round_no % 2 == 1 else 1
    if rate == "5/2":
        return 3 if round_no % 2 == 1 else 2
    return 1


def missile_rate(weapon: str, level: int) -> str:
    """Improved rate of fire for a specialised missile weapon."""
    w = (weapon or "").lower()
    if "crossbow, heavy" in w:
        return ["0.5", "1", "2 (odd rounds)"][_band(level)]
    if "crossbow, light" in w:
        return ["1", "2 (odd rounds)", "2"][_band(level)]
    if "bow" in w:
        return ["2", "3", "4"][_band(level)]
    return melee_attack_rate(level)


def _band(level: int) -> int:
    return 0 if level <= 6 else (1 if level <= 12 else 2)


def bonuses(double: bool = False) -> Dict[str, int]:
    """The to-hit and damage bonuses for (double) specialisation."""
    return {"to_hit": 1, "damage": 3} if double else {"to_hit": 1, "damage": 2}
    # Note: double specialisation is +3 damage (and stays +1 to hit per OSRIC's
    # later-supplement wording); single is +1/+2.


def can_specialise(char_class: str) -> bool:
    return char_class in SPECIALIST_CLASSES


def assess(spec: Optional[Dict[str, Any]], weapon: str, level: int,
           is_missile: bool = False) -> Optional[Dict[str, Any]]:
    """If `spec` (the character's stored {weapon, double}) matches `weapon`,
    return the applicable bonuses and attack rate; otherwise None."""
    if not spec or not spec.get("weapon"):
        return None
    if spec["weapon"].strip().lower() != (weapon or "").strip().lower():
        return None
    double = bool(spec.get("double")) and spec["weapon"] not in NO_DOUBLE
    b = bonuses(double)
    rate = missile_rate(weapon, level) if is_missile else melee_attack_rate(level)
    return {"weapon": spec["weapon"], "double": double,
            "to_hit": b["to_hit"], "damage": b["damage"], "attack_rate": rate}
