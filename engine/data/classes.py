"""classes.py -- OSRIC 3.0 character-class data (Chapter Three).

Transcribed from OSRIC 3.0 Player Guide, sections 1.3.1-1.3.10 (each class's
"THE X CHARACTER" stat block: minimum scores, hit die, alignment, prime
requisite XP bonus, initial gold). Hit-dice/XP progression tables and the long
prose of class abilities stay in the corpus for the referee to look up; this
module carries the spine the chargen engine needs.

Alignment codes: LG LN LE NG N NE CG CN CE.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

ALL_ALIGNMENTS = ("LG", "LN", "LE", "NG", "N", "NE", "CG", "CN", "CE")

# Named alignment groups, as the class blocks phrase them.
_ALIGN = {
    "any": ALL_ALIGNMENTS,
    "any evil": ("LE", "NE", "CE"),
    "any good": ("LG", "NG", "CG"),
    "any lawful": ("LG", "LN", "LE"),
    "lawful good only": ("LG",),
    "neutral only": ("N",),
    # Thief: "Neutral or evil" -> neutral on either axis, or evil.
    "neutral or evil": ("LN", "NG", "N", "NE", "CN", "CE", "LE"),
}


@dataclass
class CharClass:
    name: str
    minimums: Dict[str, int]                 # ability -> minimum score
    hit_die: int                             # die SIDES (d6 -> 6)
    hd_max_level: int                        # level after which HD stop being rolled
    first_level_hd: int = 1                  # rangers start with 2
    alignment_group: str = "any"
    prime_requisites: Tuple[str, ...] = ()
    # XP bonus: None, or (abilities, threshold) -> +10% if all >= threshold.
    prime_req_bonus: Optional[Tuple[Tuple[str, ...], int]] = None
    gold_dice: str = "2d6"                   # rolled on the seeded Dice
    gold_mult: int = 10                      # Monk is x1
    raw_alignment: str = ""                  # the book's exact phrasing

    @property
    def alignments(self) -> Tuple[str, ...]:
        return _ALIGN[self.alignment_group]


CLASSES: Dict[str, CharClass] = {
    "Assassin": CharClass(
        name="Assassin",
        minimums={"str": 12, "dex": 12, "con": 6, "int": 11, "wis": 6},
        hit_die=6, hd_max_level=15,
        alignment_group="any evil", raw_alignment="Any evil",
        prime_requisites=("dex",), prime_req_bonus=None,
        gold_dice="2d6", gold_mult=10),
    "Cleric": CharClass(
        name="Cleric",
        minimums={"str": 6, "con": 6, "int": 6, "wis": 9, "cha": 6},
        hit_die=8, hd_max_level=9,
        alignment_group="any", raw_alignment="Any",
        prime_requisites=("wis",), prime_req_bonus=(("wis",), 16),
        gold_dice="3d6", gold_mult=10),
    "Druid": CharClass(
        name="Druid",
        minimums={"str": 6, "con": 6, "int": 6, "wis": 12, "cha": 15},
        hit_die=8, hd_max_level=14,
        alignment_group="neutral only", raw_alignment="Neutral only",
        prime_requisites=("wis", "cha"), prime_req_bonus=(("wis", "cha"), 16),
        gold_dice="3d6", gold_mult=10),
    "Fighter": CharClass(
        name="Fighter",
        minimums={"str": 9, "dex": 6, "con": 7, "int": 3, "wis": 6, "cha": 6},
        hit_die=10, hd_max_level=9,
        alignment_group="any", raw_alignment="Any",
        prime_requisites=("str",), prime_req_bonus=(("str",), 16),
        gold_dice="5d4", gold_mult=10),
    "Illusionist": CharClass(
        name="Illusionist",
        minimums={"str": 6, "dex": 16, "int": 15, "wis": 6, "cha": 6},
        hit_die=4, hd_max_level=10,
        alignment_group="any", raw_alignment="Any",
        prime_requisites=("dex", "int"), prime_req_bonus=None,
        gold_dice="2d4", gold_mult=10),
    "Magic-User": CharClass(
        name="Magic-User",
        minimums={"dex": 6, "con": 6, "int": 9, "wis": 6, "cha": 6},
        hit_die=4, hd_max_level=11,             # rolls d4 HD through 11th level
        alignment_group="any", raw_alignment="Any",
        prime_requisites=("int",), prime_req_bonus=(("int",), 16),
        gold_dice="2d4", gold_mult=10),
    "Monk": CharClass(
        name="Monk",
        # Base minimums; STR/WIS 15+ and CON 11+ unlock full class abilities.
        minimums={"str": 10, "wis": 10, "dex": 15},
        hit_die=4, hd_max_level=17, first_level_hd=2,   # monk begins with 2d4
        alignment_group="any lawful", raw_alignment="Any Lawful",
        prime_requisites=("str", "wis", "dex"), prime_req_bonus=None,
        gold_dice="5d4", gold_mult=1),       # NOT x10
    "Paladin": CharClass(
        name="Paladin",
        minimums={"str": 12, "dex": 6, "con": 9, "int": 9, "wis": 13, "cha": 17},
        hit_die=10, hd_max_level=9,
        alignment_group="lawful good only", raw_alignment="Lawful Good only",
        prime_requisites=("str", "wis"), prime_req_bonus=(("str", "wis"), 16),
        gold_dice="5d4", gold_mult=10),
    "Ranger": CharClass(
        name="Ranger",
        minimums={"str": 13, "dex": 6, "con": 14, "int": 13, "wis": 14, "cha": 6},
        hit_die=8, hd_max_level=10, first_level_hd=2,   # rangers start with 2 HD
        alignment_group="any good", raw_alignment="Any good",
        prime_requisites=("str", "int", "wis"), prime_req_bonus=(("str", "int", "wis"), 16),
        gold_dice="5d4", gold_mult=10),
    "Thief": CharClass(
        name="Thief",
        minimums={"str": 6, "dex": 9, "con": 6, "int": 6, "cha": 6},
        hit_die=6, hd_max_level=10,
        alignment_group="neutral or evil", raw_alignment="Neutral or evil",
        prime_requisites=("dex",), prime_req_bonus=(("dex",), 16),
        gold_dice="2d6", gold_mult=10),
}


def get(cls: str) -> CharClass:
    return CLASSES[cls]


def meets_minimums(cls: str, scores: Dict[str, int]) -> bool:
    """True if scores satisfy every ability minimum for the class."""
    c = CLASSES[cls]
    return all(scores.get(a, 0) >= m for a, m in c.minimums.items())


def failed_minimums(cls: str, scores: Dict[str, int]) -> Tuple[str, ...]:
    """Which abilities fall short of the class minimums (for the XP-penalty
    optional rule / override messaging)."""
    c = CLASSES[cls]
    return tuple(a for a, m in c.minimums.items() if scores.get(a, 0) < m)


def alignment_allowed(cls: str, alignment: str) -> bool:
    return alignment in CLASSES[cls].alignments


def xp_bonus(cls: str, scores: Dict[str, int]) -> bool:
    """True if the character qualifies for the +10% prime-requisite XP bonus."""
    bonus = CLASSES[cls].prime_req_bonus
    if not bonus:
        return False
    abilities, threshold = bonus
    return all(scores.get(a, 0) >= threshold for a in abilities)
