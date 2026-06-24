"""equipment.py -- OSRIC 3.0 equipment: weapons, armour, gear, and encumbrance.

Transcribed from the Player Guide:
  Table 1.1.2A   Strength (encumbrance allowance, in lbs)
  Table 1.4.2.3A General Equipment (+ containers)
  Table 1.4.2.3B/C Melee Weapons (damage, weight, cost, speed)
  Table 1.4.2.3D/E Missile Weapons + Ammunition
  Table 1.4.2.G  Armour (weight, movement cap, AC, cost)
  Table 1.5.3.3A Encumbrance -> movement fraction

Weights are in pounds (a "coin" = 0.1 lb, so 10 coins = 1 lb). Costs are stored
in copper pieces for exact arithmetic: 1 gp = 100 cp, 1 sp = 10 cp, 1 pp = 500 cp.
"""
from __future__ import annotations

import math
from typing import Dict, Optional


def gp(n: float) -> int: return int(round(n * 100))
def sp(n: float) -> int: return int(round(n * 10))
def cp(n: float) -> int: return int(round(n))


def cost_string(cost_cp: int) -> str:
    if cost_cp % 100 == 0:
        return "{} gp".format(cost_cp // 100)
    if cost_cp % 10 == 0:
        return "{} sp".format(cost_cp // 10)
    return "{} cp".format(cost_cp)


# ---- weapons (melee + missile in one catalog) -------------------------
# name -> {damage_sm, damage_lg, weight, cost_cp, speed, hands, dtype, [missile fields]}
WEAPONS: Dict[str, Dict] = {
    "Axe, battle": {"damage_sm": "1d8", "damage_lg": "1d8", "weight": 7, "cost_cp": gp(5), "speed": 7, "hands": "2 or 1(STR15+)", "dtype": "slashing"},
    "Axe, hand": {"damage_sm": "1d6", "damage_lg": "1d4", "weight": 5, "cost_cp": gp(1), "speed": 4, "hands": "1", "dtype": "slashing", "range": "10ft", "rof": 1},
    "Club": {"damage_sm": "1d6", "damage_lg": "1d3", "weight": 3, "cost_cp": cp(2), "speed": 4, "hands": "1", "dtype": "blunt", "range": "10ft", "rof": 1},
    "Dagger": {"damage_sm": "1d4", "damage_lg": "1d3", "weight": 1, "cost_cp": gp(2), "speed": 2, "hands": "1", "dtype": "piercing", "range": "10ft", "rof": 2},
    "Flail, heavy": {"damage_sm": "1d6+1", "damage_lg": "2d4", "weight": 10, "cost_cp": gp(3), "speed": 7, "hands": "2 or 1(STR14+)", "dtype": "blunt"},
    "Flail, light": {"damage_sm": "1d4+1", "damage_lg": "1d4+1", "weight": 4, "cost_cp": gp(6), "speed": 6, "hands": "1", "dtype": "blunt"},
    "Halberd": {"damage_sm": "1d10", "damage_lg": "2d6", "weight": 18, "cost_cp": gp(9), "speed": 9, "hands": "2", "dtype": "piercing/slashing"},
    "Javelin": {"damage_sm": "1d6", "damage_lg": "1d4", "weight": 2, "cost_cp": sp(5), "speed": 8, "hands": "1", "dtype": "piercing", "range": "20ft", "rof": 1},
    "Lance": {"damage_sm": "2d4+1", "damage_lg": "3d6", "weight": 15, "cost_cp": gp(6), "speed": 8, "hands": "1", "dtype": "piercing"},
    "Mace, heavy": {"damage_sm": "1d6+1", "damage_lg": "1d6", "weight": 10, "cost_cp": gp(10), "speed": 7, "hands": "2 or 1(STR13+)", "dtype": "blunt"},
    "Mace, light": {"damage_sm": "1d4+1", "damage_lg": "1d4+1", "weight": 5, "cost_cp": gp(4), "speed": 6, "hands": "1", "dtype": "blunt"},
    "Morning star": {"damage_sm": "2d4", "damage_lg": "1d6+1", "weight": 12, "cost_cp": gp(5), "speed": 7, "hands": "2 or 1(STR16+)", "dtype": "blunt/piercing"},
    "Pick, heavy": {"damage_sm": "1d6+1", "damage_lg": "2d4", "weight": 8, "cost_cp": gp(8), "speed": 7, "hands": "2 or 1(STR14+)", "dtype": "blunt/piercing"},
    "Pick, light": {"damage_sm": "1d4+1", "damage_lg": "1d4", "weight": 4, "cost_cp": gp(5), "speed": 5, "hands": "1", "dtype": "blunt/piercing"},
    "Pole arm": {"damage_sm": "1d6+1", "damage_lg": "1d10", "weight": 8, "cost_cp": gp(6), "speed": 13, "hands": "2", "dtype": "blunt/piercing/slashing"},
    "Spear": {"damage_sm": "1d6", "damage_lg": "1d8", "weight": 5, "cost_cp": gp(1), "speed": 7, "hands": "2 or 1", "dtype": "piercing", "range": "15ft", "rof": 1},
    "Staff": {"damage_sm": "1d6", "damage_lg": "1d6", "weight": 5, "cost_cp": 0, "speed": 4, "hands": "2", "dtype": "blunt"},
    "Sword, bastard": {"damage_sm": "2d4", "damage_lg": "2d8", "weight": 10, "cost_cp": gp(25), "speed": 6, "hands": "2 or 1(STR15+)", "dtype": "slashing"},
    "Sword, broad": {"damage_sm": "2d4", "damage_lg": "1d6+1", "weight": 8, "cost_cp": gp(15), "speed": 5, "hands": "2 or 1(STR12+)", "dtype": "slashing"},
    "Sword, long": {"damage_sm": "1d8", "damage_lg": "1d12", "weight": 7, "cost_cp": gp(15), "speed": 5, "hands": "1", "dtype": "slashing"},
    "Sword, scimitar": {"damage_sm": "1d8", "damage_lg": "1d8", "weight": 5, "cost_cp": gp(15), "speed": 5, "hands": "1", "dtype": "slashing"},
    "Sword, short": {"damage_sm": "1d6", "damage_lg": "1d8", "weight": 3, "cost_cp": gp(8), "speed": 3, "hands": "1", "dtype": "slashing"},
    "Sword, two-handed": {"damage_sm": "1d10", "damage_lg": "3d6", "weight": 25, "cost_cp": gp(30), "speed": 10, "hands": "2", "dtype": "slashing"},
    "Trident": {"damage_sm": "1d6+1", "damage_lg": "3d4", "weight": 5, "cost_cp": gp(4), "speed": 6, "hands": "2 or 1(STR14+)", "dtype": "piercing"},
    "Warhammer, heavy": {"damage_sm": "1d6+1", "damage_lg": "1d6", "weight": 10, "cost_cp": gp(7), "speed": 7, "hands": "2 or 1(STR15+)", "dtype": "blunt"},
    "Warhammer, light": {"damage_sm": "1d4+1", "damage_lg": "1d4", "weight": 5, "cost_cp": gp(1), "speed": 4, "hands": "1", "dtype": "blunt", "range": "10ft", "rof": 1},
    # Launched missile weapons
    "Bow, long": {"damage_sm": "1d6", "damage_lg": "1d6", "weight": 12, "cost_cp": gp(60), "hands": "2", "dtype": "piercing", "range": "70ft", "rof": 2, "launched": True},
    "Bow, short": {"damage_sm": "1d6", "damage_lg": "1d6", "weight": 8, "cost_cp": gp(15), "hands": "2", "dtype": "piercing", "range": "50ft", "rof": 2, "launched": True},
    "Composite bow, long": {"damage_sm": "1d6", "damage_lg": "1d6", "weight": 8, "cost_cp": gp(100), "hands": "2", "dtype": "piercing", "range": "60ft", "rof": 2, "launched": True},
    "Composite bow, short": {"damage_sm": "1d6", "damage_lg": "1d6", "weight": 5, "cost_cp": gp(75), "hands": "2", "dtype": "piercing", "range": "50ft", "rof": 2, "launched": True},
    "Crossbow, heavy": {"damage_sm": "1d6+1", "damage_lg": "1d6+1", "weight": 12, "cost_cp": gp(20), "hands": "2", "dtype": "piercing", "range": "80ft", "rof": 0.5, "launched": True},
    "Crossbow, light": {"damage_sm": "1d4+1", "damage_lg": "1d4+1", "weight": 4, "cost_cp": gp(12), "hands": "2", "dtype": "piercing", "range": "60ft", "rof": 1, "launched": True},
    "Dart": {"damage_sm": "1d3", "damage_lg": "1d2", "weight": 0.5, "cost_cp": sp(2), "hands": "1", "dtype": "piercing", "range": "15ft", "rof": 3},
    "Sling": {"damage_sm": "1d4+1", "damage_lg": "1d6+1", "weight": 0.5, "cost_cp": sp(5), "hands": "1", "dtype": "blunt", "range": "35ft", "rof": 1, "launched": True},
}

AMMUNITION: Dict[str, Dict] = {
    "Arrows (12)": {"weight": 4, "cost_cp": gp(2)},
    "Bolts, heavy (12)": {"weight": 4, "cost_cp": gp(4)},
    "Bolts, light (12)": {"weight": 2, "cost_cp": gp(2)},
    "Sling bullets (12)": {"weight": 4, "cost_cp": gp(1)},
}

# ---- armour -----------------------------------------------------------
# name -> {weight, move_cap (ft, None for shields), ac_desc, ac_asc, cost_cp}
ARMOUR: Dict[str, Dict] = {
    "Padded": {"weight": 10, "move_cap": 90, "ac_desc": 8, "cost_cp": gp(4)},
    "Leather": {"weight": 15, "move_cap": 120, "ac_desc": 8, "cost_cp": gp(5)},
    "Studded leather": {"weight": 20, "move_cap": 90, "ac_desc": 7, "cost_cp": gp(15)},
    "Ring mail": {"weight": 35, "move_cap": 90, "ac_desc": 7, "cost_cp": gp(30)},
    "Scale or lamellar": {"weight": 40, "move_cap": 60, "ac_desc": 6, "cost_cp": gp(45)},
    "Chain mail": {"weight": 30, "move_cap": 90, "ac_desc": 5, "cost_cp": gp(75)},
    "Elfin mail": {"weight": 15, "move_cap": 120, "ac_desc": 5, "cost_cp": None},
    "Splint": {"weight": 40, "move_cap": 60, "ac_desc": 4, "cost_cp": gp(80)},
    "Banded": {"weight": 35, "move_cap": 90, "ac_desc": 4, "cost_cp": gp(90)},
    "Plate mail": {"weight": 45, "move_cap": 60, "ac_desc": 3, "cost_cp": gp(400)},
    "Shield, small": {"weight": 5, "move_cap": None, "ac_bonus": 1, "cost_cp": gp(10)},
    "Shield, medium": {"weight": 8, "move_cap": None, "ac_bonus": 1, "cost_cp": gp(12)},
    "Shield, large": {"weight": 10, "move_cap": None, "ac_bonus": 1, "cost_cp": gp(15)},
}
for _a in ARMOUR.values():
    if "ac_desc" in _a:
        _a["ac_asc"] = 20 - _a["ac_desc"]

# ---- general gear (weight in lbs when carried; worn 0(x) -> x) ---------
GEAR: Dict[str, Dict] = {
    "Backpack": {"weight": 2, "cost_cp": gp(2)},
    "Bedroll": {"weight": 5, "cost_cp": sp(2)},
    "Bell": {"weight": 0, "cost_cp": gp(1)},
    "Blanket, woollen": {"weight": 2, "cost_cp": sp(2)},
    "Block and tackle": {"weight": 5, "cost_cp": gp(5)},
    "Boots, soft": {"weight": 3, "cost_cp": gp(1)},
    "Boots, heavy": {"weight": 5, "cost_cp": gp(2)},
    "Caltrops": {"weight": 2, "cost_cp": gp(1)},
    "Candle": {"weight": 0, "cost_cp": cp(1)},
    "Cauldron and tripod": {"weight": 15, "cost_cp": gp(2)},
    "Chain (per 10ft)": {"weight": 10, "cost_cp": gp(30)},
    "Chalk": {"weight": 0, "cost_cp": cp(1)},
    "Cloak": {"weight": 1, "cost_cp": sp(3)},
    "Crowbar": {"weight": 5, "cost_cp": gp(2)},
    "Flask, leather": {"weight": 0, "cost_cp": cp(3)},
    "Flint and steel": {"weight": 0, "cost_cp": gp(1)},
    "Grappling hook": {"weight": 4, "cost_cp": gp(1)},
    "Hammer (tool)": {"weight": 2, "cost_cp": sp(5)},
    "Holy symbol, silver": {"weight": 1, "cost_cp": gp(25)},
    "Holy symbol, wooden": {"weight": 0.5, "cost_cp": sp(6)},
    "Iron spikes (dozen)": {"weight": 5, "cost_cp": gp(1)},
    "Ladder (per 10ft)": {"weight": 20, "cost_cp": sp(5)},
    "Lantern, bullseye": {"weight": 3, "cost_cp": gp(12)},
    "Lantern, hooded": {"weight": 2, "cost_cp": gp(7)},
    "Lock": {"weight": 0.5, "cost_cp": gp(20)},
    "Manacles": {"weight": 2, "cost_cp": gp(15)},
    "Mirror, small steel": {"weight": 0.5, "cost_cp": gp(20)},
    "Oil (lamp, per pint)": {"weight": 1, "cost_cp": sp(1)},
    "Parchment (sheet)": {"weight": 0, "cost_cp": sp(2)},
    "Piton": {"weight": 0.5, "cost_cp": sp(1)},
    "Pole (per 10ft)": {"weight": 8, "cost_cp": sp(2)},
    "Pot, iron": {"weight": 5, "cost_cp": sp(5)},
    "Quiver (12)": {"weight": 0, "cost_cp": gp(1)},
    "Rations, standard (day)": {"weight": 2, "cost_cp": gp(2)},   # as printed in 1.4.2.3A
    "Rations, trail (day)": {"weight": 1, "cost_cp": gp(6)},
    "Rope, hemp (50ft)": {"weight": 10, "cost_cp": gp(1)},
    "Rope, silk (50ft)": {"weight": 5, "cost_cp": gp(10)},
    "Sack, large": {"weight": 0, "cost_cp": cp(15)},
    "Sack, small": {"weight": 0, "cost_cp": cp(10)},
    "Scrollcase, leather": {"weight": 0.5, "cost_cp": gp(1)},
    "Shovel": {"weight": 8, "cost_cp": gp(2)},
    "Spell book (blank)": {"weight": 5, "cost_cp": gp(25)},
    "Tent": {"weight": 20, "cost_cp": gp(10)},
    "Thieves' tools": {"weight": 1, "cost_cp": gp(30)},
    "Torch": {"weight": 1, "cost_cp": cp(1)},
    "Waterskin": {"weight": 1, "cost_cp": gp(1)},
    "Holy water (vial)": {"weight": 0.5, "cost_cp": gp(25)},
    "Oil flask (for throwing)": {"weight": 1, "cost_cp": sp(1)},
}

# ---- Strength encumbrance allowance (lbs) -----------------------------
_STR_ALLOWANCE = {3: 0, 4: 10, 5: 10, 6: 20, 7: 20, 8: 35, 9: 35, 10: 35,
                  11: 35, 12: 45, 13: 45, 14: 55, 15: 55, 16: 70, 17: 85, 18: 110}
# Exceptional Strength (str 18 + percentile) brackets.
_EXC_ALLOWANCE = [(50, 135), (75, 160), (90, 185), (99, 235)]


def carry_allowance(str_score: int, str_pct: int = 0) -> int:
    """Max weight (lbs) carried without penalty, by Strength (Table 1.1.2A)."""
    s = int(str_score or 10)
    if s >= 19:
        return 300
    if s == 18 and str_pct:
        for top, lbs in _EXC_ALLOWANCE:
            if str_pct <= top:
                return lbs
        return 235
    return _STR_ALLOWANCE.get(max(3, min(s, 18)), 35)


# ---- encumbrance -> movement (Table 1.5.3.3A) -------------------------
# (max lbs over allowance, movement fraction, label)
_ENCUMBRANCE = [
    (0, 1.0, "Unencumbered"),
    (40, 0.75, "Lightly encumbered (3/4 move)"),
    (80, 0.5, "Encumbered (1/2 move)"),
    (120, 0.25, "Heavily encumbered (1/4 move)"),
]


def encumbrance_step(total_weight: float, allowance: int):
    """Return (fraction, label) for weight carried over the allowance."""
    over = total_weight - allowance
    if over <= 0:
        return 1.0, "Unencumbered"
    for top, frac, label in _ENCUMBRANCE[1:]:
        if over <= top:
            return frac, label
    return 0.0, "Overloaded (cannot move)"


# Base movement rate by ancestry (ft/round).
RACE_BASE_MOVE = {"Dwarf": 90, "Gnome": 90, "Halfling": 90,
                  "Human": 120, "Elf": 120, "Half-elf": 120, "Half-orc": 120}


def adjusted_move(base_move: int, total_weight: float, allowance: int,
                  armour_cap: Optional[int] = None) -> int:
    """Effective movement: base reduced by the encumbrance fraction, then
    capped by any armour movement cap (which is independent of weight)."""
    frac, _ = encumbrance_step(total_weight, allowance)
    move = int(math.floor(base_move * frac))
    if armour_cap is not None:
        move = min(move, armour_cap)
    return move


def lookup(name: str) -> Optional[Dict]:
    """Find an item in any catalog (case-insensitive). Returns a copy with a
    'category' and 'name' added, or None."""
    for cat, table in (("weapon", WEAPONS), ("armour", ARMOUR),
                       ("ammunition", AMMUNITION), ("gear", GEAR)):
        for key, val in table.items():
            if key.lower() == name.strip().lower():
                out = dict(val)
                out["name"] = key
                out["category"] = cat
                return out
    return None
