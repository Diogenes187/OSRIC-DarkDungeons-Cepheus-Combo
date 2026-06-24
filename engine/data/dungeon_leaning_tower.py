"""dungeon_leaning_tower.py -- the room-graph for the opening delve.

A DUNGEON here is a GRAPH OF ROOMS, not a drawn floorplan. Each room is a node
with:
    id        stable key the referee moves by
    name      what the players see
    contents  what is in the room (read this; never improvise the layout)
    monsters  bestiary names to get_monster/spawn_monster (never invent stats)
    treasure  what can be found (quest items are explicit; coin via the tables)
    flags     tags (entrance, boss, key, clue, trap, hidden, danger...)
    exits     list of {to, via, locked, hidden, trapped, note}

MOVEMENT IS A LOOKUP. To move, read the current room's `exits`; an exit only
exists if it is listed. A `hidden` exit must be found (search); a `locked` exit
needs a key or force; a `trapped` exit should be detected first. The schematic
SVG (render/dungeonmap.py) is generated FROM this data, so the picture can never
disagree with what the referee reads.

This dungeon resolves the canon arc 'pale-lamp' (see canon.json). The clue trail
(lintel glyph + three journal fragments) teaches the twist; the Seventh Sigil in
the Focus Vault is the key to the clean resolution at the Lamp Chamber.
Built for a starting party (levels 1-3).
"""
from __future__ import annotations

from typing import Any, Dict, List

DUNGEON_ID = "leaning_tower"
NAME = "The Leaning Tower"
REGION = "H"            # Halvedd (home region)
HOME_HEX = [9, 1]       # its hex on the Halvedd region map (the Ashmarch edge)
LEVEL_RANGE = "1-3"
ARC = "pale-lamp"

# x,y are schematic layout coords (col,row); they are for drawing only --
# adjacency is defined ENTIRELY by `exits`, never by x/y proximity.
ROOMS: List[Dict[str, Any]] = [
    {
        "id": "threshold", "name": "The Tilted Threshold", "x": 2, "y": 0,
        "contents": "The cracked ground-floor doorway. The whole tower leans a "
                    "good twenty degrees, so the flagstone floor slopes toward the "
                    "north wall. Carved into the lintel is a faintly warm glyph "
                    "(a WARD, not a curse -- a clue). A dead Boneland scavenger "
                    "lies against the rubble, two months gone.",
        "monsters": [], "treasure": ["a few coins and a rusted dagger on the corpse"],
        "flags": ["entrance", "clue:lintel-glyph"],
        "exits": [
            {"to": "stair", "via": "doorway"},
            {"to": "flooded", "via": "chute", "hidden": True,
             "note": "a rubble-choked hole in the leaning floor drops to the water below"},
        ],
    },
    {
        "id": "stair", "name": "The Leaning Stair", "x": 2, "y": 1,
        "contents": "A spiral stair canted hard by the tower's tilt; several steps "
                    "are cracked or missing. It serves a landing (the gallery) and "
                    "continues down into the lower vault.",
        "monsters": [], "treasure": [],
        "flags": ["trap"],
        "exits": [
            {"to": "threshold", "via": "doorway"},
            {"to": "gallery", "via": "landing"},
            {"to": "glyph_hall", "via": "stair", "trapped": True,
             "note": "a loose step a third of the way down (a simple fall trap)"},
        ],
    },
    {
        "id": "gallery", "name": "The Warden's Gallery", "x": 0, "y": 1,
        "contents": "A ruined study: rotted books, a cold hearth, and a faded "
                    "portrait of a thin, anxious man in imperial robes -- Maerith, "
                    "the tower's magus. The portrait conceals a sealed door. A "
                    "torn JOURNAL PAGE survives on the desk (fragment 1 of 3): it "
                    "speaks of 'the Lamp I lit to ward the march' and 'my Focus, "
                    "the Seventh Sigil, lost before the rite was done.'",
        "monsters": ["giant rat (x3)"],
        "treasure": ["journal fragment 1 (clue)"],
        "flags": ["clue:journal-1"],
        "exits": [
            {"to": "stair", "via": "landing"},
            {"to": "focus_vault", "via": "door", "hidden": True, "locked": True,
             "note": "behind the portrait; an arcane lock -- the Sigil is sealed within"},
        ],
    },
    {
        "id": "glyph_hall", "name": "The Glyph Hall", "x": 2, "y": 2,
        "contents": "A low vault-corridor. The floor is inlaid with a great "
                    "imperial rune that flares when crossed -- a wild-magic surge "
                    "trap, side-effect of the Lamp's unbalanced burn. A second "
                    "JOURNAL PAGE is pinned under a fallen sconce (fragment 2): "
                    "'the Lamp no longer holds anything back -- it FEEDS. I cannot "
                    "stop it without the Sigil and the rite's last line.'",
        "monsters": [],
        "treasure": ["journal fragment 2 (clue: the twist)"],
        "flags": ["trap:wild-magic", "clue:journal-2"],
        "exits": [
            {"to": "stair", "via": "stair", "trapped": True},
            {"to": "focus_vault", "via": "door", "trapped": True,
             "note": "a ward-trapped side door to the vault"},
            {"to": "flooded", "via": "passage"},
            {"to": "lamp_chamber", "via": "door", "locked": False,
             "note": "the warded double door to the Lamp -- the main route to the heart"},
        ],
    },
    {
        "id": "focus_vault", "name": "The Focus Vault", "x": 0, "y": 2,
        "contents": "A small sealed strongroom. On a black velvet stand rests the "
                    "SEVENTH SIGIL -- Maerith's focus-crystal, a fist-sized quartz "
                    "still humming faintly. Taking it is the KEY to ending the arc "
                    "cleanly. The stand is ward-trapped.",
        "monsters": [],
        "treasure": ["The Seventh Sigil (quest item / KEY)"],
        "flags": ["key:seventh-sigil", "trap"],
        "exits": [
            {"to": "gallery", "via": "door", "hidden": True, "locked": True},
            {"to": "glyph_hall", "via": "door", "trapped": True},
        ],
    },
    {
        "id": "flooded", "name": "The Flooded Sublevel", "x": 4, "y": 2,
        "contents": "The tilt sank this side of the vault below the water table; "
                    "black, cold water stands waist-to-chest deep. A barnacled "
                    "chest lies half-sunk in the far corner. A rusted iron grate in "
                    "the floor leads deeper still.",
        "monsters": ["giant frog (x2)"],
        "treasure": ["drowned chest -- coins & a potion (roll a small hoard)"],
        "flags": ["danger:water"],
        "exits": [
            {"to": "threshold", "via": "chute", "hidden": True},
            {"to": "glyph_hall", "via": "passage"},
            {"to": "reliquary", "via": "passage"},
            {"to": "lamp_chamber", "via": "grate", "hidden": True,
             "note": "a submerged grate -- the back way into the Lamp Chamber"},
        ],
    },
    {
        "id": "reliquary", "name": "The Drowned Reliquary", "x": 4, "y": 3,
        "contents": "A niche-lined room above the waterline, the magus's store of "
                    "minor workings. A suit of imperial parade armour stands guard "
                    "and animates if the relics are disturbed. The THIRD JOURNAL "
                    "PAGE rests in a reliquary box (fragment 3): it records the "
                    "rite's last line in full -- the words that can quench the "
                    "Lamp or lay Maerith to rest.",
        "monsters": ["animated armour (treat as a small construct -- get_monster)"],
        "treasure": ["one minor magic item (roll_magic_item)",
                     "journal fragment 3 (clue: the rite's last line)"],
        "flags": ["clue:journal-3", "danger"],
        "exits": [
            {"to": "flooded", "via": "passage"},
        ],
    },
    {
        "id": "lamp_chamber", "name": "The Lamp Chamber", "x": 2, "y": 3,
        "contents": "The vault's heart. The PALE LAMP burns on a central plinth -- "
                    "a heatless blue-white flame that throws no shadow and makes "
                    "the teeth ache. Bound to it stands MAERITH THE UNFINISHED, a "
                    "courteous revenant in imperial robes, certain he is still "
                    "warding Halvedd from a second Sundering. He will TALK first. "
                    "RESOLUTION: complete the rite with the Seventh Sigil (clean), "
                    "return his Focus / speak the last line to lay him to rest, or "
                    "talk him down -- smashing the Lamp works but triggers an "
                    "honest wild-magic backlash. See canon 'pale-lamp'.",
        "monsters": ["Maerith the Unfinished (unique boss -- base on wraith/ghost; "
                     "prefers parley; see canon)"],
        "treasure": ["the Pale Lamp (the prize is ENDING it, not looting it)"],
        "flags": ["boss", "arc-climax"],
        "exits": [
            {"to": "glyph_hall", "via": "door"},
            {"to": "flooded", "via": "grate", "hidden": True},
        ],
    },
]


def rooms_by_id() -> Dict[str, Dict[str, Any]]:
    return {r["id"]: r for r in ROOMS}
