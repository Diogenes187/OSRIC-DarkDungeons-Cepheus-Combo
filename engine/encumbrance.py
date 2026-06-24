"""encumbrance.py -- total a character's carried weight and find their movement.

Gear is stored on a character as a JSON list. Entries may be either:
  * a plain string -- a free-text item; if it names a catalog item we use that
    weight, otherwise it weighs nothing for game purposes, or
  * a dict {item, qty, weight} -- added through add_equipment, carrying its own
    weight so the catalog isn't needed again.

Coins count too: 10 coins = 1 lb (OSRIC). A purse of gold is real weight.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .data import equipment as eq


def item_weight(entry: Any) -> float:
    """Weight (lbs) of one gear entry, looking it up in the catalog if needed."""
    if isinstance(entry, dict):
        w = entry.get("weight")
        qty = entry.get("qty", 1) or 1
        if w is None:
            found = eq.lookup(str(entry.get("item", "")))
            w = found.get("weight", 0) if found else 0
        return float(w or 0) * float(qty)
    found = eq.lookup(str(entry))
    return float(found.get("weight", 0) or 0) if found else 0.0


def gear_weight(gear: List[Any]) -> float:
    return round(sum(item_weight(g) for g in gear or []), 2)


def coin_weight(gold: int) -> float:
    """A character's coins as weight: 10 coins to the pound."""
    return round(float(gold or 0) / 10.0, 2)


def worn_armour(gear: List[Any]) -> Optional[Dict]:
    """The heaviest body armour (not a shield) among a character's gear, if any
    -- used for the movement cap."""
    best = None
    for g in gear or []:
        name = g.get("item") if isinstance(g, dict) else g
        found = eq.lookup(str(name or ""))
        if found and found["category"] == "armour" and found.get("move_cap"):
            if best is None or found["weight"] > best["weight"]:
                best = found
    return best


def assess(gear: List[Any], gold: int, str_score: int, str_pct: int,
           race: str, base_move: Optional[int] = None) -> Dict[str, Any]:
    """Full encumbrance read-out for a character."""
    g_w = gear_weight(gear)
    c_w = coin_weight(gold)
    total = round(g_w + c_w, 2)
    allowance = eq.carry_allowance(str_score, str_pct)
    frac, label = eq.encumbrance_step(total, allowance)
    armour = worn_armour(gear)
    cap = armour["move_cap"] if armour else None
    base = base_move if base_move is not None else eq.RACE_BASE_MOVE.get(race or "Human", 120)
    move = eq.adjusted_move(base, total, allowance, cap)
    return {
        "gear_weight": g_w, "coin_weight": c_w, "total_weight": total,
        "allowance": allowance, "over_allowance": round(max(0.0, total - allowance), 2),
        "fraction": frac, "encumbrance": label,
        "base_move": base, "armour_cap": cap,
        "armour": armour["name"] if armour else None,
        "movement_rate": move,
    }
