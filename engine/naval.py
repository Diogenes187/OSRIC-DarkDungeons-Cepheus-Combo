"""naval.py -- ship-to-ship combat (the Cepheus ship-combat idea, fantasy seas).

A warship has a hull (structural points from its tonnage), a crew (which fights
as a War Machine Force when boarding), an optional ram, and shipboard artillery
(ballistae/catapults). A battle plays out over a few rounds: artillery and rams
chew the hull; crews board and fight; a ship is lost when its hull is breached
(sinks) or its crew is beaten (captured). Deterministic from a seeded Dice.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .dice import Dice
from . import warmachine
from . import vessels


@dataclass
class Warship:
    name: str
    tonnage: float
    crew: int
    crew_hd: float = 1.0
    crew_class: str = "average"
    ram: bool = False
    artillery: int = 0            # ballistae / catapults aboard
    leader_level: int = 0
    leader_cha: int = 10
    hull: int = 0

    def __post_init__(self):
        if not self.hull:
            self.hull = max(2, round(self.tonnage / 5))

    @property
    def afloat(self) -> bool:
        return self.hull > 0

    @property
    def manned(self) -> bool:
        return self.crew > 0

    def _force(self) -> "warmachine.Force":
        return warmachine.Force(self.name, self.crew, self.crew_hd,
                                self.crew_class, self.leader_level, self.leader_cha)


def from_vessel(name: str, vessel_type: str, crew: int, **kw) -> Warship:
    """Make a warship from a catalog vessel (its tonnage sets the hull)."""
    vt = vessels.get(vessel_type)
    tonnage = vt.capacity_tons if vt else float(kw.pop("tonnage", 20))
    kw.pop("tonnage", None)
    return Warship(name=name, tonnage=tonnage, crew=crew, **kw)


def _fate(ship: Warship) -> str:
    if not ship.afloat:
        return "sunk"
    if not ship.manned:
        return "captured"
    return "afloat"


def naval_battle(dice: Dice, a: Warship, b: Warship, ram_a: bool = True,
                 ram_b: bool = True, max_rounds: int = 6) -> Dict[str, Any]:
    """Resolve a ship-to-ship engagement. Mutates hull/crew on both ships."""
    log: List[str] = []
    rounds = 0
    for rnd in range(1, max_rounds + 1):
        rounds = rnd
        # 1) Artillery: each weapon hits on 11+ for 2d6 hull damage.
        for shooter, target in ((a, b), (b, a)):
            dmg = 0
            for _ in range(shooter.artillery):
                if dice.d20() >= 11:
                    dmg += dice.notation("2d6").total
            if dmg:
                target.hull -= dmg
                log.append("R{}: {} artillery hits {} for {} hull".format(
                    rnd, shooter.name, target.name, dmg))
        # 2) Ramming: hits on 12+ for tonnage-scaled damage (rammer takes some).
        for rammer, target, do in ((a, b, ram_a), (b, a, ram_b)):
            if do and rammer.ram and dice.d20() >= 12:
                d = round(rammer.tonnage / 20) + dice.d6()
                target.hull -= d
                rammer.hull -= max(1, round(d / 3))
                log.append("R{}: {} rams {} for {} hull".format(
                    rnd, rammer.name, target.name, d))
        if not a.afloat or not b.afloat:
            break
        # 3) Boarding: crews fight as War Machine forces.
        fa, fb = a._force(), b._force()
        res = warmachine.resolve_battle(dice, fa, fb)
        a.crew, b.crew = fa.troops, fb.troops
        log.append("R{}: boarding -> {} prevails on deck".format(rnd, res["winner"]))
        if not a.manned or not b.manned:
            break

    if not a.afloat or not a.manned:
        winner, loser = b, a
    elif not b.afloat or not b.manned:
        winner, loser = a, b
    else:                                       # both survive: stronger holds the sea
        winner = a if (a.hull + a.crew) >= (b.hull + b.crew) else b
        loser = b if winner is a else a

    return {"winner": winner.name, "loser": loser.name,
            "loser_fate": _fate(loser), "rounds": rounds, "log": log,
            "ships": {a.name: {"hull": a.hull, "crew": a.crew},
                      b.name: {"hull": b.hull, "crew": b.crew}}}
