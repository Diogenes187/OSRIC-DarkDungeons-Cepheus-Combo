"""loyalty.py -- OSRIC 3.0 Charisma, loyalty, reaction, and morale data.

Transcribed from:
  Table 1.1.7A  CHARISMA (sidekick limit, loyalty modifier, reaction modifier)
  Section 2.2.4 Loyalty of Hirelings and Henchmen (initial 50% + the modifier
                tables) and Table 2.2.4A Result of Tested Loyalty
  Table 1.6.2.8A NPC and Monster Reaction
  Section 1.6.8 Morale (NPC morale = 50% + 5%/HD; d100 over it fails)
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# Charisma score -> (max henchmen, loyalty modifier, reaction modifier).
# Stored as ranges; look up with charisma_row().
_CHARISMA: List[Tuple[int, int, int, int, int]] = [
    # (lo, hi, henchmen, loyalty, reaction)
    (3, 3, 1, -30, -25),
    (4, 4, 1, -25, -20),
    (5, 5, 2, -20, -15),
    (6, 6, 2, -15, -10),
    (7, 7, 3, -10, -5),
    (8, 8, 3, -5, 0),
    (9, 11, 4, 0, 0),
    (12, 12, 5, 0, 0),
    (13, 13, 5, 0, 5),
    (14, 14, 6, 5, 10),
    (15, 15, 7, 15, 15),
    (16, 16, 8, 20, 25),
    (17, 17, 10, 30, 30),
    (18, 18, 15, 40, 35),
    (19, 19, 20, 50, 40),
]


def _row(cha: int) -> Tuple[int, int, int]:
    cha = max(3, min(int(cha), 19))
    for lo, hi, h, loy, rxn in _CHARISMA:
        if lo <= cha <= hi:
            return h, loy, rxn
    return 4, 0, 0


def max_henchmen(cha: int) -> int:
    return _row(cha)[0]


def loyalty_modifier(cha: int) -> int:
    return _row(cha)[1]


def reaction_modifier(cha: int) -> int:
    return _row(cha)[2]


INITIAL_LOYALTY = 50

# Section 2.2.4 modifier tables. Keys are lowercased; values add to loyalty.
PC_ALIGNMENT = {"chaotic": -10, "evil": -5, "neutral": 0, "good": 5, "lawful": 10}

RELATIONSHIP = {"similar": 0, "different": -10, "opposed": -20, "irreconcilable": -30}

STATUS = {"conscript": -20, "hireling": -10, "follower": 0, "henchman": 10}

SERVICE = {"0-1 month": -5, "0-1 years": 0, "1-2 years": 5, "2-3 years": 10,
           "3-4 years": 15, "4-5 years": 20, "5+ years": 25}

TRAINING = {"untrained": -30, "semi-trained": -20, "trained-untested": -10,
            "trained": 0, "veteran": 10, "elite": 20, "leader": 30}

PAYMENT = {"unpaid": -20, "late": -15, "very poor": -10, "poor": -5,
           "standard": 0, "good": 5, "very good": 10}

TREATMENT = {"vicious": -20, "cruel": -10, "normal": 0, "kind": 10, "beneficent": 20}

DISCIPLINE = {"brutal": -10, "indifferent": 0, "fair": 10}

# Table 2.2.4A: adjusted loyalty score -> band.
def loyalty_band(score: int) -> str:
    if score < 1:
        return "None"
    if score <= 25:
        return "Disloyal"
    if score <= 50:
        return "Somewhat Loyal"
    if score <= 75:
        return "Fairly Loyal"
    if score <= 100:
        return "Loyal"
    return "Fanatical"


# Table 1.6.2.8A: d100 -> reaction (after Charisma reaction modifier).
def reaction_band(roll: int) -> str:
    if roll <= 5:
        return "Very hostile"
    if roll <= 25:
        return "Hostile"
    if roll <= 45:
        return "Unfavorable"
    if roll <= 55:
        return "Neutral"
    if roll <= 75:
        return "Favorable"
    if roll <= 95:
        return "Friendly"
    return "Very friendly"
