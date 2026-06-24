"""abilities.py -- OSRIC 3.0 ability-score modifier tables (Chapter One).

Transcribed from OSRIC 3.0 Player Guide, sections 1.1.2-1.1.7 (Tables 1.1.2A
through 1.1.7A). Lookups are by integer score 3..19, except Strength, which also
supports exceptional (percentile) Strength for fighters/paladins/rangers with an
18: pass ``pct`` 1..100 (where 100 == the "00" roll, which the rules treat as 19).

Every value here is from the book; nothing is computed or invented.
"""
from __future__ import annotations

from typing import Dict


def _spread(table: Dict[int, dict]) -> Dict[int, dict]:
    """Fill any missing scores 3..19 by carrying the last defined row forward
    (used where the book groups scores, e.g. 4-5 share a row)."""
    out: Dict[int, dict] = {}
    last = None
    for s in range(3, 20):
        if s in table:
            last = table[s]
        out[s] = dict(last)
    return out


# --- 1.1.2 STRENGTH (Table 1.1.2A) -----------------------------------------
# to_hit / damage are melee & thrown only. encumbrance is the lbs allowance.
# minor_test = max d6 roll that succeeds; major_test = % chance on d100.
STRENGTH = _spread({
    3:  dict(to_hit=-3, damage=-1, encumbrance=0,   minor_test=1, major_test=0),
    4:  dict(to_hit=-2, damage=-1, encumbrance=10,  minor_test=1, major_test=0),   # 4-5
    6:  dict(to_hit=-1, damage=0,  encumbrance=20,  minor_test=1, major_test=0),   # 6-7
    8:  dict(to_hit=0,  damage=0,  encumbrance=35,  minor_test=2, major_test=1),   # 8-9
    10: dict(to_hit=0,  damage=0,  encumbrance=35,  minor_test=2, major_test=2),   # 10-11
    12: dict(to_hit=0,  damage=0,  encumbrance=45,  minor_test=2, major_test=4),   # 12-13
    14: dict(to_hit=0,  damage=0,  encumbrance=55,  minor_test=2, major_test=7),   # 14-15
    16: dict(to_hit=0,  damage=1,  encumbrance=70,  minor_test=3, major_test=10),
    17: dict(to_hit=1,  damage=1,  encumbrance=85,  minor_test=3, major_test=13),
    18: dict(to_hit=1,  damage=2,  encumbrance=110, minor_test=3, major_test=16),
    19: dict(to_hit=3,  damage=6,  encumbrance=300, minor_test=5, major_test=40),
})

# Exceptional Strength bands for an 18 (fighters/paladins/rangers only).
# (low, high, data) where pct in [low, high]; 100 ("00") is handled as 19.
STRENGTH_EXCEPTIONAL = [
    (1,  50, dict(to_hit=1, damage=3, encumbrance=135, minor_test=3, major_test=20)),
    (51, 75, dict(to_hit=2, damage=3, encumbrance=160, minor_test=4, major_test=25)),
    (76, 90, dict(to_hit=2, damage=4, encumbrance=185, minor_test=4, major_test=30)),
    (91, 99, dict(to_hit=2, damage=5, encumbrance=235, minor_test=4, major_test=35)),
]


def strength_mods(score: int, pct: int = 0) -> dict:
    """Return the Strength row for a score (and optional exceptional pct)."""
    if score == 18 and pct:
        if pct >= 100:            # an "00" roll counts as Strength 19
            return dict(STRENGTH[19])
        for lo, hi, data in STRENGTH_EXCEPTIONAL:
            if lo <= pct <= hi:
                return dict(data)
    return dict(STRENGTH[max(3, min(19, score))])


# --- 1.1.3 DEXTERITY (Table 1.1.3A) ----------------------------------------
# ac_adj is the DESCENDING adjustment (lower AC = better); ascending = -ac_adj.
DEXTERITY = _spread({
    3:  dict(surprise=-3, missile_to_hit=-3, initiative=3,  ac_adj=4,  agility_save=-4),
    4:  dict(surprise=-2, missile_to_hit=-2, initiative=2,  ac_adj=3,  agility_save=-3),
    5:  dict(surprise=-1, missile_to_hit=-1, initiative=1,  ac_adj=2,  agility_save=-2),
    6:  dict(surprise=0,  missile_to_hit=0,  initiative=0,  ac_adj=1,  agility_save=-1),
    7:  dict(surprise=0,  missile_to_hit=0,  initiative=0,  ac_adj=0,  agility_save=0),  # 7-14
    15: dict(surprise=0,  missile_to_hit=0,  initiative=0,  ac_adj=-1, agility_save=1),
    16: dict(surprise=1,  missile_to_hit=1,  initiative=-1, ac_adj=-2, agility_save=2),
    17: dict(surprise=2,  missile_to_hit=2,  initiative=-2, ac_adj=-3, agility_save=3),
    18: dict(surprise=3,  missile_to_hit=3,  initiative=-3, ac_adj=-4, agility_save=4),
    19: dict(surprise=3,  missile_to_hit=3,  initiative=-3, ac_adj=-4, agility_save=4),
})


def dexterity_mods(score: int) -> dict:
    return dict(DEXTERITY[max(3, min(19, score))])


# --- 1.1.4 CONSTITUTION (Table 1.1.4A) -------------------------------------
# hp = standard hp bonus; hp_warrior = bonus for fighters/paladins/rangers.
CONSTITUTION = _spread({
    3:  dict(hp=-2, hp_warrior=-2, resurrection=40,  system_shock=35),
    4:  dict(hp=-1, hp_warrior=-1, resurrection=45,  system_shock=40),
    5:  dict(hp=-1, hp_warrior=-1, resurrection=50,  system_shock=45),
    6:  dict(hp=-1, hp_warrior=-1, resurrection=55,  system_shock=50),
    7:  dict(hp=0,  hp_warrior=0,  resurrection=60,  system_shock=55),
    8:  dict(hp=0,  hp_warrior=0,  resurrection=65,  system_shock=60),
    9:  dict(hp=0,  hp_warrior=0,  resurrection=70,  system_shock=65),
    10: dict(hp=0,  hp_warrior=0,  resurrection=75,  system_shock=70),
    11: dict(hp=0,  hp_warrior=0,  resurrection=80,  system_shock=75),
    12: dict(hp=0,  hp_warrior=0,  resurrection=85,  system_shock=80),
    13: dict(hp=0,  hp_warrior=0,  resurrection=90,  system_shock=85),
    14: dict(hp=0,  hp_warrior=0,  resurrection=92,  system_shock=88),
    15: dict(hp=1,  hp_warrior=1,  resurrection=94,  system_shock=91),
    16: dict(hp=2,  hp_warrior=2,  resurrection=96,  system_shock=95),
    17: dict(hp=2,  hp_warrior=3,  resurrection=98,  system_shock=97),
    18: dict(hp=2,  hp_warrior=4,  resurrection=100, system_shock=99),
    19: dict(hp=2,  hp_warrior=5,  resurrection=100, system_shock=99),
})


def constitution_mods(score: int, warrior: bool = False) -> dict:
    row = dict(CONSTITUTION[max(3, min(19, score))])
    row["hp_mod"] = row["hp_warrior"] if warrior else row["hp"]
    return row


# --- 1.1.5 INTELLIGENCE (Table 1.1.5A): max additional languages -----------
INTELLIGENCE_LANGUAGES = _spread({
    3: dict(max_languages=0), 8: dict(max_languages=1), 10: dict(max_languages=2),
    12: dict(max_languages=3), 14: dict(max_languages=4), 16: dict(max_languages=5),
    17: dict(max_languages=6), 18: dict(max_languages=7), 19: dict(max_languages=8),
})


def intelligence_languages(score: int) -> int:
    return INTELLIGENCE_LANGUAGES[max(3, min(19, score))]["max_languages"]


# --- 1.1.6 WISDOM (Table 1.1.6A): mental saving-throw modifier -------------
WISDOM_MENTAL_SAVE = _spread({
    3: dict(mental_save=-3), 4: dict(mental_save=-2), 5: dict(mental_save=-1),
    8: dict(mental_save=0), 15: dict(mental_save=1), 16: dict(mental_save=2),
    17: dict(mental_save=3), 18: dict(mental_save=4), 19: dict(mental_save=5),
})


def wisdom_mental_save(score: int) -> int:
    return WISDOM_MENTAL_SAVE[max(3, min(19, score))]["mental_save"]


# --- 1.1.7 CHARISMA (Table 1.1.7A) -----------------------------------------
CHARISMA = _spread({
    3:  dict(sidekicks=1,  loyalty=-30, reaction=-25),
    4:  dict(sidekicks=1,  loyalty=-25, reaction=-20),
    5:  dict(sidekicks=2,  loyalty=-20, reaction=-15),
    6:  dict(sidekicks=2,  loyalty=-15, reaction=-10),
    7:  dict(sidekicks=3,  loyalty=-10, reaction=-5),
    8:  dict(sidekicks=3,  loyalty=-5,  reaction=0),
    9:  dict(sidekicks=4,  loyalty=0,   reaction=0),    # 9-11
    12: dict(sidekicks=5,  loyalty=0,   reaction=0),
    13: dict(sidekicks=5,  loyalty=0,   reaction=5),
    14: dict(sidekicks=6,  loyalty=5,   reaction=10),
    15: dict(sidekicks=7,  loyalty=15,  reaction=15),
    16: dict(sidekicks=8,  loyalty=20,  reaction=25),
    17: dict(sidekicks=10, loyalty=30,  reaction=30),
    18: dict(sidekicks=15, loyalty=40,  reaction=35),
    19: dict(sidekicks=20, loyalty=50,  reaction=40),
})


def charisma_mods(score: int) -> dict:
    return dict(CHARISMA[max(3, min(19, score))])
