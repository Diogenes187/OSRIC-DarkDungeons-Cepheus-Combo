"""monsters.py -- the OSRIC bestiary, loaded from the extracted stat blocks.

`reference/osric_text/monsters.txt` is produced by scripts/extract_monsters.py
from the Gamemaster Guide. This module parses it into a queryable bestiary and
provides the bits combat needs: rolled hit points, primary damage, and the
monster's attack bonus (monsters attack on the fighter matrix by Hit Dice).

Full monster descriptions and special abilities stay in the GM Guide / corpus
for the referee to look up; here we carry the combat-relevant spine.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import List, Optional

from ..dice import Dice
from . import attack as atk

_HERE = os.path.dirname(os.path.abspath(__file__))
MONSTER_FILE = os.path.normpath(
    os.path.join(_HERE, "..", "..", "reference", "osric_text", "monsters.txt"))

_AC = re.compile(r"(-?\d+)\s*\[\s*(-?\d+)\s*\]")
_DAMAGE = re.compile(r"(\d*d\d+(?:\s*[+\-]\s*\d+)?)")
_HD_LEAD = re.compile(r"^\s*(\d+)")


@dataclass
class Monster:
    name: str
    hit_dice: str
    ac_descending: int
    ac_ascending: int
    attacks: str
    morale: str
    size: str
    no_encountered: str
    xp: str
    intelligence: str
    alignment: str
    move: str

    @property
    def hd_value(self) -> int:
        """A whole-number Hit Dice value, for the attack matrix."""
        m = _HD_LEAD.match(self.hit_dice)
        if m:
            return max(1, int(m.group(1)))
        # forms like "1d8-1 hit points" -> ~1 HD
        m = re.match(r"^\s*(\d+)d", self.hit_dice)
        return int(m.group(1)) if m else 1

    @property
    def attack_bonus(self) -> int:
        # Monsters hit as a fighter of level == Hit Dice.
        return atk.attack_bonus("Fighter", self.hd_value)

    def primary_damage(self) -> str:
        m = _DAMAGE.search(self.attacks or "")
        return m.group(1).replace(" ", "") if m else "1d6"

    def roll_hp(self, dice: Dice) -> int:
        return roll_hp(dice, self)


def _title(name: str) -> str:
    return name.title().replace("’", "'")


def _parse_line(line: str) -> Optional[Monster]:
    p = [x.strip() for x in line.split("|")]
    if len(p) < 11:
        p += [""] * (11 - len(p))
    name, hd, ac, atk_s, mor, size, noenc, xp, intel, align, move = p[:11]
    if not name or not hd:
        return None
    if ac.count("[") > 1 or hd.count("d") > 1 and " " in hd.strip():
        return None  # skip multi-variant blocks (e.g. the Horse table)
    m = _AC.search(ac)
    if not m:
        return None
    return Monster(name=_title(name), hit_dice=hd,
                   ac_descending=int(m.group(1)), ac_ascending=int(m.group(2)),
                   attacks=atk_s, morale=mor, size=size, no_encountered=noenc,
                   xp=xp, intelligence=intel, alignment=align, move=move)


def _load() -> List[Monster]:
    out: List[Monster] = []
    seen = set()
    if os.path.exists(MONSTER_FILE):
        with open(MONSTER_FILE, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                mon = _parse_line(line)
                if mon and mon.name.lower() not in seen:
                    out.append(mon)
                    seen.add(mon.name.lower())
    # Curated supplement: monsters the column-format blocks lost.
    from .monsters_extra import EXTRA
    for line in EXTRA:
        mon = _parse_line(line)
        if mon and mon.name.lower() not in seen:
            out.append(mon)
            seen.add(mon.name.lower())
    return out


BESTIARY: List[Monster] = _load()
_BY_NAME = {m.name.lower(): m for m in BESTIARY}


def roll_hp(dice: Dice, monster: Monster) -> int:
    """Roll a monster's hit points from its Hit Dice string (monsters use d8)."""
    s = monster.hit_dice.lower().replace("hit points", "").replace("hp", "").strip()
    s = s.split("(")[0].strip()                      # drop "(+1d4 hp)" notes
    # A full dice expression like "1d8-1" or "1d6": roll it directly.
    if re.fullmatch(r"\d*d\d+\s*[+\-]?\s*\d*", s.replace(" ", "")) and "d" in s:
        try:
            return max(1, dice.notation(s.replace(" ", "")).total)
        except Exception:
            pass
    # Forms like "N", "N+M", "N-M", "N to M", "N+XdY".
    m = re.match(r"^(\d+)\s*(?:to\s*\d+)?\s*([+\-]\s*\d+(?:d\d+)?)?", s)
    if not m:
        return max(1, dice.d8())
    n = int(m.group(1))
    base = sum(dice.d8() for _ in range(n)) if n else dice.d8()
    bonus = 0
    if m.group(2):
        b = m.group(2).replace(" ", "")
        sign = -1 if b[0] == "-" else 1
        b = b.lstrip("+-")
        bonus = sign * (dice.notation(b).total if "d" in b else int(b))
    return max(1, base + bonus)


def get(name: str) -> Optional[Monster]:
    return _BY_NAME.get((name or "").strip().lower())


def search(query: str, limit: int = 8) -> List[Monster]:
    q = (query or "").strip().lower()
    if not q:
        return []
    exact = [m for m in BESTIARY if m.name.lower() == q]
    sub = [m for m in BESTIARY if q in m.name.lower() and m.name.lower() != q]
    return (exact + sub)[:limit]


def to_combatant(dice: Dice, monster: Monster, label: Optional[str] = None):
    """Build a combat.Combatant for a monster (HP rolled fresh)."""
    from .. import combat
    hp = roll_hp(dice, monster)
    return combat.Combatant(
        name=label or monster.name, hp=hp, hp_max=hp,
        ac_descending=monster.ac_descending,
        attack_bonus=monster.attack_bonus,
        damage_dice=monster.primary_damage(),
        is_pc=False)
