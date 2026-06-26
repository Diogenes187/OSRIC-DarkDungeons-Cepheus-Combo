# STANDING DM PROTOCOL — MODULE AUTHORING & STOCKING
Conforms to this engine's EXISTING structure. Permanent; applies to every dungeon/module, now and future.

## CANONICAL STRUCTURE (use these — do not invent parallel files)
- **Design law:** `DESIGN_RULES.md` (the four-step "place first" discipline) + `KNOWN_WORLD_BIBLE.md` (setting canon). Read both before authoring.
- **Modules:** one file per location at `modules/<Name>.md`, in the format of the exemplar `modules/Greywether_Grange.md`. THIS is the room store.
- **Maps:** ASCII map inline in the module file (see Greywether); any rendered art goes in `maps/`.
- **Live story state / secrets:** the campaign DB via the canon tools (define_canon, sealed `secret`) and record_event.
- **DEPRECATED:** my earlier root files `_DM_ONLY_*` (bellweather/harrowgate key, map, ROOMSTOCK). Superseded by `modules/Harrowgate_Keep.md`. Do not author in the root again.

## MODULE FILE FORMAT (match Greywether_Grange.md exactly)
Title + one-line region/level header → PREMISE (short, mundane: what it was, why it fell, who's there) → THE MAP (ASCII, surface + sublevels) → THE GROUPS (1-3 factions, goals, leader stats) → ROOM KEY (each room: **Was / Now**, creatures with **HP PRE-ROLLED inline**, treasure that was lost/hidden/stored/forgotten) → THE ONE STRANGE THING (marked "do not explain") → MYSTERIES (no solution) → RUMORS (d10 table, true/false/uncertain) → WANDERING (d6/d8 table) → DM NOTES.

## RULES (bind every module)
1. DESIGN per DESIGN_RULES.md: real place first, mundane history (decades not eons), squatters with no master plan who don't all get along, EXACTLY ONE strange thing, the Coaster Test, the place is indifferent to the PCs. No puzzle chains / plots / chosen ones.
2. PRE-ROLL all HP and write it inline in the room key BEFORE play. Never roll a monster's HP at the table; never spawn creatures that aren't in the key.
3. HIDE: the module file is DM-only. Never print HP, treasure, room keys, the strange thing, or rosters into chat. Reveal only what the PCs perceive. Rumors are the only pre-play player-facing layer.
4. RUN: on room entry, READ the module's room entry; narrate the perceivable part; for combat, instantiate that room's creatures using the key's exact pre-rolled HP (for the attack tool) — read, don't invent. Roll surprise/reaction/morale honestly.
5. PERSIST: every module = `modules/<Name>.md` + a sealed canon entry (public hook + secret pointer). Current play-state deltas (who's dead/looted) go in record_event and a CURRENT STATE header in the module file.

This protocol and DESIGN_RULES.md together govern all authoring. Harrowgate now conforms: `modules/Harrowgate_Keep.md`.
