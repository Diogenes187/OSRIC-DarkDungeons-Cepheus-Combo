"""travel.py -- overland wilderness travel (OSRIC movement + getting lost).

A party's base movement rate sets a normal-terrain daily distance; terrain scales
it (roads faster, forest/hills slower, mountains/swamp slowest). Without a guide,
rough terrain risks getting lost. This feeds the journey loop, which strings
together weather and the wandering-monster check each day.
"""
from __future__ import annotations

from typing import Any, Dict

from .dice import Dice

# Daily distance multiplier vs. open terrain.
TERRAIN_SPEED = {
    "road": 1.5, "plains": 1.0, "coast": 0.66, "desert": 0.66,
    "forest": 0.5, "hills": 0.5, "swamp": 0.33, "mountains": 0.33, "jungle": 0.33,
}
# Chance to get lost: d6 roll <= this means lost (0 = can't get lost).
LOST_CHANCE = {
    "road": 0, "plains": 1, "coast": 1, "desert": 3, "forest": 2,
    "hills": 2, "swamp": 3, "mountains": 3, "jungle": 4,
}
# A base movement of 120ft covers ~24 miles/day in open terrain.
_MILES_PER_120FT = 24.0


def miles_per_day(base_move_ft: int, terrain: str) -> int:
    mult = TERRAIN_SPEED.get((terrain or "").lower(), 1.0)
    return max(1, round((base_move_ft / 120.0) * _MILES_PER_120FT * mult))


def travel_day(dice: Dice, base_move_ft: int, terrain: str,
               has_guide: bool = False) -> Dict[str, Any]:
    miles = miles_per_day(base_move_ft, terrain)
    lost = False
    if not has_guide:
        threshold = LOST_CHANCE.get((terrain or "").lower(), 0)
        lost = threshold > 0 and dice.d6() <= threshold
    if lost:
        miles = max(1, round(miles * 0.5))      # wandering eats the day's progress
    return {"terrain": terrain, "miles": miles, "lost": lost}
