"""downtime.py -- natural healing and training (OSRIC 1.6.6.1 and levelling).

Natural healing: a character recovers 1 hp per day of uninterrupted rest. A
Constitution penalty delays the onset by that many days; a Constitution bonus
adds to the daily rate from the second week on; and four full weeks of rest
restore a character to full regardless.

Training: gaining a level takes 1d3 weeks and costs 1,500 gp x the character's
current level (1,500 to reach 2nd, 3,000 to reach 3rd, and so on).
"""
from __future__ import annotations

from typing import Any, Dict

from .data import abilities as ab


def natural_healing(days: int, hp_current: int, hp_max: int, con: int) -> Dict[str, Any]:
    """Hit points recovered over `days` of uninterrupted rest."""
    days = max(0, int(days))
    if hp_current >= hp_max or days == 0:
        return {"healed": 0, "hp": hp_current}
    if days >= 28:                                  # four weeks = full
        return {"healed": hp_max - hp_current, "hp": hp_max}
    hp_mod = ab.constitution_mods(con)["hp_mod"]
    delay = -hp_mod if hp_mod < 0 else 0            # Con penalty postpones healing
    bonus = hp_mod if hp_mod > 0 else 0             # Con bonus helps from week 2
    healed = 0
    for day in range(1, days + 1):
        if day <= delay:
            continue
        healed += 1 + (bonus if day > 7 else 0)
    new = min(hp_max, hp_current + healed)
    return {"healed": new - hp_current, "hp": new}


def training_cost(current_level: int) -> int:
    """Gold to train from current_level to the next (1,500 x current level)."""
    return 1500 * max(1, int(current_level))
