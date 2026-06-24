"""dice.py -- seeded dice for the OSRIC / Greyhawk engine.

D&D resolves actions with a spread of dice (d20, d100, d6, d8, ...). Unlike a
single module-global RNG, every roller here carries its OWN seeded
``random.Random``, so any procedure -- character creation above all -- can be
replayed deterministically from its seed plus the choices made. That seeded,
replayable pattern is exactly what made the Traveller game's chargen
restart-proof, and we carry it forward here.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import List, Optional

# Standard RPG dice notation: NdS+/-M  ("2d6", "d8", "1d6+1", "3D6 - 2").
_NOTATION = re.compile(r"^\s*(\d*)\s*[dD]\s*(\d+)\s*([+-]\s*\d+)?\s*$")


@dataclass
class RollResult:
    """A roll with its full breakdown, so the log can always show its work."""

    dice: List[int] = field(default_factory=list)   # the dice that COUNT
    sides: int = 6
    modifier: int = 0
    dropped: List[int] = field(default_factory=list)  # dice rolled but discarded

    @property
    def natural(self) -> int:
        return sum(self.dice)

    @property
    def total(self) -> int:
        return self.natural + self.modifier

    def __str__(self) -> str:
        mod = " {:+d}".format(self.modifier) if self.modifier else ""
        drop = " (dropped {})".format(self.dropped) if self.dropped else ""
        return "{}d{}{} -> {}{} = {}".format(
            len(self.dice), self.sides, mod, self.dice, drop, self.total)


class Dice:
    """A seeded dice roller. Same seed + same call sequence => same results."""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed if seed is not None else random.Random().randint(0, 2**31 - 1)
        self.rng = random.Random(self.seed)

    # ---- general rolling ----------------------------------------------
    def roll_detail(self, number: int = 1, sides: int = 6, modifier: int = 0) -> RollResult:
        if number < 0:
            raise ValueError("cannot roll a negative number of dice")
        if sides < 1:
            raise ValueError("dice must have at least one side")
        dice = [self.rng.randint(1, sides) for _ in range(number)]
        return RollResult(dice=dice, sides=sides, modifier=modifier)

    def roll(self, number: int = 1, sides: int = 6, modifier: int = 0) -> int:
        return self.roll_detail(number, sides, modifier).total

    def notation(self, text: str) -> RollResult:
        m = _NOTATION.match(text)
        if not m:
            raise ValueError("unrecognized dice notation: {!r}".format(text))
        count = int(m.group(1)) if m.group(1) else 1
        sides = int(m.group(2))
        modifier = int(m.group(3).replace(" ", "")) if m.group(3) else 0
        return self.roll_detail(count, sides, modifier)

    # ---- the usual platonic solids ------------------------------------
    def d(self, sides: int) -> int:
        return self.rng.randint(1, sides)

    def d4(self) -> int:   return self.rng.randint(1, 4)
    def d6(self) -> int:   return self.rng.randint(1, 6)
    def d8(self) -> int:   return self.rng.randint(1, 8)
    def d10(self) -> int:  return self.rng.randint(1, 10)
    def d12(self) -> int:  return self.rng.randint(1, 12)
    def d20(self) -> int:  return self.rng.randint(1, 20)
    def d100(self) -> int: return self.rng.randint(1, 100)

    # ---- ability-score generation methods -----------------------------
    # The drop-lowest variants return a RollResult whose `.dice` are the KEPT
    # dice (so .natural is the score) and whose `.dropped` records the discards.
    def ability_3d6(self) -> RollResult:
        return self.roll_detail(3, 6)

    def ability_4d6_drop_lowest(self) -> RollResult:
        return self._keep_best(4, keep=3)

    def ability_5d6_drop_two(self) -> RollResult:
        """'Hero mode' -- roll 5d6, keep the best 3."""
        return self._keep_best(5, keep=3)

    def _keep_best(self, number: int, keep: int, sides: int = 6) -> RollResult:
        rolled = [self.rng.randint(1, sides) for _ in range(number)]
        ordered = sorted(rolled, reverse=True)
        return RollResult(dice=ordered[:keep], sides=sides, dropped=ordered[keep:])


# A convenience default roller for ad-hoc, non-replayed rolls.
default = Dice()


def roll(number: int = 1, sides: int = 6, modifier: int = 0) -> int:
    return default.roll(number, sides, modifier)


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    d = Dice(seed=1)
    print("d20:", d.d20(), "| 3d6+1:", d.notation("3d6+1"))
    print("4d6-drop-lowest:", d.ability_4d6_drop_lowest())
    print("5d6-drop-two:", d.ability_5d6_drop_two())
