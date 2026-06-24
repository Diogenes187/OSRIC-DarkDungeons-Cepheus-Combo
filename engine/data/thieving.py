"""thieving.py -- OSRIC 3.0 thief skill tables.

Transcribed from the Player Guide:
  Table 1.3.10.4B  THIEF SKILLS (base percentages by level)
  Table 1.3.10.4C  THIEF SKILLS -- DEXTERITY ADJUSTMENTS
  Table 1.3.10.4D  THIEF SKILLS -- ANCESTRY ADJUSTMENTS

A skill check succeeds on d100 <= the adjusted chance. Eight skills, stored under
short keys; the canonical labels are in SKILL_LABELS.
"""
from __future__ import annotations

from typing import Dict, List

SKILLS: List[str] = ["climb", "hide", "listen", "pick_locks", "pick_pockets",
                     "read_languages", "move_quietly", "traps"]

SKILL_LABELS: Dict[str, str] = {
    "climb": "Climb Walls", "hide": "Hide in Shadows", "listen": "Hear Noise",
    "pick_locks": "Open Locks", "pick_pockets": "Pick Pockets",
    "read_languages": "Read Languages", "move_quietly": "Move Silently",
    "traps": "Find/Remove Traps",
}

# Common synonyms the referee might pass.
SKILL_ALIASES: Dict[str, str] = {
    "climb walls": "climb", "climbwalls": "climb", "climbing": "climb",
    "hide in shadows": "hide", "hide_in_shadows": "hide", "hiding": "hide",
    "hear noise": "listen", "hear_noise": "listen",
    "open locks": "pick_locks", "open_locks": "pick_locks",
    "picklocks": "pick_locks", "locks": "pick_locks",
    "pick pockets": "pick_pockets", "pickpockets": "pick_pockets",
    "steal": "pick_pockets",
    "read languages": "read_languages", "languages": "read_languages",
    "move silently": "move_quietly", "move_silently": "move_quietly",
    "sneak": "move_quietly", "stealth": "move_quietly",
    "find traps": "traps", "remove traps": "traps", "find/remove traps": "traps",
    "disarm": "traps", "traps": "traps",
}

# Base chances, indexed by level (1-20). Order matches SKILLS.
_BASE: Dict[int, List[int]] = {
    1:  [85, 10, 10, 25, 30, 1, 15, 20],
    2:  [86, 15, 10, 29, 35, 5, 20, 25],
    3:  [87, 20, 15, 33, 40, 15, 27, 30],
    4:  [88, 25, 15, 37, 45, 20, 33, 35],
    5:  [90, 30, 20, 42, 50, 25, 40, 40],
    6:  [92, 35, 20, 47, 55, 30, 47, 45],
    7:  [94, 42, 25, 52, 60, 35, 55, 50],
    8:  [96, 48, 25, 57, 65, 40, 62, 55],
    9:  [98, 55, 30, 62, 70, 45, 70, 60],
    10: [99, 65, 30, 67, 80, 50, 78, 65],
    11: [99, 70, 35, 72, 90, 55, 86, 70],
    12: [99, 75, 35, 77, 100, 60, 94, 75],
    13: [99, 85, 40, 82, 105, 65, 99, 80],
    14: [99, 95, 40, 87, 110, 70, 99, 85],
    15: [99, 99, 50, 92, 115, 75, 99, 90],
    16: [99, 99, 50, 97, 125, 80, 99, 95],
    17: [99, 99, 55, 99, 125, 80, 99, 99],
    18: [99, 99, 55, 99, 125, 80, 99, 99],
    19: [99, 99, 55, 99, 125, 80, 99, 99],
    20: [99, 99, 55, 99, 125, 80, 99, 99],
}

# Dexterity adjustments (only scores 9-19 differ from zero).
_DEX: Dict[int, Dict[str, int]] = {
    9:  {"hide": -10, "pick_locks": -10, "pick_pockets": -15, "move_quietly": -20, "traps": -15},
    10: {"hide": -5, "pick_locks": -5, "pick_pockets": -10, "move_quietly": -15, "traps": -10},
    11: {"pick_pockets": -5, "move_quietly": -10, "traps": -5},
    12: {"move_quietly": -5},
    16: {"pick_locks": 5},
    17: {"hide": 5, "pick_locks": 10, "pick_pockets": 5, "move_quietly": 5, "traps": 5},
    18: {"hide": 10, "pick_locks": 15, "pick_pockets": 10, "move_quietly": 10, "traps": 10},
    19: {"hide": 15, "pick_locks": 20, "pick_pockets": 15, "move_quietly": 15, "traps": 15},
}

# Ancestry adjustments.
_ANCESTRY: Dict[str, Dict[str, int]] = {
    "Dwarf": {"climb": -10, "pick_locks": 15, "move_quietly": -5, "traps": 15, "read_languages": -5},
    "Elf": {"climb": -5, "hide": 10, "listen": 5, "pick_locks": -5, "pick_pockets": 5,
            "move_quietly": 5, "traps": 5, "read_languages": 10},
    "Gnome": {"climb": -15, "listen": 5, "pick_locks": 10},
    "Half-elf": {"hide": 5, "pick_pockets": 10},
    "Halfling": {"climb": -15, "hide": 15, "listen": 5, "pick_pockets": 5,
                 "move_quietly": 15, "read_languages": -5},
    "Half-orc": {"climb": 5, "listen": 5, "pick_locks": 5, "pick_pockets": -5,
                 "traps": 5, "read_languages": -10},
    "Human": {"climb": 5, "pick_locks": 5},
}


def canon_skill(skill: str) -> str:
    s = (skill or "").strip().lower().replace("-", " ")
    if s in SKILLS:
        return s
    return SKILL_ALIASES.get(s, s.replace(" ", "_"))


def base_chance(skill: str, level: int) -> int:
    level = max(1, min(int(level), 20))
    return _BASE[level][SKILLS.index(skill)]


def dex_adjust(skill: str, dex: int) -> int:
    return _DEX.get(int(dex or 0), {}).get(skill, 0)


def ancestry_adjust(skill: str, race: str) -> int:
    return _ANCESTRY.get(race or "", {}).get(skill, 0)
