"""encounters.py -- wandering-monster tables for The Known World.

Two tiers, same machinery as before (so the engine's random_encounter is
unchanged):

  TABLES   per-terrain baselines -- a flat list of bestiary monsters for each
           terrain (and dungeon depth). Used directly when no region is given,
           and as the USE_STD fallback for the regional tables.

  REGIONS  rich weighted d100 tables, one per realm (plus the Halvedd home
           sub-areas and the Leaning Tower), faithful to old-school regional
           stocking. Each row is (lo, hi, name). COMBAT rows use EXACT bestiary
           names so the engine spawns real, rolled stats; DESCRIPTIVE rows
           (patrols, refugees, caravans, omens, wild-magic surges) return as a
           named encounter the referee plays out -- random_encounter reports
           in_bestiary=false and no stats for those, by design. A USE_STD row
           rolls the region's fallback terrain table instead.

Every combat name here is checked against the bestiary by tools/build_encounters.py.
"""
from __future__ import annotations

from typing import List, Optional

from ..dice import Dice

# ── per-terrain baselines (exact bestiary names) ─────────────────────────────
TABLES = {
    # Dungeon by depth (shallower = weaker).
    "dungeon-1": ["Goblin", "Kobold", "Rat, Giant", "Skeleton", "Centipede, Giant",
                  "Orc", "Stirge", "Zombie"],
    "dungeon-2": ["Orc", "Hobgoblin", "Ghoul", "Spider, Giant", "Gnoll",
                  "Ogre", "Snake, Giant Boa", "Shadow"],
    "dungeon-3": ["Gnoll", "Ogre", "Bugbear", "Wight", "Owlbear", "Bear, Cave",
                  "Carrion Crawler", "Wraith"],
    "dungeon-4": ["Wraith", "Spectre", "Troll", "Giant, Hill", "Manticore",
                  "Basilisk", "Medusa", "Wyvern", "Mummy", "Ogre Mage"],
    # Wilderness terrains.
    "plains": ["Wolf", "Lion", "Gnoll", "Boar, Wild", "Bison",
               "Eagle, Giant", "Hobgoblin", "Wolf, Dire", "Mounted Nomads"],
    "grassland": ["Wolf", "Lion", "Boar, Wild", "Bison", "Eagle, Giant",
                  "Gnoll", "Hobgoblin", "Wolf, Dire"],
    "steppe": ["Wolf, Dire", "Worg", "Lion", "Bison", "Eagle, Giant",
               "Mounted Nomads", "Tribal Warriors", "Camel", "Gnoll", "Boar, Wild"],
    "forest": ["Wolf", "Bear, Black", "Boar, Wild", "Orc", "Goblin",
               "Spider, Giant", "Owlbear", "Centaur", "Ogre", "Stirge"],
    "jungle": ["Tiger", "Ape, Carnivorous", "Baboon", "Snake, Giant Boa",
               "Snake, Cobra", "Lizard, Giant", "Spider, Giant", "Stirge",
               "Leech, Giant", "Wasp, Giant"],
    "hills": ["Ogre", "Orc", "Hobgoblin", "Wolf", "Bear, Brown",
              "Mountain Lion", "Goblin", "Wolf, Dire", "Bugbear", "Giant, Hill"],
    "mountains": ["Ogre", "Orc", "Goblin", "Mountain Lion", "Bear, Cave",
                  "Griffon", "Roper", "Wolf", "Giant, Stone", "Wyvern"],
    "badlands": ["Gnoll", "Hobgoblin", "Ogre", "Jackalwere", "Vulchling",
                 "Wolf, Dire", "Manticore", "Wight", "Skeleton", "Lizard, Giant"],
    "desert": ["Gnoll", "Lizard, Giant", "Snake, Cobra", "Snake, Pit Viper",
               "Ogre", "Dragon, Brass", "Camel", "Lamia", "Basilisk", "Al-Mi'Raj"],
    "tundra": ["Wolf, Winter", "Yeti", "Bear, Polar", "Giant, Frost", "Remorhaz",
               "Rhinoceros, Woolly", "Mammoth", "Worg", "Eagle, Giant", "Dragon, White"],
    "swamp": ["Lizard Man", "Frog, Giant", "Toad, Giant", "Troll",
              "Snake, Giant Boa", "Stirge", "Centipede, Giant", "Naga, Water",
              "Bullywug", "Shambling Mound"],
    "marsh": ["Lizard Man", "Frog, Giant", "Bullywug", "Stirge", "Leech, Giant",
              "Snake, Giant Boa", "Naga, Water", "Shambling Mound", "Troll",
              "Toad, Giant"],
    "coast": ["Merman", "Sahuagin", "Crab, Giant", "Sea Lion", "Eel, Giant",
              "Squid, Giant", "Octopus, Giant", "Locathah", "Triton", "Sea Hag"],
    "sea": ["Sahuagin", "Sea Serpent", "Squid, Giant", "Octopus, Giant",
            "Eel, Giant", "Dragon Turtle", "Kraken", "Whale", "Sea Lion", "Barracuda"],
    "water": ["Sahuagin", "Sea Serpent", "Squid, Giant", "Eel, Giant",
              "Dragon Turtle", "Kraken", "Sea Lion", "Barracuda"],
    "lake": ["Fish, Giant Pike", "Fish, Giant Gar", "Crayfish, Giant",
             "Eel, Giant", "Nixie", "Beetle, Water", "Spider, Giant Water",
             "Leech, Giant", "Lizard Man", "Frog, Giant", "Troll", "Naga, Water"],
    "river": ["Crayfish, Giant", "Eel, Giant", "Frog, Giant", "Lizard Man",
              "Nixie", "Stirge", "Leech, Giant", "Snake, Giant Boa",
              "Fish, Giant Pike", "Troll"],
    "scar": ["Gelatinous Cube", "Carrion Crawler", "Otyugh", "Gorgon", "Basilisk",
             "Cockatrice", "Rust Monster", "Shadow", "Wraith", "Invisible Stalker",
             "Chimera", "Dretch"],
    "ruins": ["Skeleton", "Zombie", "Ghoul", "Ghast", "Wight", "Shadow",
              "Gargoyle", "Caryatid Column", "Stirge", "Rat, Giant",
              "Crypt Thing", "Spectre"],
    "settled": ["Rat, Giant", "Stirge", "Kobold"],
}


def terrains() -> List[str]:
    return sorted(TABLES.keys())


def roll(dice: Dice, terrain: str) -> Optional[str]:
    table = TABLES.get((terrain or "").strip().lower())
    if not table:
        return None
    return table[dice.d(len(table)) - 1]


# ── encounter context (group sizing) -- unchanged, world-agnostic ────────────
CONTEXTS = [
    ("scouting patrol",        40, 0.05),
    ("hunting party",          28, 0.15),
    ("raiding warband",        18, 0.40),
    ("large band on the move", 10, 0.75),
    ("full muster",             4, 1.00),
]


def contexts() -> List[str]:
    return [c[0] for c in CONTEXTS]


def context_fraction(name: str) -> Optional[float]:
    key = (name or "").strip().lower()
    if key in ("lair", "muster", "full muster", "full"):
        return 1.0
    for nm, _w, frac in CONTEXTS:
        if nm.lower() == key:
            return frac
    return None


def roll_context(dice: Dice):
    total = sum(w for _n, w, _f in CONTEXTS)
    pick = dice.d(total)
    upto = 0
    for nm, w, frac in CONTEXTS:
        upto += w
        if pick <= upto:
            return nm, frac
    return CONTEXTS[-1][0], CONTEXTS[-1][2]


# ── The Known World regional d100 tables ─────────────────────────────────────
# Each row: (lo, hi, name). Combat rows = exact bestiary names; descriptive rows
# = named encounters the referee plays. USE_STD rolls the fallback terrain table.
USE_STD = "Use Standard"

REGIONS = {
    # ===================== THE NORTH =====================
    "frostmark": {  # free Hjoldar clans; cold tundra/fjord
        "fallback": "tundra",
        "rows": [
            (1, 12, "Wolf, Winter"), (13, 20, "Wolf, Dire"),
            (21, 30, "Tribal Warriors"),  # Hjoldar reavers
            (31, 36, "Bear, Polar"), (37, 40, "Yeti"),
            (41, 44, "Giant, Frost"), (45, 46, "Remorhaz"),
            (47, 52, "Rhinoceros, Woolly"), (53, 56, "Mammoth"),
            (57, 63, "Hjoldar hunting party (clansfolk)"),
            (64, 66, "Skald and oath-sworn escort"),
            (67, 68, "Dragon, White"), (69, 100, USE_STD),
        ],
    },
    "karth": {  # Iron Covenant theocracy; ordered hills
        "fallback": "hills",
        "rows": [
            (1, 14, "Covenant footmen on patrol"),
            (15, 22, "Flame-priest and acolytes"),
            (23, 30, "Witch-hunter inquisitors"),
            (31, 36, "Pilgrim column to the Eternal Pyre"),
            (37, 44, "Wolf"), (45, 50, "Bear, Brown"),
            (51, 56, "Bandit heretics (outlaws)"),
            (57, 62, "Ogre"), (63, 66, "Hobgoblin"),
            (67, 100, USE_STD),
        ],
    },
    "vaultholme": {  # dwarven holds; northern peaks
        "fallback": "mountains",
        "rows": [
            (1, 14, "Dwarf prospecting party"),
            (15, 22, "Dwarf hold-guard patrol"),
            (23, 30, "Pack-train of dwarven traders"),
            (31, 38, "Orc"), (39, 44, "Goblin"),
            (45, 50, "Giant, Stone"), (51, 54, "Bear, Cave"),
            (55, 58, "Griffon"), (59, 60, "Roper"),
            (61, 62, "Dragon, Red"), (63, 100, USE_STD),
        ],
    },
    # ===================== THE EAST =====================
    "khalassar": {  # steppe nomads
        "fallback": "steppe",
        "rows": [
            (1, 18, "Mounted Nomads"),  # outriders
            (19, 28, "Tribal Warriors"),
            (29, 34, "Mystic Nomad"),  # ancestor-shaman
            (35, 44, "Wolf, Dire"), (45, 50, "Worg"),
            (51, 58, "Bison"),  # a herd on the move
            (59, 64, "Lion"), (65, 70, "Eagle, Giant"),
            (71, 76, "Caravan under the Khan's truce-banner"),
            (77, 100, USE_STD),
        ],
    },
    "yselmark": {  # high elves; silver woods
        "fallback": "forest",
        "rows": [
            (1, 14, "Evenstar elf wardens"),
            (15, 20, "Elf"), (21, 26, "Unicorn"),
            (27, 32, "Dryad"), (33, 38, "Satyr (Faun)"),
            (39, 44, "Pixie"), (45, 48, "Tree, Animated"),  # treants
            (49, 54, "Centaur"), (55, 58, "Spider, Giant"),
            (59, 62, "Owlbear"), (63, 66, "A silent elven hunt that does not stop"),
            (67, 100, USE_STD),
        ],
    },
    # ===================== THE HEARTLAND =====================
    "aurenne": {  # chivalric successor kingdom
        "fallback": "plains",
        "rows": [
            (1, 16, "Aurennois knight and retinue"),
            (17, 26, "Men-at-arms patrol"),
            (27, 38, "Farmers and herd animals"),
            (39, 46, "Merchant caravan"),
            (47, 52, "Pilgrims to the Dawnmother"),
            (53, 60, "Wolf"), (61, 66, "Boar, Wild"),
            (67, 72, "Bandits (broken men)"),
            (73, 76, "Ogre"), (77, 100, USE_STD),
        ],
    },
    "valmoria": {  # merchant republic
        "fallback": "plains",
        "rows": [
            (1, 18, "Valmorian merchant train with hired guards"),
            (19, 28, "Free Company escort under contract"),
            (29, 34, "Senate tax-agents and bailiffs"),
            (35, 40, "Bonded courier and outriders"),
            (41, 48, "Farmers and herd animals"),
            (49, 56, "Wolf"), (57, 62, "Bandits"),
            (63, 68, "Hobgoblin"), (69, 72, "Ogre"),
            (73, 100, USE_STD),
        ],
    },
    "sundering-scar": {  # the blasted wound; wild magic & horrors
        "fallback": "scar",
        "rows": [
            (1, 10, "Wild-magic surge (no monster -- an omen/effect)"),
            (11, 18, "Shadow"), (19, 24, "Wraith"),
            (25, 30, "Skeleton"), (31, 36, "Zombie"),
            (37, 42, "Carrion Crawler"), (43, 47, "Gelatinous Cube"),
            (48, 52, "Rust Monster"), (53, 56, "Chimera"),
            (57, 60, "Basilisk"), (61, 64, "Invisible Stalker"),
            (65, 68, "Dretch"), (69, 71, "Spectre"),
            (72, 74, "Ruin-scavengers who should have turned back"),
            (75, 100, USE_STD),
        ],
    },
    "pallid-cities": {  # decadent ruin city-states
        "fallback": "ruins",
        "rows": [
            (1, 14, "Masked revellers of the Ash-Duke's court"),
            (15, 22, "Bravo duelists and sell-swords"),
            (23, 30, "Cult of quiet sorcery (robed adepts)"),
            (31, 38, "Skeleton"), (39, 44, "Zombie"),
            (45, 50, "Ghoul"), (51, 54, "Shadow"),
            (55, 58, "Gargoyle"), (59, 62, "Stirge"),
            (63, 66, "Rat, Giant"), (67, 100, USE_STD),
        ],
    },
    "bonelands": {  # broken khanates, warlords, restless dead
        "fallback": "badlands",
        "rows": [
            (1, 14, "Warlord's outriders"),
            (15, 22, "Mercenary free-lances between contracts"),
            (23, 30, "Refugee column fleeing a sacked camp"),
            (31, 38, "Gnoll"), (39, 44, "Hobgoblin"),
            (45, 50, "Ogre"), (51, 56, "Wight"),
            (57, 62, "Skeleton"), (63, 66, "Jackalwere"),
            (67, 70, "Vulchling"), (71, 74, "Manticore"),
            (75, 100, USE_STD),
        ],
    },
    "march-of-coin": {  # mercenary buffer state
        "fallback": "hills",
        "rows": [
            (1, 20, "A chartered Free Company on the march"),
            (21, 30, "Recruiters and a paymaster's wagon"),
            (31, 38, "Rival company spoiling for a contract"),
            (39, 46, "Merchant caravan hiring guards"),
            (47, 54, "Wolf"), (55, 60, "Ogre"),
            (61, 66, "Bandits"), (67, 70, "Hobgoblin"),
            (71, 100, USE_STD),
        ],
    },
    "halvedd": {  # HOME REGION -- detailed sub-areas
        "fallback": "plains",
        "subregions": {
            "farmland": [
                (1, 16, "Marchfolk farmers and herd animals"),
                (17, 24, "Reeve Maddox's militia on patrol"),
                (25, 30, "Refugees from the Bonelands"),
                (31, 36, "Valmorian tax-agents pressing Baron Thorn's debt"),
                (37, 46, "Wolf"), (47, 52, "Boar, Wild"),
                (53, 60, "Goblin"),  # raiders pushed south
                (61, 66, "Rat, Giant"), (67, 70, "Ogre"),
                (71, 74, "A blighted beast, grey and wrong (Pale Lamp)"),
                (75, 100, USE_STD),
            ],
            "road": [  # the King's Road
                (1, 16, "Merchant caravan, Aurenne-to-Valmoria"),
                (17, 24, "Pilgrims bound for Saint's Rest"),
                (25, 32, "Aurennois knight and retinue"),
                (33, 40, "Free Company column under contract"),
                (41, 50, "Bandits working the road"),
                (51, 58, "Goblin"), (59, 64, "Wolf"),
                (65, 68, "Ogre"), (69, 100, USE_STD),
            ],
            "ashmarch": [  # the Scar's poisoned edge; the Pale Lamp clock
                (1, 12, "Wild-magic surge off the Scar (an omen/effect)"),
                (13, 20, "A blighted, grey-furred beast"),
                (21, 28, "Shadow"), (29, 36, "Skeleton"),  # raised near the Lamp
                (37, 42, "Zombie"), (43, 50, "Stirge"),
                (51, 58, "Wolf"),  # a grey-blighted pack
                (59, 64, "Boneland scavengers picking the dead-zone"),
                (65, 70, "The cold blue Lamp-light seen in the tower at dusk (omen)"),
                (71, 74, "Wraith"), (75, 100, USE_STD),
            ],
            "tumblewood": [  # outlaw forest
                (1, 18, "Captain Crow's outlaws"),
                (19, 26, "Charcoalers and poachers"),
                (27, 36, "Wolf"), (37, 44, "Boar, Wild"),
                (45, 52, "Goblin"), (53, 58, "Spider, Giant"),
                (59, 64, "Stirge"), (65, 68, "Owlbear"),
                (69, 72, "Ogre"), (73, 100, USE_STD),
            ],
            "barrowdowns": [  # ancient tombs; undead
                (1, 16, "Shepherds hurrying their flock off the downs"),
                (17, 26, "Skeleton"), (27, 36, "Zombie"),
                (37, 44, "Ghoul"), (45, 50, "Shadow"),
                (51, 56, "Wight"),  # barrow-wight
                (57, 60, "Crypt Thing"), (61, 64, "Poltergeist"),
                (65, 68, "Ghast"), (69, 100, USE_STD),
            ],
        },
    },
    "gloamhold": {  # the Underrealm reaches
        "fallback": "mountains",
        "rows": [
            (1, 12, "Dark Creeper"), (13, 20, "Dark Stalker"),
            (21, 28, "Grimlock"), (29, 34, "Troglodyte"),
            (35, 40, "Carrion Crawler"), (41, 46, "Roper"),
            (47, 50, "Xorn"), (51, 56, "Grey Ooze"),
            (57, 60, "Otyugh"), (61, 64, "Rust Monster"),
            (65, 68, "Naga, Guardian"), (69, 72, "Medusa"),
            (73, 100, USE_STD),
        ],
    },
    # ===================== THE WEST =====================
    "lumenar": {  # merchant republic harbor-cities
        "fallback": "coast",
        "rows": [
            (1, 18, "League galley and marine escort"),
            (19, 26, "Harbor merchants and factors"),
            (27, 34, "Spies and informers shadowing you"),
            (35, 42, "Press-gang seeking crew"),
            (43, 50, "Sahuagin"), (51, 56, "Merman"),
            (57, 62, "Crab, Giant"), (63, 66, "Sea Lion"),
            (67, 100, USE_STD),
        ],
    },
    "scarlet-isles": {  # corsairs
        "fallback": "coast",
        "rows": [
            (1, 22, "Corsair shore party"),
            (23, 32, "Rival pirate crew"),
            (33, 40, "Marooned sailors with a grudge"),
            (41, 48, "Smugglers moving a cargo"),
            (49, 56, "Sahuagin"), (57, 62, "Barracuda"),  # a shark-pack
            (63, 68, "Sea Hag"), (69, 72, "Octopus, Giant"),
            (73, 100, USE_STD),
        ],
    },
    "tidereach": {  # drowning storm-coast; sea-elves
        "fallback": "marsh",
        "rows": [
            (1, 14, "Seywn fisherfolk on stilted causeways"),
            (15, 22, "Storm-priest and shrine-wardens"),
            (23, 30, "Triton"),  # sea-elf scouts in the shallows
            (31, 38, "Lizard Man"), (39, 44, "Sahuagin"),
            (45, 50, "Sea Hag"), (51, 56, "Stirge"),
            (57, 62, "Frog, Giant"), (63, 66, "Naga, Water"),
            (67, 70, "Nixie"), (71, 100, USE_STD),
        ],
    },
    # ===================== THE SOUTH =====================
    "sahl": {  # desert caliphates; djinn-bargains
        "fallback": "desert",
        "rows": [
            (1, 16, "Salt-and-spice caravan of the caliphates"),
            (17, 24, "Sultan's mounted guard"),
            (25, 30, "Astronomers and a wandering poet-sage"),
            (31, 36, "Bandit (desert raiders)"),
            (37, 44, "Snake, Cobra"), (45, 50, "Snake, Pit Viper"),
            (51, 56, "Lizard, Giant"), (57, 60, "Lamia"),
            (61, 64, "Djinni"), (65, 67, "Dragon, Brass"),
            (68, 70, "Efreet"), (71, 100, USE_STD),
        ],
    },
    "qoph": {  # serpent dominion; necromancy, the old dark
        "fallback": "swamp",
        "rows": [
            (1, 12, "Serpent-priest and shaven acolytes"),
            (13, 20, "Temple slave-column under the lash"),
            (21, 28, "Snake, Giant Boa"), (29, 34, "Snake, Cobra"),
            (35, 40, "Naga, Spirit"), (41, 46, "Naga, Guardian"),
            (47, 52, "Lizard Man"), (53, 58, "Troglodyte"),
            (59, 64, "Mummy"), (65, 70, "Skeleton"),
            (71, 74, "Couatl"),  # rare; an enemy of the Serpent
            (75, 78, "Lamia"), (79, 80, "Lich"),  # a deathless priest
            (81, 100, USE_STD),
        ],
    },
    "ymmu": {  # jungle tribes & beast-cults
        "fallback": "jungle",
        "rows": [
            (1, 16, "Tribal Warriors"),  # Ymmu jungle hunters
            (17, 24, "Beast-cult drummers and a fetish-priest"),
            (25, 30, "Slaver raiders from the coast"),
            (31, 38, "Tiger"), (39, 44, "Ape, Carnivorous"),
            (45, 50, "Snake, Giant Boa"), (51, 56, "Baboon"),
            (57, 62, "Lizard, Giant"), (63, 66, "Leech, Giant"),
            (67, 70, "Wasp, Giant"), (71, 74, "Couatl"),
            (75, 100, USE_STD),
        ],
    },
    # ===================== THE ELDER WILD =====================
    "eldwood": {  # primeval forest; the fey keep their own law
        "fallback": "forest",
        "rows": [
            (1, 12, "Fey revel that lures travellers from the path (omen)"),
            (13, 20, "Elf"),  # wood-elves, watchful and silent
            (21, 26, "Dryad"), (27, 32, "Satyr (Faun)"),
            (33, 38, "Pixie"), (39, 42, "Brownie"),
            (43, 46, "Leprechaun"), (47, 52, "Centaur"),
            (53, 56, "Unicorn"), (57, 60, "Tree, Animated"),  # treants
            (61, 64, "Boar, Wild"), (65, 68, "Bear, Black"),
            (69, 72, "Spider, Giant"), (73, 100, USE_STD),
        ],
    },
    # ===================== THE OPENING DUNGEON =====================
    "leaning-tower": {  # the Pale Lamp delve -- supplements the keyed rooms
        "fallback": "dungeon-1",
        "subregions": {
            "upper": [  # threshold, stair, gallery
                (1, 22, "Rat, Giant"), (23, 36, "Stirge"),
                (37, 48, "Centipede, Giant"), (49, 60, "Skeleton"),
                (61, 70, "Boneland scavenger, alone and desperate"),
                (71, 78, "Spider, Giant"), (79, 100, USE_STD),
            ],
            "lower": [  # glyph hall, vault, flooded sublevel, reliquary
                (1, 16, "Shadow"), (17, 28, "Skeleton"),
                (29, 38, "Zombie"), (39, 48, "Frog, Giant"),
                (49, 56, "Crypt Thing"), (57, 64, "Gargoyle"),
                (65, 72, "Caryatid Column"),
                (73, 82, "A wild-magic flicker off the Pale Lamp (omen/effect)"),
                (83, 100, USE_STD),
            ],
        },
    },
}


def regions() -> List[str]:
    return sorted(REGIONS.keys())


def subregions(region: str) -> List[str]:
    reg = REGIONS.get((region or "").strip().lower())
    return sorted(reg["subregions"].keys()) if reg and "subregions" in reg else []


def region_fallback(region: str) -> Optional[str]:
    reg = REGIONS.get((region or "").strip().lower())
    return reg.get("fallback") if reg else None


def _lookup(rows, n: int) -> str:
    for lo, hi, name in rows:
        if lo <= n <= hi:
            return name
    return USE_STD


def roll_region(dice: Dice, region: str, subregion: Optional[str] = None):
    """Roll a Known World regional encounter. Returns (name, used_standard,
    subregion). A USE_STD result (or unknown region) returns (None, True, sub)
    so the caller rolls the fallback terrain table instead."""
    reg = REGIONS.get((region or "").strip().lower())
    if not reg:
        return None, True, None
    sub_key = None
    if "subregions" in reg:
        subs = reg["subregions"]
        sub_key = (subregion or "").strip().lower()
        if sub_key not in subs:
            sub_key = sorted(subs.keys())[0]
        rows = subs[sub_key]
    else:
        rows = reg["rows"]
    name = _lookup(rows, dice.d(100))
    if name == USE_STD:
        return None, True, sub_key
    return name, False, sub_key
