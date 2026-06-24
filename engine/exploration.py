"""exploration.py -- OSRIC dungeon procedures (deterministic, seeded).

Surprise, searching for secret doors and traps, listening at doors, and the
Strength feats (forcing doors, bending bars) -- the d6 and d100 checks that
drive careful play, plus light-source durations.
"""
from __future__ import annotations

from typing import Any, Dict

from .data import abilities as ab

# ancestry bonuses on a d6 search/listen
_ELVEN = ("Elf", "Half-elf")
_STONE = ("Dwarf", "Gnome")
_KEEN_EARS = ("Elf", "Gnome", "Halfling", "Half-orc")


def _d6_check(dice, chance_in_6: int) -> Dict[str, Any]:
    roll = dice.d6()
    return {"roll": roll, "chance_in_6": chance_in_6, "success": roll <= chance_in_6}


def search_secret_doors(dice, race: str = "Human") -> Dict[str, Any]:
    """Thorough search: 1 in 6, or 2 in 6 for elves and half-elves (1 turn / 10ft²)."""
    res = _d6_check(dice, 2 if race in _ELVEN else 1)
    res.update({"what": "secret doors", "race": race})
    return res


def search_traps(dice, race: str = "Human") -> Dict[str, Any]:
    """Quick check for a pit/trap: 2 in 6 per character, 3 in 6 for dwarves and
    gnomes using stone-kenning (on stonework)."""
    res = _d6_check(dice, 3 if race in _STONE else 2)
    res.update({"what": "traps", "race": race})
    return res


def listen_at_door(dice, race: str = "Human") -> Dict[str, Any]:
    """Hear noise: 1 in 6, 2 in 6 for elves, gnomes, halflings, and half-orcs
    (thieves/assassins should use their thief skill instead)."""
    res = _d6_check(dice, 2 if race in _KEEN_EARS else 1)
    res.update({"what": "listen", "race": race})
    return res


def force_door(dice, str_score: int, str_pct: int = 0) -> Dict[str, Any]:
    """Force a stuck door: succeed on d6 <= the Strength open-doors number."""
    target = ab.strength_mods(str_score, str_pct)["minor_test"]
    roll = dice.d6()
    return {"check": "force door", "roll": roll, "target_in_6": target,
            "success": roll <= target}


def bend_bars(dice, str_score: int, str_pct: int = 0) -> Dict[str, Any]:
    """Bend bars / lift gates: succeed on d100 <= the Strength percentage."""
    pct = ab.strength_mods(str_score, str_pct)["major_test"]
    roll = dice.d100()
    return {"check": "bend bars / lift gates", "roll": roll, "chance_pct": pct,
            "success": roll <= pct}


def surprise(dice, party_best_dex: int = 10, foe_best_dex: int = 10,
             foe_surprises_on: int = 2) -> Dict[str, Any]:
    """Each side rolls 1d6; surprised on a 1-2 (foes may surprise on more),
    shifted by the best Dexterity surprise modifier on the side. Returns the
    free segments each side gets."""
    def free(roll, dexmod, threshold):
        eff = roll - dexmod
        return max(0, (threshold + 1) - eff) if eff <= threshold else 0
    pr, fr = dice.d6(), dice.d6()
    party = free(pr, ab.dexterity_mods(party_best_dex)["surprise"], 2)
    foes = free(fr, ab.dexterity_mods(foe_best_dex)["surprise"], foe_surprises_on)
    return {"party_roll": pr, "foe_roll": fr,
            "party_surprised_segments": party, "foes_surprised_segments": foes}


# Light-source burn durations (turns; 1 turn = 10 minutes).
LIGHT_SOURCES = {
    "torch": {"turns": 6, "radius_ft": 40},
    "candle": {"turns": 3, "radius_ft": 20},          # ~30 minutes
    "lantern, hooded": {"turns": 24, "radius_ft": 30, "per": "pint of oil"},
    "lantern, bullseye": {"turns": 24, "radius_ft": 80, "per": "pint of oil"},
}


def light_duration(source: str) -> Dict[str, Any]:
    return LIGHT_SOURCES.get((source or "").strip().lower(),
                             {"note": "unknown light source"})
