"""warmachine.py -- mass combat (a War Machine-style Battle Rating system).

The Rules Cyclopedia "War Machine" lets two armies fight as single units. Dark
Dungeons omits it, so this is our implementation of the same idea: each force
gets a Battle Rating from troop quality, size, training, leadership, special
troops, and fortification; both sides roll d100 + their rating; the margin
decides the victor, the casualties on each side, and whether the loser routs.

Deterministic from a seeded Dice. This is how a tyrant is unseated from without
(the within path is engine.domain Confidence: drive it to Turbulent and revolt).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .dice import Dice

# Training/experience modifier to the Battle Rating.
TROOP_CLASS = {"untrained": -20, "poor": -10, "average": 0, "good": 10,
               "excellent": 20, "elite": 30}


def _size_bonus(n: int) -> int:
    for ceiling, bonus in ((10, 0), (50, 5), (100, 10), (500, 15),
                           (1000, 20), (5000, 25)):
        if n < ceiling:
            return bonus
    return 30


def _leadership(level: int, cha: int) -> int:
    cha_mod = max(-3, min(5, (cha - 9) // 2))
    return min(25, max(0, level) + cha_mod)


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


@dataclass
class Force:
    name: str
    troops: int
    troop_hd: float = 1.0           # average Hit Dice per soldier
    troop_class: str = "average"    # training/experience
    leader_level: int = 0
    leader_cha: int = 10
    mounted: bool = False
    missile: bool = False
    spellcasters: int = 0
    fortified: bool = False         # defending a stronghold/prepared position

    def battle_rating(self, terrain_mod: int = 0) -> int:
        bfr = 30 + self.troop_hd * 5 + _size_bonus(self.troops)
        mods = TROOP_CLASS.get(self.troop_class.lower(), 0)
        mods += _leadership(self.leader_level, self.leader_cha)
        if self.mounted:
            mods += 10
        if self.missile:
            mods += 5
        if self.spellcasters:
            mods += min(20, self.spellcasters * 3)
        if self.fortified:
            mods += 25
        return round(bfr + mods + terrain_mod)


def resolve_battle(dice: Dice, attacker: Force, defender: Force,
                   attacker_terrain: int = 0, defender_terrain: int = 0
                   ) -> Dict[str, Any]:
    """Resolve one battle. Mutates each force's troop count by casualties."""
    a_br = attacker.battle_rating(attacker_terrain)
    d_br = defender.battle_rating(defender_terrain)
    a_total = dice.d100() + a_br
    d_total = dice.d100() + d_br

    if a_total >= d_total:
        winner, loser, margin = attacker, defender, a_total - d_total
    else:
        winner, loser, margin = defender, attacker, d_total - a_total

    loser_pct = _clamp(round(10 + margin * 0.4), 10, 95)
    winner_pct = _clamp(round(18 - margin * 0.12), 2, 25)
    rout = margin >= 50

    loser_cas = round(loser.troops * loser_pct / 100)
    winner_cas = round(winner.troops * winner_pct / 100)
    if rout:                                    # a rout adds to the loser's losses
        loser_cas = min(loser.troops, loser_cas + round(loser.troops * 0.2))

    winner.troops = max(0, winner.troops - winner_cas)
    loser.troops = max(0, loser.troops - loser_cas)

    return {
        "winner": winner.name, "loser": loser.name, "margin": margin,
        "rout": rout,
        "battle_ratings": {attacker.name: a_br, defender.name: d_br},
        "casualties": {winner.name: winner_cas, loser.name: loser_cas},
        "survivors": {attacker.name: attacker.troops, defender.name: defender.troops},
        "loser_destroyed": loser.troops == 0,
    }


def besiege(dice: Dice, attacker: Force, defender: Force,
            attacker_terrain: int = -10) -> Dict[str, Any]:
    """A siege/assault: the defender fights fortified; storming walls is costly
    for the attacker (terrain penalty)."""
    was_fortified = defender.fortified
    defender.fortified = True
    try:
        result = resolve_battle(dice, attacker, defender,
                                attacker_terrain=attacker_terrain)
    finally:
        defender.fortified = was_fortified
    result["siege"] = True
    return result
