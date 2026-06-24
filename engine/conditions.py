"""conditions.py -- resolve OSRIC combat conditions (deterministic, seeded).

Poison and disease (save vs poison), energy/level drain, item saving throws, and
unarmed grappling/overbearing. Each rolls on the seeded Dice so a nasty moment
replays identically.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .data import conditions as C
from .data import advancement as adv
from . import leveling


# ---- poison -----------------------------------------------------------
def poison_save(dice, save_target: int, modifier: int = 0,
                on_fail_damage: Optional[str] = None,
                on_success_damage: Optional[str] = None) -> Dict[str, Any]:
    """Save vs poison (the death/paralysis/poison category). By default a failed
    save is fatal; pass damage notations for poisons that wound instead of kill."""
    nat = dice.d20()
    total = nat + int(modifier)
    saved = total >= save_target
    out = {"natural": nat, "total": total, "target": save_target, "saved": saved}
    if saved:
        out["result"] = "survived"
        out["damage"] = dice.notation(on_success_damage).total if on_success_damage else 0
    else:
        if on_fail_damage:
            out["result"] = "wounded"
            out["damage"] = dice.notation(on_fail_damage).total
        else:
            out["result"] = "dead"
            out["damage"] = None
    return out


# ---- disease ----------------------------------------------------------
def disease_check(dice, save_target: int, modifier: int = 0,
                  in_hours: bool = False) -> Dict[str, Any]:
    """Plague/infection: save vs poison to avoid. On failure, incubate 2d8, then
    suffer -1d6 to all stats/rolls for 2d8 (the disease is fatal if either onset
    or duration die rolled an 8)."""
    nat = dice.d20()
    saved = (nat + int(modifier)) >= save_target
    if saved:
        return {"natural": nat, "saved": True, "contracted": False,
                "note": "Future saves vs this disease are at +4."}
    o1, o2 = dice.d(8), dice.d(8)
    d1, d2 = dice.d(8), dice.d(8)
    penalty = dice.d(C.DISEASE_PENALTY_DIE)
    fatal = 8 in (o1, o2, d1, d2)
    unit = "hours" if in_hours else "days"
    return {"natural": nat, "saved": False, "contracted": True,
            "onset": o1 + o2, "onset_unit": unit,
            "penalty": -penalty, "duration": d1 + d2, "duration_unit": unit,
            "fatal": fatal,
            "note": "Dies at the end of the illness." if fatal else
                    "Recovers 1 point per day after the illness runs its course."}


# ---- level (energy) drain --------------------------------------------
def drain_levels(classes: List[Dict[str, Any]], levels: int = 1) -> Dict[str, Any]:
    """Drain `levels` life-energy levels. Each drain removes the character's
    highest class level, dropping them to the start of the new level. Draining
    below 1st level slays the character."""
    cls = leveling.normalize(classes)
    lost = []
    slain = False
    for _ in range(max(1, int(levels))):
        if not cls:
            break
        # highest current level (ties: first one)
        top = max(cls, key=lambda c: c["level"])
        new_level = top["level"] - 1
        lost.append({"class": top["class"], "from": top["level"], "to": new_level})
        if new_level < 1:
            slain = True
            break
        top["level"] = new_level
        top["xp"] = adv.xp_for_level(top["class"], new_level)
    return {"classes": cls, "levels_lost": lost, "slain": slain}


# ---- item saving throws ----------------------------------------------
def item_save(dice, material: str, attack: str, magic_bonus: int = 0) -> Dict[str, Any]:
    """An item's save vs a destructive effect (only rolled when its bearer has
    already failed their own save). Magical items get +2, plus their numeric
    plus: a +1 item is +3, a +2 item is +4, and so on."""
    target = C.item_save_target(material, attack)
    if target == 0:
        return {"error": "unknown material or attack form"}
    bonus = int(magic_bonus)
    if bonus > 0:
        bonus += 2                      # magical items: +2 plus their plus-1
    nat = dice.d20()
    total = nat + bonus
    return {"material": material.lower(), "attack": attack.lower(),
            "target": target, "natural": nat, "bonus": bonus, "total": total,
            "saved": total >= target,
            "result": "survives" if total >= target else "destroyed"}


# ---- unarmed: grappling & overbearing --------------------------------
def _result_mods(dice, atk: Dict[str, Any], dfn: Dict[str, Any]):
    """Strength/size/legs modifiers for the result tables."""
    def str_mod(s, hd, sign):
        v = 0
        if (s and s >= 16) or (hd and 4 <= hd <= 8):
            v = 1
        if (s and s > 18) or (hd and hd >= 9):      # 18.01+ Strength, or 9+ HD
            v = 2
        return v * sign
    am = str_mod(atk.get("str"), atk.get("hd"), 1)
    am += C.SIZE_ATTACKER_MOD.get(atk.get("size", "medium"), 0)
    if atk.get("four_legs"):
        am += 2
    dm = str_mod(dfn.get("str"), dfn.get("hd"), -1)
    dm += C.SIZE_DEFENDER_MOD.get(dfn.get("size", "medium"), 0)
    return am, dm


def unarmed_attack(dice, mode: str, attacker: Dict[str, Any],
                   defender: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve one grapple or overbear attempt. attacker/defender are dicts with
    ac, dex, str, move, hd, size, four_legs (all optional). Returns the to-hit
    and, on a hit, the result-table outcome with real/temporary damage."""
    target = C.unarmed_tohit_target(defender.get("ac", 10))
    mod = 0
    if (attacker.get("dex") or 0) >= 19:
        mod += 2
    elif (attacker.get("dex") or 0) >= 15:
        mod += 1
    mod += C.attacker_move_mod(attacker.get("move", 0))
    mod += C.defender_move_mod(defender.get("move", 0))
    mod += C.defender_armour_mod(defender.get("ac", 10))
    nat = dice.d20()
    hit = nat != 1 and (nat + mod) >= target
    out = {"mode": mode, "target": target, "natural": nat, "modifier": mod,
           "to_hit_total": nat + mod, "hit": hit}
    if not hit:
        out["result"] = "miss"
        return out

    am, dm = _result_mods(dice, attacker, defender)
    if mode.startswith("over"):
        roll = dice.d6()
        total = roll + am + dm
        res = C.overbearing_result(total)
        out.update({"roll": roll, "result_total": total})
        out.update(res)
        str_dmg = max(0, attacker.get("str_damage", 0))
        out["real_damage"] = res.get("real", 0) + (str_dmg if res.get("real") else 0)
    else:
        roll = dice.d(8)
        total = roll + am + dm
        res = C.grappling_result(total)
        out.update({"roll": roll, "result_total": total})
        out.update(res)
        dmg = res["damage"]
        real = res["real"]
        out["real_damage"] = real
        out["temp_damage"] = max(0, dmg - real)
    return out
