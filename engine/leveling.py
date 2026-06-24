"""leveling.py -- experience, level gain, and hit-point growth.

The engine owns advancement. Award XP through grant_xp; it splits the award
across a multi-class character's classes (OSRIC: "divide it up equally"), looks
each class's new level up in the advancement tables, and rolls the resulting
hit-point growth on the seeded Dice so it is deterministic and replayable.

Multi-class characters fight and save as the BEST of their classes (lowest THAC0,
lowest save target), and their hit points grow at the AVERAGE of their classes'
gains -- the classic 1e trade-off, made mechanical.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .data import advancement as adv
from .data import attack as attack_mod
from .data import saves as saves_mod
from .data import abilities as ab
from .data import classes as classes_mod

WARRIORS = ("Fighter", "Paladin", "Ranger")


# ---- class lists --------------------------------------------------------
def normalize(classes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure each class entry has class/level/xp. Level is taken as the higher
    of any explicitly stored level and the level the XP earns -- so XP drives PC
    advancement, while a directly-set level (e.g. a spawned monster's HD with 0
    XP) is still honoured."""
    out = []
    for c in classes or []:
        name = c.get("class")
        if name not in adv.XP_NEEDED:
            continue
        xp = int(c.get("xp", 0) or 0)
        explicit = int(c.get("level", 1) or 1)
        # When training is required, a class's usable level is frozen at its
        # trained_level until the character trains -- XP can run ahead of it.
        trained = c.get("trained_level")
        if trained is not None:
            level = int(trained)
        else:
            level = max(explicit, adv.level_for_xp(name, xp))
        entry = {"class": name, "xp": xp, "level": level}
        if trained is not None:
            entry["trained_level"] = int(trained)
        if c.get("suppressed"):                 # a dual-classed character's old
            entry["suppressed"] = True          # class, not yet usable
        out.append(entry)
    return out


def active(classes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Classes that currently count for combat and saves -- a dual-classed
    character's suppressed old class is excluded until it is regained."""
    live = [c for c in classes if not c.get("suppressed")]
    return live or classes


def effective_level(classes: List[Dict[str, Any]]) -> int:
    return max((int(c.get("level", 1)) for c in classes), default=1)


# ---- best-of-class combat and saves ------------------------------------
def best_thac0(classes: List[Dict[str, Any]]) -> int:
    cs = active(classes)
    return min((attack_mod.thac0(c["class"], int(c["level"])) for c in cs),
               default=20)


def best_attack_bonus(classes: List[Dict[str, Any]]) -> int:
    return 20 - best_thac0(classes)


def best_save_target(classes: List[Dict[str, Any]], category: str) -> int:
    cs = active(classes)
    return min((saves_mod.save_target(c["class"], int(c["level"]), category)
                for c in cs), default=20)


# ---- experience and hit points -----------------------------------------
def _hp_for_gain(dice, cls: str, new_level: int, con_mod: int, divisor: int) -> int:
    """HP gained for reaching `new_level` in `cls`. Rolls a Hit Die (plus the
    Constitution modifier) up to the class's HD cap; a fixed amount beyond it.
    Divided by `divisor` for multi-class averaging, minimum 1."""
    if new_level <= adv.hd_max_level(cls):
        gain = dice.d(classes_mod.get(cls).hit_die) + con_mod
    else:
        gain = adv.hp_after(cls)                 # no Con bonus past the HD cap
    if divisor > 1:
        gain = gain // divisor
    return max(1, gain)


def grant_xp(dice, classes: List[Dict[str, Any]], amount: int, con: int,
             prime_bonus: bool = False) -> Dict[str, Any]:
    """Award `amount` XP to a character. Returns the updated class list, total
    hp gained, and any level-ups. `prime_bonus` applies the +10% before the
    split. The award is divided equally among multi-classed characters."""
    classes = normalize(classes)
    if not classes:
        return {"classes": [], "hp_gained": 0, "level_ups": [], "xp_each": 0}

    total = int(round(amount * (1.1 if prime_bonus else 1.0)))
    n = len(classes)
    each = total // n
    warrior = any(c["class"] in WARRIORS for c in classes)
    con_mod = ab.constitution_mods(con, warrior=warrior)["hp_mod"]

    hp_gained = 0
    level_ups: List[Dict[str, Any]] = []
    for c in classes:
        old_level = c["level"]
        c["xp"] = c["xp"] + each
        new_level = adv.level_for_xp(c["class"], c["xp"])
        for lvl in range(old_level + 1, new_level + 1):
            hp_gained += _hp_for_gain(dice, c["class"], lvl, con_mod, n)
        if new_level != old_level:
            level_ups.append({"class": c["class"], "from": old_level,
                              "to": new_level})
        c["level"] = new_level
    return {"classes": classes, "hp_gained": hp_gained, "level_ups": level_ups,
            "xp_each": each}


def grant_xp_dual(dice, classes: List[Dict[str, Any]], amount: int, con: int,
                  from_class: str, from_level: int, to_class: str) -> Dict[str, Any]:
    """Award XP to a dual-classed character: ALL of it goes to the new class.
    No hit points are gained until the new class passes the old class's level;
    once it does, the old class's abilities (and combat/saves) are regained."""
    classes = normalize(classes)
    warrior = to_class in WARRIORS
    con_mod = ab.constitution_mods(con, warrior=warrior)["hp_mod"]
    hp_gained = 0
    level_ups: List[Dict[str, Any]] = []
    regained = False
    for c in classes:
        if c["class"] != to_class:
            continue
        old_level = c["level"]
        c["xp"] = c["xp"] + int(amount)
        new_level = adv.level_for_xp(to_class, c["xp"])
        for lvl in range(old_level + 1, new_level + 1):
            if lvl > from_level:                # HP only past the old class level
                hp_gained += _hp_for_gain(dice, to_class, lvl, con_mod, 1)
        if new_level != old_level:
            level_ups.append({"class": to_class, "from": old_level, "to": new_level})
        c["level"] = new_level
        if new_level > from_level:              # old class abilities return
            regained = True
    if regained:
        for c in classes:
            if c["class"] == from_class and c.get("suppressed"):
                c.pop("suppressed", None)
    return {"classes": classes, "hp_gained": hp_gained, "level_ups": level_ups,
            "regained_old_class": regained}


def bank_xp(classes: List[Dict[str, Any]], amount: int,
            prime_bonus: bool = False) -> Dict[str, Any]:
    """Award XP WITHOUT applying the level (training required). XP accrues but each
    class's usable level stays frozen at its trained_level; returns which classes
    are now eligible to train."""
    valid = [c for c in classes if c.get("class") in adv.XP_NEEDED]
    n = len(valid) or 1
    each = int(round(amount * (1.1 if prime_bonus else 1.0))) // n
    out, ready = [], []
    for c in classes:
        name = c.get("class")
        if name not in adv.XP_NEEDED:
            out.append(c)
            continue
        xp = int(c.get("xp", 0) or 0) + each
        trained = int(c.get("trained_level", c.get("level", 1) or 1))
        entry = {"class": name, "xp": xp, "level": trained, "trained_level": trained}
        if c.get("suppressed"):
            entry["suppressed"] = True
        earned = adv.level_for_xp(name, xp)
        if earned > trained:
            ready.append({"class": name, "trained": trained, "earned": earned})
        out.append(entry)
    return {"classes": out, "xp_each": each, "ready_to_train": ready}


def train(dice, classes: List[Dict[str, Any]], char_class: str, con: int
          ) -> Dict[str, Any]:
    """Train up ONE level in char_class (the XP must already be earned). Rolls the
    new level's hit points; the caller charges the gold and time."""
    out = [dict(c) for c in classes]
    for c in out:
        if c.get("class") != char_class:
            continue
        trained = int(c.get("trained_level", c.get("level", 1) or 1))
        earned = adv.level_for_xp(char_class, int(c.get("xp", 0) or 0))
        if earned <= trained:
            return {"error": "{} hasn't earned enough XP to train".format(char_class)}
        new_level = trained + 1
        warrior = char_class in WARRIORS
        con_mod = ab.constitution_mods(con, warrior=warrior)["hp_mod"]
        hp = _hp_for_gain(dice, char_class, new_level, con_mod, 1)
        c["trained_level"] = new_level
        c["level"] = new_level
        return {"classes": out, "class": char_class, "from": trained,
                "to": new_level, "hp_gained": hp}
    return {"error": "{} is not one of this character's classes".format(char_class)}


def xp_to_next(classes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """For each class: current level, xp, and XP remaining to the next level
    (None if the class is at its ceiling)."""
    out = []
    for c in normalize(classes):
        cap = adv.max_level(c["class"])
        if cap is not None and c["level"] >= cap:
            need = None
        else:
            need = adv.xp_for_level(c["class"], c["level"] + 1) - c["xp"]
        out.append({"class": c["class"], "level": c["level"], "xp": c["xp"],
                    "to_next": need})
    return out
