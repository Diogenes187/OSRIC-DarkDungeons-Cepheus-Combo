"""conditions.py -- OSRIC 3.0 data for combat conditions.

  Table 1.6.4A   Item Saving Throws (by material vs attack form)
  Section 1.6.7  Life Energy / Level Drain
  Section 1.6.9  Poison, Disease
  Tables 1.6.12A/B/C  Unarmed To-Hit, Overbearing, Grappling
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# ---- item saving throws (Table 1.6.4A) --------------------------------
# A material saves on d20 >= the listed number for the attack form.
ITEM_ATTACKS = ("acid", "cold", "crushing", "disintegrate", "fall",
                "fire_magical", "fire_normal", "lightning")

ITEM_SAVES: Dict[str, List[int]] = {
    # material: [acid, cold, crushing, disintegrate, fall, fire_mag, fire_norm, lightning]
    "crystal":   [5, 5, 19, 20, 10, 5, 3, 15],
    "glass":     [5, 5, 19, 20, 10, 5, 3, 15],
    "leather":   [10, 3, 4, 20, 1, 6, 4, 13],
    "metal":     [7, 1, 6, 20, 1, 2, 1, 11],
    "paper":     [16, 2, 11, 20, 1, 20, 18, 20],
    "pottery":   [10, 3, 17, 20, 5, 6, 3, 5],
    "bone":      [10, 3, 17, 20, 5, 6, 3, 5],
    "rope":      [12, 1, 10, 20, 1, 15, 10, 14],
    "cloth":     [12, 1, 10, 20, 1, 15, 10, 14],
    "stone":     [3, 1, 17, 18, 1, 2, 1, 14],
    "gem":       [3, 1, 17, 18, 1, 2, 1, 14],
    "wood":      [10, 1, 10, 20, 2, 7, 5, 10],
}

ITEM_ATTACK_ALIASES = {
    "acid": "acid", "corrosion": "acid",
    "cold": "cold", "frost": "cold", "ice": "cold",
    "crushing": "crushing", "crush": "crushing", "crushing blow": "crushing",
    "disintegrate": "disintegrate", "disintegration": "disintegrate",
    "fall": "fall", "falling": "fall",
    "fire": "fire_magical", "fireball": "fire_magical", "fire_magical": "fire_magical",
    "magical fire": "fire_magical", "dragon breath": "fire_magical",
    "normal fire": "fire_normal", "fire_normal": "fire_normal", "flame": "fire_normal",
    "lightning": "lightning", "electricity": "lightning", "shock": "lightning",
}


def item_save_target(material: str, attack: str) -> int:
    mat = ITEM_SAVES.get((material or "").strip().lower())
    atk = ITEM_ATTACK_ALIASES.get((attack or "").strip().lower())
    if mat is None or atk is None:
        return 0
    return mat[ITEM_ATTACKS.index(atk)]


# ---- unarmed combat ---------------------------------------------------
def unarmed_tohit_target(ac_descending: int) -> int:
    """Target number to land an unarmed (grapple/overbear) attack, from the
    defender-as-attacker armour table: 2 at AC 10, +2 per point better, cap 22."""
    return max(2, min(2 + 2 * (10 - int(ac_descending)), 22))


def attacker_move_mod(move: int) -> int:
    if move < 30:
        return 0
    return min((int(move) // 30) * 2, 10)


def defender_move_mod(move: int) -> int:
    if move < 30:
        return 0
    return -min((int(move) // 30) * 2, 10)


def defender_armour_mod(ac_descending: int) -> int:
    ac = int(ac_descending)
    if ac >= 10:
        return 0
    return {9: 0, 8: 2, 7: 2, 6: 2, 5: 4, 4: 4, 3: 5, 2: 5, 1: 5}.get(ac, 7)


SIZE_ATTACKER_MOD = {"tiny": -4, "small": -2, "medium": 0, "large": 2,
                     "huge": 6, "gargantuan": 10}
SIZE_DEFENDER_MOD = {"tiny": 4, "small": 2, "medium": 0, "large": -2,
                     "huge": -6, "gargantuan": -10}

# Overbearing results (d6 + mods): threshold -> (name, real_damage_is_die_minus, ...)
def overbearing_result(total: int) -> Dict[str, object]:
    if total <= 1:
        return {"result": "Total Failure", "prone_target": False,
                "prone_attacker": True, "real": 0, "followup": False}
    if total == 2:
        return {"result": "Partial Failure", "prone_target": False,
                "prone_attacker": True, "real": 0, "followup": False,
                "note": "Attacker clutches target's feet; may grip (target move -30)."}
    if total <= 4:
        return {"result": "Partial Success", "prone_target": False,
                "overborne": True, "real": 0, "followup": True}
    if total <= 6:
        return {"result": "Success", "prone_target": True, "overborne": True,
                "real": 1, "followup": True}
    return {"result": "Total Success", "prone_target": True, "overborne": True,
            "real": 2, "followup": True, "bonus_grapple": 2,
            "note": "Target may take no action next round."}


# Grappling results (d8 + mods): die -> (controlling hold, total dmg, real dmg)
def grappling_result(total: int) -> Dict[str, object]:
    if total <= 1:
        return {"hold": "Awkward Scuffling", "damage": 1, "real": 0, "grappling": False}
    if total <= 4:
        d = max(2, min(total, 4))
        return {"hold": "Arm Grab", "inferior": "Elbow Bash", "damage": d,
                "real": 1, "grappling": True}
    if total == 5:
        return {"hold": "Waist Lock", "inferior": "Leg Hold", "damage": 5,
                "real": 1, "grappling": True}
    if total == 6:
        return {"hold": "Rear Choke", "inferior": "Head Butt", "damage": 6,
                "real": 2, "grappling": True,
                "note": "Held target cannot shout or cast spells."}
    if total == 7:
        return {"hold": "Arm Lock", "inferior": "Wicked Elbow Bash", "damage": 7,
                "real": 2, "grappling": True, "can_prone": True}
    if total == 8:
        return {"hold": "Head Lock", "inferior": "Gouge", "damage": 8,
                "real": 2, "grappling": True, "can_prone": True}
    return {"hold": "Decisive Throw", "damage": 9, "real": 3, "grappling": True,
            "note": "Target loses their next action."}


# ---- disease (Section 1.6.9.2) ----------------------------------------
DISEASE_ONSET_DICE = (2, 8)       # 2d8 days (hours for infected wounds)
DISEASE_DURATION_DICE = (2, 8)    # 2d8 days
DISEASE_PENALTY_DIE = 6           # -1d6 to all characteristics and rolls
