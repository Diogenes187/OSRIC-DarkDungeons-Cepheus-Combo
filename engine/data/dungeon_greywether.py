"""dungeon_greywether.py -- room-graph data for GREYWETHER GRANGE.

A small fortified manor-grange in the southern hill country of the march of
Halvedd (the Known World, continent of Orruvane). Mundane decline ~70 years ago;
three sets of squatters shelter inside the walls now -- a brigand band (the
Crow's-Foot), a goblin warren broken up from the caves below, and one old
graveward woman. The deep well whispers at night; its nature is left
UNRESOLVED on purpose. Companion to modules/Greywether_Grange.md.

Schematic (x, y) coordinates are for layout only, not to scale. "surface" is the
walled yard; "cellar" is the undercroft and the natural caves below it.
"""

DUNGEON_ID = "greywether_grange"
NAME = "Greywether Grange"
REGION = "H"  # the march of Halvedd
LEVEL_RANGE = (1, 3)

# Each room dict:
#   id, name, x, y, area ("surface"|"cellar"),
#   contents (function-first + current state),
#   monsters (list of "name xN" strings, hp pre-rolled in the .md),
#   treasure (list of strings),
#   flags (list, e.g. "entrance","faction:crowsfoot","faction:goblins",
#          "faction:nan","strange","danger"),
#   exits (list of {"to", "via", optional "locked"/"hidden"})
# Exits are authored bidirectionally (every exit has a matching reverse exit).

ROOMS = [
    {
        "id": "gate",
        "name": "The Gate",
        "x": 4, "y": 8, "area": "surface",
        "contents": ("WAS the grange's only formal entrance, an iron-shod oak "
                     "gate in the curtain wall. NOW one leaf hangs broken; the "
                     "other is barred from inside with fresh timber. A boy "
                     "lookout rings a cracked bell at armed strangers."),
        "monsters": ["bandit-lookout Pell x1 (hp 4, sling)"],
        "treasure": [],
        "flags": ["entrance", "faction:crowsfoot"],
        "exits": [
            {"to": "gatehouse", "via": "door"},
            {"to": "yard", "via": "gate"},
        ],
    },
    {
        "id": "gatehouse",
        "name": "The Gatehouse",
        "x": 3, "y": 8, "area": "surface",
        "contents": ("WAS the guardroom for the road-watch, with a ladder to "
                     "the wall-walk. NOW the brigands' watch-post and overflow "
                     "bunk; two off-duty brigands dice here."),
        "monsters": ["brigand Dob x1 (hp 6)", "brigand Yannick x1 (hp 3)"],
        "treasure": ["card-pot: 17 sp, 4 gp", "three cloaks, spare boots"],
        "flags": ["faction:crowsfoot"],
        "exits": [
            {"to": "gate", "via": "door"},
        ],
    },
    {
        "id": "yard",
        "name": "The Yard",
        "x": 4, "y": 6, "area": "surface",
        "contents": ("WAS the working yard -- muck, hens, carts, the smell of "
                     "sheep. NOW waist-high nettle and bramble, a fallen cart, "
                     "the whipping-post stump. A wild boar has wallowed in the "
                     "far corner and charges anything near her piglets."),
        "monsters": ["wild boar x1 (hp 17, tusk 3d4)", "piglets x3 (flee)"],
        "treasure": ["silver ram brooch (35 gp) tangled in a dead man's "
                     "belt-buckle in the bramble"],
        "flags": ["danger"],
        "exits": [
            {"to": "gate", "via": "gate"},
            {"to": "hall", "via": "door"},
            {"to": "well", "via": "passage"},
            {"to": "brewhouse", "via": "passage"},
            {"to": "chapel", "via": "passage"},
            {"to": "dovecote", "via": "passage"},
            {"to": "byre", "via": "passage"},
        ],
    },
    {
        "id": "hall",
        "name": "The Stone Hall",
        "x": 6, "y": 6, "area": "surface",
        "contents": ("WAS the heart of the grange -- one great stone-floored "
                     "room, central hearth, long table, the lord's high seat. "
                     "NOW the brigands' common hall; Mald and 2-4 men are "
                     "usually here. A loose hearthstone hides the band's cache; "
                     "a half-hidden trapdoor leads to the undercroft."),
        "monsters": ["Mald Crow-foot x1 (hp 20, leader)",
                     "brigands x4 (hp 7,5,8,2)"],
        "treasure": ["under hearthstone: 220 sp, 130 gp, garnet (50 gp), "
                     "Wend wool-cloth (25 gp)",
                     "Mald: 41 gp, stolen steel signet ring (60 gp)"],
        "flags": ["faction:crowsfoot"],
        "exits": [
            {"to": "yard", "via": "door"},
            {"to": "solar", "via": "stair"},
            {"to": "servants", "via": "door"},
            {"to": "undercroft", "via": "stair", "hidden": True},
        ],
    },
    {
        "id": "solar",
        "name": "The Solar",
        "x": 8, "y": 6, "area": "surface",
        "contents": ("WAS the lord's private upper chamber -- bed, shutters, "
                     "writing-desk. NOW Mald's own quarters, the one dry room. "
                     "A chest holds old Greywether letters and a land-deed "
                     "naming the murrain year and 'the singing in the well.'"),
        "monsters": [],
        "treasure": ["loose floorboard: 2 gp, silver ear-drop (10 gp)",
                     "Greywether letters & land-deed (lore, not coin)",
                     "bottle of southern wine"],
        "flags": ["faction:crowsfoot"],
        "exits": [
            {"to": "hall", "via": "stair"},
        ],
    },
    {
        "id": "servants",
        "name": "The Servants' Quarters",
        "x": 6, "y": 4, "area": "surface",
        "contents": ("WAS a low lean-to chamber where household servants slept "
                     "on pallets. NOW damp, half-collapsed; the brigands store "
                     "meal, bacon, apples, rope, spears in the dry half. Giant "
                     "rats nest under the rotten pallets and raid the sacks."),
        "monsters": ["giant rats x5 (hp 3,4,2,4,1, disease)"],
        "treasure": ["chewed pouch: 13 sp, a clay whistle",
                     "stores: smoked bacon, meal, rope, two spears"],
        "flags": ["danger"],
        "exits": [
            {"to": "hall", "via": "door"},
        ],
    },
    {
        "id": "well",
        "name": "The Well",
        "x": 5, "y": 5, "area": "surface",
        "contents": ("WAS the grange's deep well, dug deeper long ago 'to the "
                     "second water' and broken into a natural fissure below. "
                     "NOW a stone-rimmed shaft, windlass rotted. On still "
                     "nights it WHISPERS -- low, wordless, seeming to answer. "
                     "The brigands won't drink from it; Nan leaves bread on the "
                     "rim; the goblins won't pass beneath it. 60 ft to black "
                     "water, with the fissure-mouth opening off it ~40 ft down. "
                     "ITS NATURE IS NEVER EXPLAINED."),
        "monsters": [],
        "treasure": [],
        "flags": ["strange"],
        "exits": [
            {"to": "yard", "via": "passage"},
            {"to": "fissure", "via": "breach"},
        ],
    },
    {
        "id": "brewhouse",
        "name": "The Brewhouse",
        "x": 8, "y": 9, "area": "surface",
        "contents": ("WAS where the grange brewed its small-beer and ale -- "
                     "copper, mash-tun, troughs. NOW roofless and rain-rotted, "
                     "the copper scrapped, the tun in staves. Stirges colonize "
                     "the rafter-stub and old flue."),
        "monsters": ["stirges x4 (hp 6,4,7,5, blood drain)"],
        "treasure": ["stoneware jug of brandy (still good)", "iron pry-bar"],
        "flags": ["danger"],
        "exits": [
            {"to": "yard", "via": "passage"},
        ],
    },
    {
        "id": "chapel",
        "name": "The Chapel",
        "x": 6, "y": 10, "area": "surface",
        "contents": ("WAS the small family chapel -- altar, benches, the "
                     "honored dead beneath the floor. NOW roof partly fallen, "
                     "altar cracked, pews long burned. Three grave-slabs that "
                     "Nan Tegg keeps swept. A niche behind the altar holds the "
                     "chapel plate, never looted."),
        "monsters": [],
        "treasure": ["altar niche: silver chalice (40 gp), censer (15 gp), "
                     "prayer-beads w/ amber bead (20 gp)"],
        "flags": ["faction:nan"],
        "exits": [
            {"to": "yard", "via": "passage"},
        ],
    },
    {
        "id": "dovecote",
        "name": "The Dovecote",
        "x": 4, "y": 10, "area": "surface",
        "contents": ("WAS the round stone dovecote -- pigeons for table and "
                     "message, nest-holes ringing the wall. NOW wild doves "
                     "nest, the floor deep in guano, a barn owl at the top. A "
                     "long-dead servant's hoard is wedged in a high nest-hole. "
                     "Disturbing the doves clatters loud (wandering check)."),
        "monsters": ["wild doves (flush)", "barn owl x1 (harmless)"],
        "treasure": ["high nest-hole: purse of 30 gp, thin gold ring (45 gp)"],
        "flags": [],
        "exits": [
            {"to": "yard", "via": "passage"},
        ],
    },
    {
        "id": "byre",
        "name": "The Byre / Barn",
        "x": 2, "y": 6, "area": "surface",
        "contents": ("WAS the long timber barn and byre -- winter shelter for "
                     "sheep and oxen, hay in the loft. NOW half-fallen, the "
                     "loft a slope of rotten thatch; bats roost above. The "
                     "brigands stable two horses and a mule under a sound "
                     "corner; a brigand tends them and sleeps here."),
        "monsters": ["brigand Cinch x1 (hp 5)", "bats (clatter if disturbed)"],
        "treasure": ["two horses & a mule (30-60 gp each; enrages Mald)",
                     "moldered drover's pack: whetstone, 6 sp, hand-axe"],
        "flags": ["faction:crowsfoot"],
        "exits": [
            {"to": "yard", "via": "passage"},
        ],
    },
    {
        "id": "undercroft",
        "name": "The Undercroft",
        "x": 6, "y": 2, "area": "cellar",
        "contents": ("WAS the vaulted storage cellar under the hall -- ale, "
                     "salt-meat, overflow. NOW empty racks, broken hoops, "
                     "seventy years' dust, and the goblins' frontier. The hall "
                     "trapdoor comes down here; a back passage and a "
                     "goblin-broken hole lead on. A goblin sentry sometimes "
                     "skulks here."),
        "monsters": ["goblin sentry x1 (hp 4; 50% day / 80% night)"],
        "treasure": ["kicked in a corner: good-steel dagger, 8 cp"],
        "flags": ["faction:goblins"],
        "exits": [
            {"to": "hall", "via": "stair", "hidden": True},
            {"to": "larder", "via": "passage"},
            {"to": "warren", "via": "breach"},
            {"to": "nan_burrow", "via": "passage"},
        ],
    },
    {
        "id": "larder",
        "name": "The Larder / Cold-store",
        "x": 8, "y": 2, "area": "cellar",
        "contents": ("WAS the cold cellar -- stone shelves, a meat-hook beam, "
                     "kept cool. NOW the goblins' food-hole: stinking, hung "
                     "with stolen bacon and worse, the floor a midden. 2-3 "
                     "goblins squabble over scraps."),
        "monsters": ["goblins x3 (hp 5,2,6)"],
        "treasure": ["in the muck: 44 cp, 19 sp, gilt reliquary locket "
                     "(only 8 gp; goblins prize it)"],
        "flags": ["faction:goblins"],
        "exits": [
            {"to": "undercroft", "via": "passage"},
            {"to": "cistern", "via": "passage"},
        ],
    },
    {
        "id": "cistern",
        "name": "The Old Cistern",
        "x": 9, "y": 4, "area": "cellar",
        "contents": ("WAS a stone-lined rainwater cistern feeding the "
                     "cold-store. NOW half-full of black still water and dead "
                     "leaves; both factions ignore it. A drowned goblin floats "
                     "face-down; a lost caravan strongbox lies in the mud at "
                     "the bottom. The water is foul (sickness if drunk)."),
        "monsters": [],
        "treasure": ["strongbox (submerged): 300 sp, 80 gp, two amethysts "
                     "(50 gp each)"],
        "flags": ["danger"],
        "exits": [
            {"to": "larder", "via": "passage"},
        ],
    },
    {
        "id": "warren",
        "name": "The Goblin Warren",
        "x": 6, "y": 0, "area": "cellar",
        "contents": ("WAS the deepest cellar room where the dug cellar met the "
                     "living rock. NOW the goblins' main den: filthy bedding, a "
                     "dung-fire, bones. Skritch and the bulk of the warren are "
                     "here; their hoard is hidden under his bedding."),
        "monsters": ["Skritch x1 (hp 7, warren-boss)",
                     "goblins x6 (hp 4,6,3,5,2,7)"],
        "treasure": ["Skritch: jet-pommel dagger (30 gp), 22 gp",
                     "hoard under bedding: 190 cp, 60 sp, 35 gp, copper "
                     "armband (8 gp), silver bell-rattle (15 gp)"],
        "flags": ["faction:goblins", "danger"],
        "exits": [
            {"to": "undercroft", "via": "breach"},
            {"to": "cave", "via": "passage"},
        ],
    },
    {
        "id": "cave",
        "name": "The Natural Cave",
        "x": 8, "y": 0, "area": "cellar",
        "contents": ("WAS nothing made by hand -- the natural cavern the warren "
                     "spreads into. NOW a damp, dripping limestone chamber, the "
                     "goblins' overflow and rubbish-tip. Blind cave-rats live "
                     "in the cracks. A tight side-crack leads toward the "
                     "fissure."),
        "monsters": ["giant rats x4 (hp 2,3,1,4, disease)"],
        "treasure": ["dropped goblin necklace of pierced river-shells"],
        "flags": ["faction:goblins"],
        "exits": [
            {"to": "warren", "via": "passage"},
            {"to": "fissure", "via": "passage"},
        ],
    },
    {
        "id": "fissure",
        "name": "The Fissure",
        "x": 5, "y": -1, "area": "cellar",
        "contents": ("WAS never anything -- a natural rift the old well-diggers "
                     "broke into. NOW a tall narrow crack, cold air sighing "
                     "out. 40 ft up the rift the bottom of the well-shaft "
                     "opens. The goblins won't enter; they say it 'talks.' When "
                     "the well whispers above, here it is louder, nearer, still "
                     "wordless, from no direction at all. NOTHING TO FIND, "
                     "NOTHING TO KILL -- the one strange thing; leave it open."),
        "monsters": [],
        "treasure": [],
        "flags": ["strange"],
        "exits": [
            {"to": "cave", "via": "passage"},
            {"to": "well", "via": "breach"},
        ],
    },
    {
        "id": "nan_burrow",
        "name": "Nan Tegg's Burrow",
        "x": 4, "y": 2, "area": "cellar",
        "contents": ("WAS a side-cellar -- ice-pit or root-store -- off the "
                     "undercroft. NOW the old graveward's nest: pallet, banked "
                     "fire, dried herbs, offerings before three little stone "
                     "markers she made 'for the family.' Nan Tegg lives here; "
                     "she is the place's lore-source and no threat."),
        "monsters": ["Nan Tegg x1 (hp 3, non-combatant lore-source)"],
        "treasure": ["among her trinkets: real gold locket w/ faded portrait "
                     "(50 gp) -- only for kindness, not coin"],
        "flags": ["faction:nan"],
        "exits": [
            {"to": "undercroft", "via": "passage"},
        ],
    },
]


def rooms_by_id():
    """Return {id: room} for the grange's rooms."""
    return {room["id"]: room for room in ROOMS}


def _validate():
    """Self-check: unique ids, every exit target exists, exits are
    bidirectional, and every room is reachable from the entrance."""
    index = rooms_by_id()
    assert len(index) == len(ROOMS), "duplicate room id"

    # every exit target exists
    for room in ROOMS:
        for ex in room["exits"]:
            assert ex["to"] in index, (
                f"{room['id']} -> missing {ex['to']}")

    # exits are bidirectional
    for room in ROOMS:
        for ex in room["exits"]:
            back = [e for e in index[ex["to"]]["exits"]
                    if e["to"] == room["id"]]
            assert back, f"no reverse exit {ex['to']} -> {room['id']}"

    # connectivity from the entrance
    entrances = [r["id"] for r in ROOMS if "entrance" in r["flags"]]
    assert entrances, "no entrance flagged"
    start = entrances[0]
    seen, stack = set(), [start]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        for ex in index[cur]["exits"]:
            stack.append(ex["to"])
    unreached = set(index) - seen
    assert not unreached, f"unreachable rooms: {sorted(unreached)}"
    return True


if __name__ == "__main__":
    _validate()
    print(f"{NAME}: {len(ROOMS)} rooms, graph OK")
