"""weather.py -- a simple seasonal weather generator for the Flanaess.

Deterministic from a seeded Dice. Produces a day's temperature, sky,
precipitation, wind, and the occasional notable event -- enough to colour travel
and feed encounter/visibility rulings without pretending to be a climate model.
"""
from __future__ import annotations

from typing import Any, Dict

from ..dice import Dice

# (low, high) daytime temperature band in degrees F, by season.
_TEMP = {"spring": (38, 66), "summer": (60, 92),
         "autumn": (34, 62), "winter": (8, 40)}

# Chance (d100) of precipitation by season.
_PRECIP_CHANCE = {"spring": 45, "summer": 30, "autumn": 50, "winter": 55}


def generate(dice: Dice, season: str = "spring") -> Dict[str, Any]:
    s = (season or "spring").strip().lower()
    lo, hi = _TEMP.get(s, (40, 70))
    temp = lo + dice.d(hi - lo + 1) - 1

    sky_roll = dice.d100()
    sky = "clear" if sky_roll <= 45 else "partly cloudy" if sky_roll <= 75 \
        else "overcast"

    precip = "none"
    if dice.d100() <= _PRECIP_CHANCE.get(s, 40):
        cold = temp <= 33
        heavy = dice.d100() <= 30
        if cold:
            precip = "heavy snow" if heavy else "light snow"
        else:
            precip = "thunderstorm" if (s == "summer" and heavy) else \
                     ("heavy rain" if heavy else "light rain")

    wind_roll = dice.d100()
    wind = "calm" if wind_roll <= 40 else "breezy" if wind_roll <= 80 \
        else "strong winds" if wind_roll <= 95 else "gale"

    special = None
    if dice.d100() <= 8:
        special = dice.notation("1d6").total  # placeholder index
        events = ["dense fog at dawn", "unseasonable warmth", "sudden cold snap",
                  "rainbow after rain", "distant lightning", "eerie still air"]
        special = events[(special - 1) % len(events)]

    return {"season": s, "temperature_f": temp, "sky": sky,
            "precipitation": precip, "wind": wind, "special": special}
