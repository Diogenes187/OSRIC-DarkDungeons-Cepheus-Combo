"""treasure.py -- OSRIC 3.0 treasure generation (Chapter Twelve, Loot Classes).

Monsters carry a LOOT entry like "Hoard 3, Cache 4". Each Loot Class is a list of
percentage-gated coin/gem/jewellery/magic rolls. This module encodes all of them
(Hoard 1-9, Individual 1-5, Cache 1-12) plus the gem and jewellery value tables,
and rolls a full treasure parcel deterministically from a seeded Dice.

Named magic items come from the magic-item catalog (separate); here a magic
result reports how many of what kind to roll.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..dice import Dice

# Coin values in gold pieces.
COIN_GP = {"cp": 0.01, "sp": 0.1, "ep": 0.5, "gp": 1.0, "pp": 5.0}


def _coin(pct, dice, mult, kind):
    return {"chance": pct, "kind": kind, "dice": dice, "mult": mult}


def _gj(pct, dice, mult, kind):     # gems / jewellery
    return {"chance": pct, "kind": kind, "dice": dice, "mult": mult}


def _magic(pct, count, desc):
    return {"chance": pct, "kind": "magic", "count": count, "desc": desc}


LOOT_CLASSES: Dict[str, List[dict]] = {
    "Hoard 1": [_coin(25, "1d6", 1000, "cp"), _coin(30, "1d6", 1000, "sp"),
                _coin(35, "1d6", 1000, "ep"), _coin(40, "1d10", 1000, "gp"),
                _coin(25, "1d4", 100, "pp"), _gj(60, "4d10", 1, "gems"),
                _gj(60, "3d10", 1, "jewellery"), _magic(30, 3, "any type")],
    "Hoard 2": [_coin(50, "1d8", 1000, "cp"), _coin(25, "1d6", 1000, "sp"),
                _coin(25, "1d4", 1000, "ep"), _coin(25, "1d3", 1000, "gp"),
                _gj(30, "1d8", 1, "gems"), _gj(20, "1d4", 1, "jewellery"),
                _magic(10, 1, "sword, armour, or weapon")],
    "Hoard 3": [_coin(20, "1d12", 1000, "cp"), _coin(30, "1d6", 1000, "sp"),
                _coin(10, "1d4", 1000, "ep"), _gj(25, "1d6", 1, "gems"),
                _gj(20, "1d3", 1, "jewellery"), _magic(10, 2, "any type")],
    "Hoard 4": [_coin(10, "1d8", 1000, "cp"), _coin(15, "1d12", 1000, "sp"),
                _coin(15, "1d8", 1000, "ep"), _coin(50, "1d6", 1000, "gp"),
                _gj(30, "1d10", 1, "gems"), _gj(25, "1d6", 1, "jewellery"),
                _magic(15, 3, "1 potion + 2 any type")],
    "Hoard 5": [_coin(5, "1d10", 1000, "cp"), _coin(25, "1d12", 1000, "sp"),
                _coin(25, "1d6", 1000, "ep"), _coin(25, "1d8", 1000, "gp"),
                _gj(15, "1d12", 1, "gems"), _gj(10, "1d8", 1, "jewellery"),
                _magic(25, 4, "1 scroll + 3 any type")],
    "Hoard 6": [_coin(10, "1d20", 1000, "sp"), _coin(15, "1d12", 1000, "ep"),
                _coin(40, "1d10", 1000, "gp"), _coin(35, "1d8", 100, "pp"),
                _gj(20, "3d10", 1, "gems"), _gj(10, "1d10", 1, "jewellery"),
                _magic(30, 5, "1 potion + 1 scroll + 3 (no sword/misc)")],
    "Hoard 7": [_coin(50, "10d4", 1000, "gp"), _coin(50, "1d20", 100, "pp"),
                _gj(30, "5d4", 1, "gems"), _gj(25, "1d10", 1, "jewellery"),
                _magic(35, 5, "1 scroll + 4 any type")],
    "Hoard 8": [_coin(25, "5d6", 1000, "cp"), _coin(40, "1d100", 1000, "sp"),
                _coin(40, "10d4", 1000, "ep"), _coin(55, "10d6", 1000, "gp"),
                _coin(25, "5d10", 100, "pp"), _gj(50, "1d100", 1, "gems"),
                _gj(50, "10d4", 1, "jewellery"),
                _magic(15, 6, "1 potion + 1 scroll + 4 any type")],
    "Hoard 9": [_coin(30, "3d6", 100, "pp"), _gj(55, "2d10", 1, "gems"),
                _gj(50, "1d12", 1, "jewellery"), _magic(15, 1, "any type")],
    "Individual 1": [_coin(100, "3d8", 1, "cp")],
    "Individual 2": [_coin(100, "3d6", 1, "sp")],
    "Individual 3": [_coin(100, "2d6", 1, "ep")],
    "Individual 4": [_coin(100, "2d4", 1, "gp")],
    "Individual 5": [_coin(100, "1d6", 1, "pp")],
    "Cache 1": [_coin(25, "1d4", 1000, "cp"), _coin(20, "1d3", 1000, "sp")],
    "Cache 2": [_coin(30, "1d6", 1000, "sp"), _coin(25, "1d2", 1000, "ep")],
    "Cache 3": [_gj(50, "1d4", 1, "gems")],
    "Cache 4": [_coin(40, "2d4", 1000, "gp"), _coin(50, "10d6", 100, "pp"),
                _gj(55, "4d8", 1, "gems"), _gj(45, "1d12", 1, "jewellery")],
    "Cache 5": [_magic(40, 2, "potions (2d4)")],
    "Cache 6": [_magic(50, 1, "scrolls (1d4)")],
    "Cache 7": [_gj(90, "1d8", 10, "gems"), _gj(80, "5d6", 1, "jewellery"),
                _magic(70, 6, "1 ring, 1 wand, 1 misc, 1 armour, 1 sword, 1 weapon")],
    "Cache 8": [_magic(85, 12, "2 each: rings, wands, misc, armour, swords, weapons")],
    "Cache 9": [_coin(60, "5d6", 1000, "gp"), _coin(15, "1d8", 100, "pp"),
                _gj(60, "1d8", 10, "gems"), _gj(50, "5d8", 1, "jewellery"),
                _magic(55, 1, "map")],
    "Cache 10": [_magic(60, 2, "1 potion + 1 miscellaneous magic")],
    "Cache 11": [_coin(70, "2d6", 1000, "gp")],
    "Cache 12": [_coin(20, "1d3", 1000, "cp"), _coin(25, "1d4", 1000, "sp"),
                 _coin(25, "1d4", 1000, "ep"), _coin(30, "1d4", 1000, "gp"),
                 _coin(30, "1d6", 100, "pp"), _gj(55, "1d6", 10, "gems"),
                 _gj(50, "5d6", 1, "jewellery"), _magic(50, 3, "any type")],
}

# Gem value: (cumulative d100 threshold, value dice, mult, description).
GEM_VALUE = [(30, "4d4", 1, "ornamental stone"), (55, "2d4", 10, "semi-precious stone"),
             (75, "4d4", 10, "fancy stone"), (90, "2d4", 100, "precious stone"),
             (99, "4d4", 100, "gem"), (100, "2d4", 1000, "jewel")]

JEWELLERY_ITEMS = ["amulet", "anklet", "arm-ring", "belt", "bracelet", "brooch",
                   "buckle", "chain", "chalice", "choker", "clasp", "comb",
                   "coronet", "crown", "diadem", "earring", "goblet", "idol",
                   "locket", "medallion", "necklace", "pendant", "pin", "ring",
                   "seal", "statuette", "tiara"]

# Jewellery value by composition (d10): (max_roll, label, dice, mult).
JEWELLERY_VALUE = [(4, "silver", "1d10", 100), (6, "silver & gold", "2d6", 100),
                   (8, "gold", "3d6", 100), (9, "silver & gems", "5d6", 100),
                   (10, "gold & gems", "2d4", 1000)]


def _roll_gem(dice: Dice) -> Dict[str, Any]:
    r = dice.d100()
    for thresh, dstr, mult, desc in GEM_VALUE:
        if r <= thresh:
            return {"description": desc, "value": dice.notation(dstr).total * mult}
    return {"description": "gem", "value": dice.notation("4d4").total * 100}


def _roll_jewellery(dice: Dice) -> Dict[str, Any]:
    item = JEWELLERY_ITEMS[dice.d(len(JEWELLERY_ITEMS)) - 1]
    r = dice.d10()
    for max_roll, label, dstr, mult in JEWELLERY_VALUE:
        if r <= max_roll:
            return {"item": "{} ({})".format(item, label),
                    "value": dice.notation(dstr).total * mult}
    return {"item": item, "value": dice.notation("3d6").total * 100}


@dataclass
class Treasure:
    coins: Dict[str, int] = field(default_factory=dict)
    gems: List[dict] = field(default_factory=list)
    jewellery: List[dict] = field(default_factory=list)
    magic: List[dict] = field(default_factory=list)

    @property
    def total_gp(self) -> float:
        t = sum(COIN_GP.get(k, 0) * v for k, v in self.coins.items())
        t += sum(g["value"] for g in self.gems)
        t += sum(j["value"] for j in self.jewellery)
        return round(t, 2)


def generate(dice: Dice, *loot_classes: str) -> Treasure:
    """Roll a treasure parcel for one or more loot classes (e.g. 'Hoard 3')."""
    out = Treasure()
    for name in loot_classes:
        lines = LOOT_CLASSES.get(name.strip())
        if not lines:
            continue
        for ln in lines:
            if ln["chance"] < 100 and dice.d100() > ln["chance"]:
                continue
            kind = ln["kind"]
            if kind in COIN_GP:
                amt = dice.notation(ln["dice"]).total * ln["mult"]
                out.coins[kind] = out.coins.get(kind, 0) + amt
            elif kind == "gems":
                for _ in range(dice.notation(ln["dice"]).total * ln["mult"]):
                    out.gems.append(_roll_gem(dice))
            elif kind == "jewellery":
                for _ in range(dice.notation(ln["dice"]).total * ln["mult"]):
                    out.jewellery.append(_roll_jewellery(dice))
            elif kind == "magic":
                out.magic.append({"count": ln["count"], "detail": ln["desc"]})
    return out


def loot_classes_in(loot_field: str) -> List[str]:
    """Parse a monster LOOT string like 'Hoard 3, Cache 4' into class names."""
    found = re.findall(r"(?:Hoard|Cache|Individual)\s+\d+", loot_field or "")
    return found
