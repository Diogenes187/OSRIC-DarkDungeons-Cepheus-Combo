"""spells.py -- the OSRIC spell catalog, loaded from the extracted spell list.

`reference/osric_text/spell_list.txt` is produced by scripts/extract_spells.py
from the four spellbook PDFs (Cleric, Druid, Illusionist, Magic-User). This
module parses it into a queryable catalog. Full spell *descriptions* stay in the
spellbooks/corpus for the referee to look up; here we carry name, class, spell
level, and school -- enough to choose, memorise, and cast.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
SPELL_FILE = os.path.normpath(
    os.path.join(_HERE, "..", "..", "reference", "osric_text", "spell_list.txt"))


@dataclass(frozen=True)
class Spell:
    name: str
    char_class: str
    level: int
    school: str


def _clean_name(n: str) -> str:
    n = n.replace("'S ", "'s ").replace("’", "'")
    while "  " in n:
        n = n.replace("  ", " ")
    return n.strip()


def _clean_school(s: str) -> str:
    s = s.strip()
    for pre in ("Arcane ", "Divine "):
        if s.startswith(pre):
            return s[len(pre):]
    return s


def _load() -> List[Spell]:
    out: List[Spell] = []
    if not os.path.exists(SPELL_FILE):
        return out
    with open(SPELL_FILE, encoding="utf-8") as f:
        for line in f:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4 and parts[1].isdigit():
                out.append(Spell(name=_clean_name(parts[2]),
                                 char_class=parts[0], level=int(parts[1]),
                                 school=_clean_school(parts[3])))
    return out


SPELLS: List[Spell] = _load()


def for_class(char_class: str, level: Optional[int] = None) -> List[Spell]:
    return [s for s in SPELLS
            if s.char_class == char_class and (level is None or s.level == level)]


def spell_levels(char_class: str) -> List[int]:
    return sorted({s.level for s in SPELLS if s.char_class == char_class})


def find(name: str, char_class: Optional[str] = None) -> Optional[Spell]:
    nl = name.lower()
    for s in SPELLS:
        if s.name.lower() == nl and (char_class is None or s.char_class == char_class):
            return s
    return None


def count_by_class() -> dict:
    out: dict = {}
    for s in SPELLS:
        out[s.char_class] = out.get(s.char_class, 0) + 1
    return out
