"""flanaess.py -- a curated starter set of iconic Greyhawk anchor locations.

The published Atlas is an image map, so canonical hex coordinates can't be
extracted from it. These are APPROXIMATE relative placements on a 22x16 working
grid -- enough to orient a campaign (Nyr Dyv central, Furyondy/Veluna/Keoland
west, Nyrond/Urnst/Great Kingdom east, Iuz/Bandit Kingdoms north, Pomarj/Wild
Coast south). A DM seeds these, then adds and moves locations as play reveals
the world. Positions are not meant to be cartographically exact.

Each tuple: (name, kind, terrain, col, row).
"""

# kind: city | town | dungeon | landmark | region
FLANAESS_ANCHORS = [
    # --- the central lake and the free city ---
    ("Nyr Dyv",            "landmark", "water",     11, 6),
    ("City of Greyhawk",   "city",     "settled",   11, 8),
    ("Cairn Hills",        "landmark", "hills",     13, 8),
    ("Gnarley Forest",     "landmark", "forest",    10, 10),

    # --- the west: Furyondy, Veluna, the Vesve ---
    ("Dyvers",             "city",     "settled",    9, 7),
    ("Verbobonc",          "town",     "settled",    7, 7),
    ("Hommlet",            "village",  "plains",     6, 8),
    ("Furyondy",           "region",   "plains",     6, 5),
    ("Veluna",             "region",   "plains",     5, 6),
    ("Highfolk",           "town",     "hills",      4, 4),
    ("Vesve Forest",       "landmark", "forest",     5, 3),
    ("Yatil Mountains",    "landmark", "mountains",  4, 2),

    # --- the north: Iuz, the Horned Society, the Bandit Kingdoms ---
    ("Iuz",                "region",   "plains",     9, 3),
    ("Horned Society",     "region",   "plains",    11, 3),
    ("Bandit Kingdoms",    "region",   "plains",    15, 4),
    ("Tenh",               "region",   "plains",    16, 6),

    # --- the east: the Urnsts, Nyrond, the Great Kingdom ---
    ("County of Urnst",    "region",   "plains",    13, 7),
    ("Nyrond",             "region",   "plains",    16, 9),
    ("Rel Mord",           "city",     "settled",   17, 9),
    ("Great Kingdom",      "region",   "plains",    20, 9),
    ("Rauxes",             "city",     "settled",   20, 8),

    # --- the south: the Wild Coast, the Pomarj, the elf realms ---
    ("Wild Coast",         "region",   "coast",      9, 11),
    ("Pomarj",             "region",   "hills",     10, 12),
    ("Celene",             "region",   "forest",     7, 10),
    ("Keoland",            "region",   "plains",     5, 11),
    ("Sea of Gearnat",     "landmark", "sea",       12, 12),

    # --- the far west wastes ---
    ("Crystalmist Mtns",   "landmark", "mountains",  3, 9),
    ("Sea of Dust",        "landmark", "desert",     1, 11),
]


def seed_campaign(repo, cid: int) -> int:
    """Place the anchor set into a campaign. Returns the count seeded."""
    for name, kind, terrain, col, row in FLANAESS_ANCHORS:
        repo.add_location(cid, name, kind=kind, terrain=terrain,
                          hex_col=col, hex_row=row)
    return len(FLANAESS_ANCHORS)
