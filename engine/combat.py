"""combat.py -- OSRIC 3.0 combat resolution (deterministic, seeded).

Attack resolution uses the ascending-AC identity (see engine.data.attack):

    hit if  d20 + attack_bonus + STR-to-hit + situational  >=  ascending AC
    natural 20 always hits; natural 1 always misses.

Both AC scales are tracked so the table can be shown either way. Initiative and a
2d6 morale check round out a first combat core; saving throws come next.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .dice import Dice
from .data import abilities as ab
from .data import attack as atk
from .data import saves as sv
from . import leveling

WARRIORS = ("Fighter", "Paladin", "Ranger")


def asc_from_desc(desc: int) -> int:
    return 20 - desc


def desc_from_asc(asc: int) -> int:
    return 20 - asc


@dataclass
class Combatant:
    name: str
    hp: int
    hp_max: int
    ac_descending: int = 10
    attack_bonus: int = 0
    to_hit_mod: int = 0       # e.g. STR (melee)
    damage_mod: int = 0       # e.g. STR (melee)
    damage_dice: str = "1d6"
    morale: int = 8           # 2d6 target; <= holds
    is_pc: bool = False
    alive: bool = True

    @property
    def ac_ascending(self) -> int:
        return asc_from_desc(self.ac_descending)


def combatant_from_row(row: Dict[str, Any], damage_dice: str = "1d6") -> Combatant:
    """Build a Combatant from a saved character row (dict / sqlite Row)."""
    classes = json.loads(row["classes_json"] or "[]") if "classes_json" in row.keys() \
        else row.get("classes", [])
    # Multi-class fights as the BEST of its classes (lowest THAC0 -> highest
    # attack bonus). Falls back to Fighter/1 for class-less rows.
    norm = leveling.normalize(classes)
    if norm:
        attack_bonus = leveling.best_attack_bonus(norm)
    else:
        attack_bonus = atk.attack_bonus("Fighter", 1)
    smods = ab.strength_mods(row["str_score"], row["str_pct"] or 0)
    # A stored damage_dice (e.g. a spawned monster's listed damage) wins over the
    # default; monsters carry their own damage and no STR bonus.
    stored = row["damage_dice"] if "damage_dice" in row.keys() else None
    return Combatant(
        name=row["name"],
        hp=row["hp_current"] if row["hp_current"] is not None else row["hp_max"],
        hp_max=row["hp_max"],
        ac_descending=row["ac_descending"] if row["ac_descending"] is not None else 10,
        attack_bonus=attack_bonus,
        to_hit_mod=smods["to_hit"],    # STR applies to melee to-hit for anyone
        damage_mod=smods["damage"],
        damage_dice=stored or damage_dice,
        is_pc=not bool(row["is_npc"]) if "is_npc" in row.keys() else True,
    )


def resolve_attack(attacker: Combatant, defender: Combatant, dice: Dice,
                   situational: int = 0,
                   damage_dice: Optional[str] = None) -> Dict[str, Any]:
    """Resolve one melee attack. Mutates defender.hp on a hit."""
    nat = dice.d20()
    total = nat + attacker.attack_bonus + attacker.to_hit_mod + situational
    if nat == 1:
        hit = False
    elif nat == 20:
        hit = True
    else:
        hit = total >= defender.ac_ascending

    result = {"attacker": attacker.name, "defender": defender.name,
              "natural": nat, "total": total, "target_ac": defender.ac_descending,
              "hit": hit, "damage": 0, "defender_hp": defender.hp,
              "defender_down": False}
    if hit:
        dmg = dice.notation(damage_dice or attacker.damage_dice).total \
            + attacker.damage_mod
        dmg = max(1, dmg)
        defender.hp -= dmg
        result["damage"] = dmg
        result["defender_hp"] = defender.hp
        if defender.hp <= 0:
            defender.alive = False
            result["defender_down"] = True
    return result


def saving_throw(dice: Dice, char_class: str, level: int, category: str,
                 modifier: int = 0) -> Dict[str, Any]:
    """Roll a saving throw. Succeeds on d20 + modifier >= the class/level target.

    `category` is one of engine.data.saves.CATEGORIES. `modifier` carries ability
    bonuses (e.g. Wisdom mental save vs spells, Dexterity agility save vs breath/
    area effects) and ancestry (e.g. dwarf/halfling/gnome Stalwart) bonuses.
    """
    target = sv.save_target(char_class, level, category)
    nat = dice.d20()
    total = nat + modifier
    return {"category": category, "natural": nat, "modifier": modifier,
            "total": total, "target": target, "success": total >= target}


def saving_throw_classes(dice: Dice, classes, category: str,
                         modifier: int = 0) -> Dict[str, Any]:
    """Saving throw for a (possibly multi-class) character: uses the BEST (lowest)
    save target across all the character's classes at their levels."""
    norm = leveling.normalize(classes)
    target = leveling.best_save_target(norm, category) if norm \
        else sv.save_target("Fighter", 1, category)
    nat = dice.d20()
    total = nat + modifier
    return {"category": category, "natural": nat, "modifier": modifier,
            "total": total, "target": target, "success": total >= target}


def roll_initiative(dice: Dice) -> int:
    """OSRIC initiative: 1d6 per side; the LOWER result acts first."""
    return dice.d6()


def morale_check(dice: Dice, morale: int) -> Dict[str, Any]:
    """2d6 morale check (Dark Dungeons style): roll <= morale to hold."""
    roll = dice.d6() + dice.d6()
    return {"roll": roll, "morale": morale, "holds": roll <= morale}
