"""known_world.py -- the source of truth for The Known World setting.

Forked from flanaess.py's *role* (a seedable set of world anchors) but built
for a much larger, scripted continent. NOTHING here is meant to be recalled from
memory at the table: the map, the realms, the locales all live as DATA that the
referee reads. The SVG map is GENERATED from this module (see render/worldmap.py)
so the picture and the data can never disagree.

Layout convention matches the engine: flat-top hexes, even-q/odd-q offset, the
SAME (col,row) coordinates render/hexmap.py uses. Neighbors are NOT hard-coded
here -- render/worldmap.py derives them geometrically from the engine's own
hex-center math, so adjacency is always exactly what the engine believes.

Reckoning: years are counted After the Sundering (AS). The campaign opens in
211 AS. "Before" the cataclysm is reckoned BS.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

# ── grid size ────────────────────────────────────────────────────────────────
COLS = 26
ROWS = 18

WORLD_NAME = "Orruvane"          # the world (the planet)
CONTINENT_NAME = "The Known World"  # the charted continent the realms share
CURRENT_YEAR = "211 AS"          # After the Sundering

# ── realms ───────────────────────────────────────────────────────────────────
# code -> realm record. `terrain` is the default fill for the realm's hexes;
# feature overrides (mountains, rivers, the Scar) are applied afterward.
# `tone` tags which genre vein the realm leans into: tolkien | conan | dnd.
REALMS: Dict[str, Dict[str, Any]] = {
    "F": {"name": "The Frostmark", "people": "Hjoldar clans (humans)",
          "terrain": "tundra", "gov": "free clan-moots", "tone": "conan",
          "creed": "Freedom, oath, and the axe. Distrust kings and sorcery alike.",
          "blurb": "Cold-hardened northern clans of hunters, reavers, and skalds. "
                   "No throne rules them; honor and feud do. They despise the "
                   "southern empires that once tried to tax the snow."},
    "K": {"name": "The Iron Covenant of Karth", "people": "Karthish (humans)",
          "terrain": "hills", "gov": "militant theocracy", "tone": "dnd",
          "creed": "One Law, one Flame. Sorcery is sin; the old gods are lies.",
          "blurb": "A stern monotheist crusader-state worshipping the Forgefather "
                   "as the One True Flame. Orderly, zealous, and expansionist by "
                   "'conversion.' Burns witches and outlaws arcane magic."},
    "D": {"name": "Vaultholme", "people": "Dwarves of the Deepholds",
          "terrain": "mountains", "gov": "guild-kings & the Stone Moot", "tone": "tolkien",
          "creed": "The stone remembers. Debts are sacred; grudges are eternal.",
          "blurb": "Ancient dwarven hold-cities under the northern peaks. Masters "
                   "of forge and ledger, isolationist, and still mining toward "
                   "doors they sealed before the Sundering -- and should not reopen."},
    "N": {"name": "The Khalassar", "people": "Steppe nomads (humans, half-orcs)",
          "terrain": "steppe", "gov": "confederation of khans", "tone": "conan",
          "creed": "The horizon belongs to the rider. The dead ride beside us.",
          "blurb": "A vast confederation of horse-clans on the eastern Sea of "
                   "Grass. Raiders, traders, and ancestor-shamans. When a great "
                   "Khan unites them, empires to the west learn to fear dust."},
    "Y": {"name": "Yselmark", "people": "High elves of the East",
          "terrain": "forest", "gov": "the Evenstar Court", "tone": "tolkien",
          "creed": "We kept the lore the Imperium burned. We will not lend it cheaply.",
          "blurb": "A fading, reclusive elven realm of silver woods and drowned "
                   "towers. The elves remember the world before the Sundering -- "
                   "they warned against it -- and trust no human crown."},
    "A": {"name": "Aurenne", "people": "Aurennois (humans, half-elves)",
          "terrain": "plains", "gov": "feudal kingdom", "tone": "tolkien",
          "creed": "We are the rightful heirs of the Imperium. The crown endures.",
          "blurb": "The largest successor kingdom, chivalric and proud, claiming "
                   "the dead Imperium's mantle. Glorious on the surface, hollowed "
                   "by feuding dukes, an aging king, and an empty treasury."},
    "V": {"name": "Valmoria", "people": "Valmorian (humans)",
          "terrain": "plains", "gov": "merchant-princes & a chartered Senate",
          "tone": "dnd", "creed": "Coin is the only crown that never dies.",
          "blurb": "Aurenne's pragmatic rival: banks, charters, and a senate of "
                   "merchant houses. It buys with gold what Aurenne claims by "
                   "blood, and quietly funds half the wars on the continent."},
    "Z": {"name": "The Sundering Scar", "people": "(no nation; scavengers, horrors)",
          "terrain": "scar", "gov": "none", "tone": "tolkien",
          "creed": "Here the world broke. It has not finished breaking.",
          "blurb": "The blasted heart of the cataclysm: the drowned ruin of the "
                   "imperial capital, wild magic, and things that crawled in "
                   "through the thinned veil. Rich in ruin-gold and quick death."},
    "P": {"name": "The Pallid Cities", "people": "Ash-Dukes (humans)",
          "terrain": "ruins", "gov": "decadent city-tyrannies", "tone": "conan",
          "creed": "The world is ending slowly; we intend to enjoy the wait.",
          "blurb": "Jewel-bright city-states raised in the Imperium's outer ruins. "
                   "Pleasure, poison, masque, and quiet sorcery. Beautiful, cruel, "
                   "and rotting from the inside like fruit."},
    "B": {"name": "The Bonelands", "people": "broken khanates, warlords",
          "terrain": "badlands", "gov": "feuding warlords", "tone": "conan",
          "creed": "Strong take, weak dig. The graves here are not all old.",
          "blurb": "A wind-scoured march of shattered petty-kingdoms east of the "
                   "Scar, fought over by warlords and mercenary captains. Every "
                   "hill is somebody's barrow; some of the dead object."},
    "M": {"name": "The March of Coin", "people": "Free Companies (all races)",
          "terrain": "hills", "gov": "the Captains' Compact", "tone": "dnd",
          "creed": "We sell war wholesale and peace at a premium.",
          "blurb": "A buffer region run by condottieri -- chartered mercenary "
                   "companies who rent themselves to every realm in turn. The one "
                   "place a sellsword of any blood is judged only by their record."},
    "H": {"name": "Halvedd", "people": "Marchfolk (humans, dwarves, halflings)",
          "terrain": "plains", "gov": "petty lords & free towns", "tone": "dnd",
          "creed": "The edge of the map is where a nobody becomes a name.",
          "blurb": "The frontier march where Aurenne, Valmoria, the Free "
                   "Companies, and the Scar's poisoned edge all collide. Petty "
                   "lords, ruin-delvers, refugees, and opportunity. (Home region.)"},
    "G": {"name": "The Gloamhold", "people": "drow, duergar, deeper things",
          "terrain": "mountains", "gov": "warring deep-houses", "tone": "dnd",
          "creed": "Up is a rumor. Everything sinks, in the end.",
          "blurb": "The cave-mouths and sinkholes of the southeast hills are the "
                   "doors of the Underrealm -- a downward kingdom of drow houses, "
                   "duergar forges, and aberrant horrors that the Sundering stirred."},
    "L": {"name": "The Lumenar League", "people": "Lumenese (humans, gnomes)",
          "terrain": "coast", "gov": "merchant republic", "tone": "dnd",
          "creed": "Free ports, free trade, and a free hand with the truth.",
          "blurb": "A league of west-coast harbor-cities: galleys, ledgers, "
                   "spies, and the continent's busiest slave-debate. Rich, "
                   "scheming, and perpetually one bad season from civil war."},
    "C": {"name": "The Scarlet Isles", "people": "Corsairs (all bloods)",
          "terrain": "water", "gov": "pirate captaincies", "tone": "conan",
          "creed": "No flag but the red one. No law past the tide-line.",
          "blurb": "A scatter of free ports and pirate-kings in the Western Sea. "
                   "A polyglot, lawless, gloriously dangerous frontier where the "
                   "League's lost cargo and the realms' exiles all wash up."},
    "T": {"name": "The Tidereach of Seywn", "people": "Seywn folk, sea-elves",
          "terrain": "marsh", "gov": "storm-priest moot", "tone": "tolkien",
          "creed": "The sea gives and the sea takes. Bow to neither king nor wave.",
          "blurb": "A half-drowned southwestern coast of fishing-clans and storm "
                   "shrines, sinking slowly since the Sundering tilted the tides. "
                   "Sea-elves and stranger things share the shallows."},
    "S": {"name": "The Caliphates of Sahl", "people": "Sahli (humans)",
          "terrain": "desert", "gov": "rival sultanates", "tone": "conan",
          "creed": "All things are written -- but the clever read ahead.",
          "blurb": "Brass-domed desert cities of caravans, astronomers, poets, "
                   "and djinn-bargains. Wealthy, learned, and riven by the feuds "
                   "of sultans who each claim the others are heretics."},
    "Q": {"name": "Qoph, the Serpent Dominion", "people": "Qophic (humans, yuan-ti)",
          "terrain": "swamp", "gov": "god-king priesthood", "tone": "conan",
          "creed": "The Serpent was first and will be last. Kneel and be spared.",
          "blurb": "The oldest and darkest power: a serpent-haunted southern "
                   "theocracy of necromancers and a deathless god-king priesthood. "
                   "The very name the northern crusaders use to mean 'the old evil.'"},
    "J": {"name": "Ymmu, the Sunscorch", "people": "Ymmu tribes (humans)",
          "terrain": "jungle", "gov": "warring chieftaincies & beast-cults",
          "tone": "conan", "creed": "The gods here have teeth, and they are hungry.",
          "blurb": "A vast southern jungle-savanna of tribal kingdoms, ivory, "
                   "and beast-god cults. Slavers from Sahl and the Isles raid its "
                   "coasts; its interior has swallowed every army sent to chart it."},
    "E": {"name": "The Eldwood (Sylvarine)", "people": "Wood elves & fey",
          "terrain": "forest", "gov": "the Greenmoot (no central rule)",
          "tone": "tolkien", "creed": "Older than the Imperium. Older than its gods.",
          "blurb": "The great primeval forest of the southwest, where the world's "
                   "first trees still stand and the fey keep their own law. "
                   "Neutral, ancient, and patient. It outlasted the Imperium; it "
                   "intends to outlast everyone."},
}

# ── continent layout: realm boxes, painted in order (later wins) ─────────────
# Each entry: (code, [(c0, c1, r0, r1), ...]) inclusive ranges.
_PAINT_ORDER: List[Tuple[str, List[Tuple[int, int, int, int]]]] = [
    ("N", [(18, 25, 1, 6), (20, 25, 6, 8)]),
    ("F", [(7, 16, 0, 2), (9, 15, 2, 3)]),
    ("K", [(2, 6, 1, 5)]),
    ("D", [(7, 17, 3, 4), (5, 7, 4, 6), (16, 18, 4, 5)]),
    ("A", [(3, 9, 5, 9), (4, 8, 9, 10)]),
    ("V", [(14, 19, 5, 9), (17, 20, 6, 8)]),
    ("Y", [(21, 25, 6, 11)]),
    ("Z", [(10, 13, 4, 7)]),
    ("P", [(10, 13, 8, 9)]),
    ("B", [(16, 21, 9, 12), (19, 22, 8, 9)]),
    ("M", [(5, 9, 10, 12)]),
    ("H", [(10, 14, 10, 12)]),
    ("G", [(15, 18, 11, 13)]),
    ("L", [(2, 3, 5, 10)]),
    ("E", [(1, 6, 10, 14)]),
    ("T", [(0, 3, 13, 16)]),
    ("S", [(8, 14, 13, 16)]),
    ("Q", [(15, 21, 14, 17)]),
    ("J", [(4, 9, 15, 17), (10, 13, 16, 17)]),
]

# explicit island/special hexes painted after boxes
_SCATTER: List[Tuple[str, int, int]] = [
    ("C", 0, 6), ("C", 1, 8), ("C", 0, 10), ("C", 1, 11), ("C", 0, 12),
]

# terrain feature overrides: (col,row) -> terrain. Applied after realm fills.
# Mountain spines, the great river, the inner lake, the Scar's heart, coasts.
_FEATURES: Dict[Tuple[int, int], str] = {}
def _spine(coords, terr):
    for c, r in coords:
        _FEATURES[(c, r)] = terr
# the northern mountain wall (Vaultholme peaks)
_spine([(8,3),(10,3),(12,3),(14,3),(9,4),(11,4),(13,4),(15,4),(6,5),(6,4)], "mountains")
# the Dragontooth range between Valmoria and the Bonelands
_spine([(18,7),(19,8),(18,9),(17,10)], "mountains")
# the Gloamhold cave-hills
_spine([(15,12),(16,13),(17,13),(18,14)], "hills")
# the heart of the Scar (the drowned-then-ashen imperial capital) -- ruined scar
_spine([(11,5),(12,6)], "scar")
# the Silverflow, the great river through the heartland (Aurenne->Halvedd->Sahl)
_spine([(6,6),(7,7),(8,8),(9,9),(10,10),(11,11),(11,12),(11,13),(11,14),(11,15)], "river")
# the Inner Lake (Lake Aurenmere) west-central
_spine([(5,8),(5,7)], "lake")
# desert deepening south
_spine([(9,14),(10,14),(11,14)], "desert")

# ── named locales (capitals, cities, ruins, dungeons, landmarks) ─────────────
# (name, kind, realm_code, col, row, blurb)
# kind: capital | city | town | dungeon | ruin | landmark | port
LOCALES: List[Tuple[str, str, str, int, int, str]] = [
    # North
    ("Hjoldenfast", "town", "F", 11, 1, "Greatest of the Frostmark steadings; a free moot-hall on the only sheltered fjord."),
    ("Karth-on-the-Flame", "capital", "K", 4, 2, "Cathedral-fortress of the Iron Covenant; the Eternal Pyre never gutters."),
    ("Khazad Vaultholme", "capital", "D", 10, 3, "The dwarven hold-city; its Iron Gate has not opened to outsiders in 80 years."),
    ("The Sealed Door", "dungeon", "D", 14, 4, "A black gate the dwarves walled up before the Sundering. Something knocks."),
    # Steppe & eastern elves
    ("Tomb-Camp of Khans", "landmark", "N", 22, 4, "The moving capital of the Khalassar -- wherever the Great Khan's yurt stands."),
    ("Yssimar", "capital", "Y", 23, 8, "The Evenstar Court of Yselmark, a silver city woven through living trees."),
    ("The Drowned Spire", "ruin", "Y", 24, 10, "A pre-Sundering elven tower now half-sunk in a black mere; its library survives."),
    # Heartland
    ("Aurenholt", "capital", "A", 5, 6, "Seat of King Aldric IV of Aurenne; a glorious, crumbling palace-city."),
    ("Lake Aurenmere", "landmark", "A", 5, 8, "The great inland lake; pilgrim-barges and a sunken pre-Sundering villa."),
    ("Valmoria City", "capital", "V", 16, 7, "Banking heart of the continent; its Senate Vaults are said to be undelvable."),
    ("Vael's Crossing", "city", "V", 15, 9, "The bridge-city where the Silverflow trade meets the eastern roads."),
    ("Old Aurelis", "ruin", "Z", 11, 5, "The drowned imperial capital at the Scar's heart. The richest, deadliest ruin alive."),
    ("The Weeping Gate", "dungeon", "Z", 12, 6, "A still-standing imperial arch that leaks wild magic and worse."),
    ("Masque of Pallidar", "capital", "P", 11, 8, "First of the Pallid Cities; beautiful, poisoned, ruled by the masked Ash-Duke."),
    ("Warlord's Reach", "town", "B", 19, 10, "The strongest Boneland warcamp this year; it will have a new owner next year."),
    ("The Singing Barrow", "dungeon", "B", 21, 9, "A khan's tomb whose dead are said to sing the names of those who enter."),
    # The March of Coin & Gloamhold
    ("Compacthold", "city", "M", 7, 11, "Free-company clearinghouse: contracts signed, companies hired, scores settled."),
    ("The Maw of Gloam", "dungeon", "G", 16, 13, "The widest sinkhole-gate to the Underrealm; a downward road no map follows."),
    # West coast & isles
    ("Lume", "capital", "L", 2, 7, "First city of the League; a forest of masts and a thicket of knives."),
    ("Port Scarlet", "port", "C", 0, 10, "The corsairs' open city -- every flag welcome, every purse at risk."),
    # The drowned southwest & south
    ("Seywatch", "town", "T", 1, 14, "Storm-shrine and last dry harbor of the sinking Tidereach."),
    ("Sahl-al-Brass", "capital", "S", 11, 14, "Greatest of the brass-domed caliphate cities; caravans, courts, and conspiracies."),
    ("Qophet-Nul", "capital", "Q", 18, 15, "The serpent-throne; its god-king has 'reigned' through nine recorded deaths."),
    ("The Coiled Ziggurat", "dungeon", "Q", 16, 16, "A black step-pyramid where the Serpent's oldest rite is still kept."),
    ("Ymmu-Kaa", "town", "J", 7, 16, "The only walled town of the Sunscorch; ivory, fever, and beast-god drums."),
    # The Eldwood
    ("The First Grove", "landmark", "E", 3, 12, "Where the world's eldest trees stand; the fey hold their Greenmoot here."),
]


def all_hexes() -> Dict[Tuple[int, int], Dict[str, Any]]:
    """Build the full continent as data: {(col,row): {realm, terrain, ...}}."""
    grid: Dict[Tuple[int, int], Dict[str, Any]] = {}
    # sea everywhere first
    for c in range(COLS):
        for r in range(ROWS):
            grid[(c, r)] = {"col": c, "row": r, "realm": None, "terrain": "sea"}
    # paint realm boxes in order
    for code, boxes in _PAINT_ORDER:
        terr = REALMS[code]["terrain"]
        for (c0, c1, r0, r1) in boxes:
            for c in range(c0, c1 + 1):
                for r in range(r0, r1 + 1):
                    if (c, r) in grid:
                        grid[(c, r)]["realm"] = code
                        grid[(c, r)]["terrain"] = terr
    # scatter (islands)
    for code, c, r in _SCATTER:
        if (c, r) in grid:
            grid[(c, r)]["realm"] = code
            grid[(c, r)]["terrain"] = REALMS[code]["terrain"]
    # feature terrain overrides (keep realm membership)
    for (c, r), terr in _FEATURES.items():
        if (c, r) in grid:
            grid[(c, r)]["terrain"] = terr
    # attach locales
    by_hex = {(c, r): (name, kind, blurb)
              for (name, kind, code, c, r, blurb) in LOCALES}
    for (c, r), cell in grid.items():
        if (c, r) in by_hex:
            name, kind, blurb = by_hex[(c, r)]
            cell["name"] = name
            cell["kind"] = kind
            cell["contents"] = blurb
    return grid


# ── seed into a campaign database (replaces flanaess.seed_campaign) ──────────
def seed_campaign(repo, cid: int) -> int:
    """Place every named locale into a campaign. Returns the count seeded."""
    for name, kind, code, col, row, _blurb in LOCALES:
        terrain = REALMS[code]["terrain"]
        repo.add_location(cid, name, kind=kind, terrain=terrain,
                          hex_col=col, hex_row=row)
    return len(LOCALES)
