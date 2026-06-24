# The Known World — a data-first, AI-refereed OSRIC engine

An AI-refereed swords-and-sorcery RPG engine and an original campaign setting,
built on OSRIC (AD&D 1e-compatible core), the Dark Dungeons realm layer
(domains, strongholds, war machine), and Cepheus-style trade/vessels/hex-map
patterns. Forked clean from a Greyhawk engine and rebuilt around one principle:

> **The model never relies on its own memory for anything that has to be correct.**
> The engine (code) owns the math. The database owns the truth. The model only
> narrates from what a tool returns. When data is missing it is *flagged*, never
> invented. Honest dice always — rolled by the engine, not asserted by the model.

This repo is the result of that discipline taken seriously: state lives in SQLite,
every mechanical outcome is a deterministic tool call, the world is **data** that
gets read (never recalled), and a two-pass validator flags any narration that
references a room, NPC, monster, or plot beat not present in the data.

## The setting

**The Known World** is the continent of Orruvane, two centuries after the
**Sundering** — a magical catastrophe that broke the old Aurelian Imperium.
Twenty realms share the wreckage and none can rule the rest: a Tolkien-tragic
heartland of fading successor kingdoms, Conan-grim frontiers (barbarian clans,
decadent sorcerer-cities, pirate coasts, a serpent-haunted south), and one
slowly-healing wound — the Sundering Scar — at the centre. There is no single
doom, only many cold tensions. Play opens in the frontier march of **Halvedd**.

See **`KNOWN_WORLD_BIBLE.md`** for the full gazetteer and
**`The_Known_World_Gazetteer.pdf`** for the illustrated version.

## The data formats (this is the interesting part)

- **World map** — a hex map authored as data in `engine/data/known_world.py` and
  rendered to an SVG (`render/worldmap.py`) that is a *both-readers* artifact:
  pleasant for a human, and every hex carries `data-hex`, `data-terrain`,
  `data-contents`, and an explicit `data-neighbors` list. Movement is a lookup
  against the data; neighbors are computed from the engine's own hex geometry, so
  adjacency always matches what the engine believes. You navigate by the data,
  never by eyeballing the picture.
- **Dungeons** — a room graph (`engine/data/dungeon_leaning_tower.py`): each room
  a node with `data-exits` (doors/passages/stairs/grates, each flagged
  locked/hidden/trapped), `data-contents`, monsters, and treasure. Rendered to a
  schematic by `render/dungeonmap.py`.
- **Monsters** — referenced by name from the OSRIC bestiary; the engine rolls
  real HP into tracked state.
- **Storyline** — authored once as locked canon (`canon.json`): villain, goal,
  twist, win-condition, clock, and a *sealed* secret revealed only through play.
  The narrator reads it and runs to it, and is forbidden to contradict it.
- **Encounters** — rich weighted d100 tables per realm + sub-area + dungeon
  (`engine/data/encounters.py`), every combat row keyed to a real bestiary
  creature so the engine can spawn honest stats.

Each is generated/validated from data by a script in `tools/`, so the picture can
never drift from the truth:

```
python tools/build_world.py      # render continent + home-region maps, validate
python tools/build_dungeon.py    # render + validate the Leaning Tower room graph
```

## Layout

```
engine/        deterministic rules: dice, combat, calendar, leveling, spells,
               thief skills, turning, trade, vessels, naval, domains, war machine
  data/        rule tables + the WORLD: known_world, home_halvedd,
               dungeon_leaning_tower, encounters, bestiary
  validator.py the two-pass narration guardrail
referee/       tools.py (the MCP tool layer) + prompt.py (the DM directive)
state/         repo.py, schema.sql — SQLite, the single source of truth
render/        worldmap.py, dungeonmap.py, hexmap.py — the both-readers renderers
server/        mcp_server.py — exposes the engine's tools to a desktop client
tools/         build_world.py, build_dungeon.py — generate + validate artifacts
tests/         headless engine tests
maps/          generated map/schematic SVGs and PNGs
```

## Running the tests

```
pip install pytest
python -m pytest tests -q
```

## Running it as a desktop DM (MCP)

The engine runs as an MCP stdio server (`server/mcp_server.py`) and is driven by
an AI client as the Dungeon Master. Configure it with:

- `GREYHAWK_MCP_DB`   — path to this game's campaign database (one per solo game)
- `GREYHAWK_MCP_NAME` — the server/connector name
- `GREYHAWK_CORPUS`   — path to the 1e reference corpus (NOT included; see below)
- `ANTHROPIC_API_KEY` — optional, enables the Pass-2 (Haiku) narration validator

`connector_config.json` is a template. Multiple independent solo games are just
multiple servers, each pointing at its own database — same engine, same world,
separate saves.

## Reliability features

- **Two-pass validator** (`engine/validator.py`): a local rule-checker plus an
  optional Claude-Haiku pass that flags narration referencing entities not in the
  data, un-rolled dice, the model speaking for a player's character, and
  continuity/name drift.
- **`save_turn`** discipline so every state change is written down, not just said.
- **`roll_ability`** / engine dice: ability generation (3d6, 4d6-drop-lowest,
  5d6-drop-two) is done by the engine, including the drop — the model only reports.

## Licensing & attribution

The engine code and the original **Known World** setting (lore, maps, realms,
canon, encounter tables) are the author's own work.

This project is rules-compatible with **OSRIC** and **Dark Dungeons**, which are
distributed under open licenses (OSRIC's distribution terms; Dark Dungeons under
the OGL / Creative Commons). The reference text under `reference/` is that open
content. **The scraped 1e rulebook corpus (`adnd_1e.db`) is NOT included and must
not be committed** — it contains copyrighted material (PHB/DMG/UA/Monster Manuals
and the Greyhawk folio) and is referenced only as a local, private file via
`GREYHAWK_CORPUS`. No Wizards of the Coast / TSR product identity is included.

This is a personal, non-commercial project.
