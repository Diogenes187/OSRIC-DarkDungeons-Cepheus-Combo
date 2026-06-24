"""magic_items.py -- the OSRIC magic-item catalog, loaded from the extracted
property tables (reference/osric_text/magic_items.txt, by scripts/extract_magic_items.py).

Carries item name + category (potion, ring, rod/staff/wand, sword, weapon,
armour, misc, ioun stone) so the referee can roll or hand out a named item; the
full item description stays in the GM Guide for lookup. A short noise filter
drops the table artifacts (truncated names, sub-option fragments).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

from ..dice import Dice

_HERE = os.path.dirname(os.path.abspath(__file__))
ITEM_FILE = os.path.normpath(
    os.path.join(_HERE, "..", "..", "reference", "osric_text", "magic_items.txt"))

# Single-word sub-option fragments the table format leaks (e.g. wand targets).
_NOISE = {"acid", "demons", "devils", "elementals", "lycanthropes", "magic",
          "petrifaction", "polymorph", "undead", "trident/fork", "special"}

# Map treasure-result category words to catalog categories.
_ALIASES = {"wand": "rod/staff/wand", "staff": "rod/staff/wand",
            "rod": "rod/staff/wand", "shield": "armour"}


@dataclass(frozen=True)
class MagicItem:
    category: str
    name: str


def _load() -> List[MagicItem]:
    out: List[MagicItem] = []
    if not os.path.exists(ITEM_FILE):
        return out
    with open(ITEM_FILE, encoding="utf-8") as f:
        for line in f:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 2 or not parts[1]:
                continue
            cat, name = parts[0], parts[1]
            if name.lower() in _NOISE:
                continue
            if name.lower().endswith(" of"):          # truncated ("Wand of")
                continue
            out.append(MagicItem(category=cat, name=name))
    return out


ITEMS: List[MagicItem] = _load()


def categories() -> List[str]:
    return sorted({i.category for i in ITEMS})


def by_category(category: str) -> List[MagicItem]:
    cat = _ALIASES.get((category or "").lower(), (category or "").lower())
    return [i for i in ITEMS if i.category == cat]


def find(name: str) -> Optional[MagicItem]:
    nl = (name or "").strip().lower()
    for i in ITEMS:
        if i.name.lower() == nl:
            return i
    return None


def random_item(dice: Dice, category: Optional[str] = None) -> Optional[MagicItem]:
    pool = by_category(category) if category and category.lower() != "any" else ITEMS
    if not pool:
        pool = ITEMS
    if not pool:
        return None
    return pool[dice.d(len(pool)) - 1]
