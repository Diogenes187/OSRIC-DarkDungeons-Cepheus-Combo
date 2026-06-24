"""build_dungeon.py -- validate the Leaning Tower room-graph and render it.

Run:  python tools/build_dungeon.py [OUTDIR]
Emits: leaning_tower.svg   and runs guardrail checks; exits non-zero on errors.
"""
from __future__ import annotations
import os, sys
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine.data import dungeon_leaning_tower as dg
from render import dungeonmap


def build(outdir: str) -> None:
    os.makedirs(outdir, exist_ok=True)
    rooms = dg.ROOMS
    by_id = {r["id"]: r for r in rooms}
    errors, warnings = [], []

    # 1. every exit target exists
    for r in rooms:
        for e in r.get("exits", []):
            if e["to"] not in by_id:
                errors.append("Room '{}' exit -> '{}' does not exist.".format(r["id"], e["to"]))

    # 2. reciprocity: a->b implies b->a
    for r in rooms:
        for e in r.get("exits", []):
            if e["to"] in by_id:
                back = [x for x in by_id[e["to"]].get("exits", []) if x["to"] == r["id"]]
                if not back:
                    warnings.append("Exit '{}' -> '{}' has no return exit.".format(r["id"], e["to"]))

    # 3. connectivity from the entrance
    entrances = [r["id"] for r in rooms if "entrance" in [f.split(":")[0] for f in r.get("flags", [])]]
    if len(entrances) != 1:
        warnings.append("Expected exactly 1 entrance, found {}.".format(len(entrances)))
    start = entrances[0] if entrances else rooms[0]["id"]
    seen, q = {start}, deque([start])
    while q:
        cur = q.popleft()
        for e in by_id[cur].get("exits", []):
            if e["to"] in by_id and e["to"] not in seen:
                seen.add(e["to"]); q.append(e["to"])
    orphans = set(by_id) - seen
    if orphans:
        errors.append("Rooms unreachable from '{}': {}".format(start, ", ".join(sorted(orphans))))

    # 4. every room has at least one exit
    for r in rooms:
        if not r.get("exits"):
            errors.append("Room '{}' has no exits.".format(r["id"]))

    # 5. arc integrity: a boss, the key, and the clue trail are present
    allflags = [f for r in rooms for f in r.get("flags", [])]
    if not any(f == "boss" for f in allflags):
        errors.append("No boss room flagged.")
    if not any(f.startswith("key:") for f in allflags):
        errors.append("No key item flagged (the Seventh Sigil).")
    clues = [f for f in allflags if f.startswith("clue:")]
    if len(clues) < 3:
        warnings.append("Expected the full clue trail (lintel + 3 journals); found {}.".format(len(clues)))

    svg = dungeonmap.render({"name": dg.NAME, "rooms": rooms,
                             "level_range": dg.LEVEL_RANGE, "arc": dg.ARC})
    path = os.path.join(outdir, "leaning_tower.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)

    print("=" * 60)
    print("THE LEANING TOWER  -  dungeon build report")
    print("=" * 60)
    print("rooms: {}   exits: {}".format(
        len(rooms), sum(len(r.get("exits", [])) for r in rooms)))
    print("entrance: {}   reachable: {}/{}".format(start, len(seen), len(rooms)))
    print("clue trail: {}   key: {}   boss: {}".format(
        len(clues), any(f.startswith('key:') for f in allflags),
        any(f == 'boss' for f in allflags)))
    print("wrote:", path)
    print("-" * 60)
    if warnings:
        print("WARNINGS ({}):".format(len(warnings)))
        for w in warnings: print("  ! " + w)
    if errors:
        print("ERRORS ({}):".format(len(errors)))
        for e in errors: print("  X " + e)
        sys.exit(1)
    print("VALIDATION: OK (no hard errors)")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "maps")
    build(out)
