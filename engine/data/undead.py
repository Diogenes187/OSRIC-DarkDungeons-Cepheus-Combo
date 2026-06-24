"""undead.py -- OSRIC 3.0 Turning the Undead table (Table 1.6.5A).

Columns are cleric level 1,2,3,4,5,6,7,8, then the brackets 9-13, 14-18, 19+.
Each cell is one of:
  "-"     no chance to affect this type
  number  turn on d20 >= number
  "T"     turned automatically
  "D"     affected automatically (2d6); good/neutral DESTROY, evil may control
  "D*"    affected automatically (1d6+6); good/neutral DESTROY, evil may control
"""
from __future__ import annotations

from typing import Dict, List, Optional

# index: 0..7 == levels 1..8; 8 == 9-13; 9 == 14-18; 10 == 19+
def level_column(level: int) -> int:
    level = max(1, int(level))
    if level <= 8:
        return level - 1
    if level <= 13:
        return 8
    if level <= 18:
        return 9
    return 10


# type number -> (example creature, [11 cells])
TURN_TABLE: Dict[int, List[str]] = {
    1:  ["10", "7", "4", "T", "T", "D", "D", "D*", "D*", "D*", "D*"],
    2:  ["13", "10", "7", "T", "T", "D", "D", "D", "D*", "D*", "D*"],
    3:  ["16", "13", "10", "4", "T", "T", "D", "D", "D", "D*", "D*"],
    4:  ["19", "16", "13", "7", "4", "T", "T", "D", "D", "D", "D*"],
    5:  ["20", "19", "16", "10", "7", "4", "T", "T", "D", "D", "D"],
    6:  ["-", "20", "19", "13", "10", "7", "4", "T", "T", "D", "D"],
    7:  ["-", "-", "20", "16", "13", "10", "7", "4", "T", "T", "D"],
    8:  ["-", "-", "-", "19", "16", "13", "10", "7", "4", "T", "D"],
    9:  ["-", "-", "-", "20", "19", "16", "13", "10", "7", "T", "T"],
    10: ["-", "-", "-", "-", "20", "19", "16", "13", "10", "7", "4"],
    11: ["-", "-", "-", "-", "-", "20", "19", "16", "13", "10", "7"],
    12: ["-", "-", "-", "-", "-", "-", "20", "19", "16", "13", "10"],
    13: ["-", "-", "-", "-", "-", "-", "-", "20", "19", "16", "13"],
}

TYPE_EXAMPLE: Dict[int, str] = {
    1: "Skeleton", 2: "Zombie", 3: "Ghoul", 4: "Shadow", 5: "Wight",
    6: "Ghast", 7: "Wraith", 8: "Mummy", 9: "Spectre", 10: "Vampire",
    11: "Ghost", 12: "Lich", 13: "Fiend",
}

# Creature name -> turning type. Covers the examples plus common synonyms.
NAME_TO_TYPE: Dict[str, int] = {
    "skeleton": 1, "skeletons": 1, "animated skeleton": 1,
    "zombie": 2, "zombies": 2,
    "ghoul": 3, "ghouls": 3, "lacedon": 3,
    "shadow": 4, "shadows": 4,
    "wight": 5, "wights": 5,
    "ghast": 6, "ghasts": 6,
    "wraith": 7, "wraiths": 7,
    "mummy": 8, "mummies": 8,
    "spectre": 9, "specter": 9, "spectres": 9,
    "vampire": 10, "vampires": 10,
    "ghost": 11, "ghosts": 11,
    "lich": 12, "liches": 12, "demilich": 12,
    "fiend": 13, "demon": 13, "devil": 13, "daemon": 13, "fiends": 13,
}


def resolve_type(undead) -> Optional[int]:
    """Map an int type, an example name, or a creature name to a turning type."""
    if isinstance(undead, int):
        return undead if undead in TURN_TABLE else None
    s = str(undead or "").strip().lower()
    if s.isdigit():
        n = int(s)
        return n if n in TURN_TABLE else None
    if s.startswith("type ") and s[5:].strip().isdigit():
        n = int(s[5:].strip())
        return n if n in TURN_TABLE else None
    return NAME_TO_TYPE.get(s)


def cell(undead_type: int, level: int) -> str:
    return TURN_TABLE[undead_type][level_column(level)]
