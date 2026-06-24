"""home_halvedd.py -- the detailed home region: the March of Halvedd.

This is the zoomed-in starting region (one corner of the continent map, the
realm 'H'). Where known_world.py paints Halvedd as a handful of continent hexes,
THIS file resolves it to a fine hex grid with a named, described locale on most
hexes -- the actual sandbox the party begins in.

Same hex convention as the rest of the engine. render/worldmap.py turns this
into the data-rich SVG; the referee reads `contents` / `exits` and never the
picture. Coordinates are local to the region (0,0 = NW corner).

Geography: the poisoned Ashmarch (the Scar's edge) along the north; the river
Silverflow cutting SE; the King's Road running W (to Aurenne) to E (to
Valmoria); the Barrowdowns in the SE; Tumblewood in the SW. Wend is the hub.
"""
from __future__ import annotations

from typing import Any, Dict, List

HR_COLS = 14
HR_ROWS = 11
REGION_NAME = "The March of Halvedd"
REGION_OF = "H"  # which continent realm this expands

# Each hex: col,row,terrain,(name,kind,contents,flags). Unnamed hexes are
# wilderness of the given terrain. kind: town|village|keep|dungeon|ruin|
# landmark|shrine|bridge|lair. flags: free-form tags (hidden, trap, danger...).
HR_HEXES: List[Dict[str, Any]] = [
    # ── the Ashmarch: the Scar's poisoned northern edge (rows 0-1) ──
    {"col": 5, "row": 0, "terrain": "scar", "name": "The Ashmarch", "kind": "landmark",
     "contents": "A grey, ash-choked no-man's-land where Halvedd ends and the Sundering Scar begins. Nothing grows; the air tastes of old lightning.", "flags": "danger,wildmagic"},
    {"col": 7, "row": 0, "terrain": "scar", "name": "Cinderfield", "kind": "landmark",
     "contents": "A plain of fused black glass where an imperial legion died in the Sundering. Treasure-hunters dig here; few dig twice.", "flags": "danger,treasure"},
    {"col": 9, "row": 1, "terrain": "ruin", "name": "The Leaning Tower", "kind": "dungeon",
     "contents": "A half-collapsed pre-Sundering mage-tower tilting over the Ashmarch. Its lower vaults are intact, warded, and unlooted. A classic first delve.", "flags": "dungeon,trap,treasure"},
    {"col": 3, "row": 1, "terrain": "hills", "name": "Gallows Hill", "kind": "landmark",
     "contents": "A lone hill crowned by a long-empty gibbet, the march's old boundary-mark. You can see the whole valley from the top.", "flags": ""},
    # ── the heartland of the march (rows 2-5) ──
    {"col": 6, "row": 3, "terrain": "plains", "name": "Wend", "kind": "town",
     "contents": "The walled caravan-town at the march's heart and the party's home base: market, the Broken Wheel inn, a chapter-house of the Free Companies, and Reeve Maddox who keeps the peace badly.", "flags": "haven,quests"},
    {"col": 4, "row": 3, "terrain": "plains", "name": "Stagford", "kind": "village",
     "contents": "A farming hamlet on the King's Road west toward Aurenne. Sheep, a shrine, and a miller who hears everything.", "flags": ""},
    {"col": 9, "row": 4, "terrain": "plains", "name": "Mirebeck", "kind": "village",
     "contents": "A poor hamlet on the Valmoria road, half its folk refugees from the Bonelands. Resentful, hungry, and watched by Valmorian tax-agents.", "flags": ""},
    {"col": 7, "row": 4, "terrain": "river", "name": "Greywater Ford", "kind": "bridge",
     "contents": "The shallow crossing of the Silverflow on the King's Road. A toll-post, a ferryman, and the wreck of the old stone bridge the Sundering shook down.", "flags": "chokepoint"},
    {"col": 2, "row": 4, "terrain": "hills", "name": "Thornhold", "kind": "keep",
     "contents": "The seat of Baron Cael Thorn, nominal lord of Halvedd: a squat border-keep, a thin garrison, and a lord who owes money to Valmoria he cannot pay.", "flags": "patron"},
    {"col": 11, "row": 3, "terrain": "plains", "name": "The King's Road (East)", "kind": "landmark",
     "contents": "The rutted imperial road leaving the march toward Vael's Crossing and Valmoria. Merchant trains, and the bandits who love them.", "flags": "road"},
    {"col": 1, "row": 3, "terrain": "plains", "name": "The King's Road (West)", "kind": "landmark",
     "contents": "The road toward Lake Aurenmere and Aurenholt. Better kept on the Aurenne side; pilgrims and knights pass through.", "flags": "road"},
    # ── Tumblewood & the western wilds (rows 5-8, SW) ──
    {"col": 3, "row": 6, "terrain": "forest", "name": "Tumblewood", "kind": "landmark",
     "contents": "A tangled second-growth forest reclaiming abandoned imperial farmland. Charcoalers, poachers, and a band of broken-men outlaws under one 'Captain Crow.'", "flags": "danger,outlaws"},
    {"col": 1, "row": 7, "terrain": "forest", "name": "The Hermit's Hollow", "kind": "shrine",
     "contents": "Deep in Tumblewood, the cell of Brother Ossian, an exiled Aurennois priest who heals those who find him and asks hard questions.", "flags": "ally,hidden"},
    {"col": 5, "row": 7, "terrain": "marsh", "name": "Duskmoor", "kind": "landmark",
     "contents": "A reeking fen where the Silverflow spreads and slows. Will-o'-wisps, a sunken causeway, and stories of something that takes the unwary at dusk.", "flags": "danger"},
    {"col": 4, "row": 8, "terrain": "ruin", "name": "The Sunken Villa", "kind": "dungeon",
     "contents": "A pre-Sundering noble's villa swallowed by Duskmoor; its tiled halls are below the waterline now, and not empty.", "flags": "dungeon,hidden,treasure"},
    # ── the Silverflow valley & center-south (rows 6-9) ──
    {"col": 7, "row": 6, "terrain": "river", "name": "The Silverflow", "kind": "landmark",
     "contents": "The great river that runs from Aurenne to Sahl, here broad and slow. Barge-traffic, fishing-clans, and good fast travel for those with a boat.", "flags": "river,travel"},
    {"col": 8, "row": 7, "terrain": "plains", "name": "Saint's Rest", "kind": "shrine",
     "contents": "A roadside shrine and waystation tended by lay-sisters of the Dawnmother. Safe beds, weak ale, and the only consecrated ground for a day's ride.", "flags": "haven,ally"},
    {"col": 6, "row": 8, "terrain": "plains", "name": "Cael's Fields", "kind": "village",
     "contents": "The march's best farmland, worked in common since the old manor burned. The harvest here is what everyone north of the river is quietly counting on.", "flags": ""},
    # ── the Barrowdowns & SE hills (rows 7-10) ──
    {"col": 10, "row": 7, "terrain": "hills", "name": "The Barrowdowns", "kind": "landmark",
     "contents": "Rolling downs studded with the green mounds of a people older than the Imperium. Shepherds avoid them after dark; the barrows are not all sealed.", "flags": "danger,undead"},
    {"col": 11, "row": 8, "terrain": "hills", "name": "The Singing Barrow", "kind": "dungeon",
     "contents": "The greatest of the downs' tombs, its entry-stone cracked open last winter. Cold air and a faint keening come out of it. Nothing has come back in.", "flags": "dungeon,undead,treasure"},
    {"col": 9, "row": 9, "terrain": "hills", "name": "The Goblin Stair", "kind": "lair",
     "contents": "A warren in a quarried hillside where a goblin tribe -- pushed south out of the Bonelands -- now raids the Valmoria road.", "flags": "danger,lair"},
    {"col": 12, "row": 9, "terrain": "hills", "name": "Hollow Keep", "kind": "ruin",
     "contents": "A Free-Company strongpoint abandoned after its captain's company was wiped out in the Bonelands. The Compact will pay to see it reclaimed.", "flags": "ruin,quest"},
    # ── eastern edge & the road to the Bonelands (rows 4-9, E) ──
    {"col": 12, "row": 5, "terrain": "plains", "name": "Old Toll-Bridge", "kind": "bridge",
     "contents": "A surviving imperial bridge over a Silverflow tributary, held by a self-appointed 'baron' charging passage east. The Baron of Thornhold disputes the claim, weakly.", "flags": "chokepoint"},
    {"col": 13, "row": 7, "terrain": "badlands", "name": "The Bonelands Marches", "kind": "landmark",
     "contents": "Where Halvedd frays into the lawless Bonelands. Warlord outriders, refugees, and the dust of someone's recent war.", "flags": "danger,border"},
    {"col": 10, "row": 2, "terrain": "scar", "name": "The Whispering Stones", "kind": "landmark",
     "contents": "A ring of imperial boundary-stones on the Ashmarch's edge that murmur in a dead tongue when the wild magic rises. Wizards pay for rubbings; few will camp here.", "flags": "wildmagic,danger"},
]


def region_grid() -> Dict[Any, Dict[str, Any]]:
    """Full region as data: {(col,row): cell}. Unnamed hexes filled as wild."""
    grid: Dict[Any, Dict[str, Any]] = {}
    for c in range(HR_COLS):
        for r in range(HR_ROWS):
            grid[(c, r)] = {"col": c, "row": r, "terrain": "plains"}
    # carve the river/marsh band and surrounding wilds as sensible defaults
    for cell in HR_HEXES:
        grid[(cell["col"], cell["row"])] = dict(cell)
    return grid
