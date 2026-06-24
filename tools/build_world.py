"""build_world.py -- generate the Known World maps from data, and validate.

Run:  python tools/build_world.py [OUTDIR]
Emits:  the_known_world.svg   (continent, all 20 realms)
        halvedd_home_region.svg (the detailed starting march)
Then runs guardrail checks and prints a report. Exits non-zero on hard errors.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine.data import known_world as kw
from engine.data import home_halvedd as hh
from render import worldmap


def build(outdir: str) -> None:
    os.makedirs(outdir, exist_ok=True)
    errors, warnings = [], []

    # ── continent ──
    grid = kw.all_hexes()
    realm_labels = {code: rec["name"] for code, rec in kw.REALMS.items()}
    svg = worldmap.render(grid, kw.COLS, kw.ROWS,
                          title="The Known World  ·  {}".format(kw.CURRENT_YEAR),
                          subtitle="The continent of {}, two centuries after the Sundering. "
                                   "Twenty realms; one healing wound at the heart.".format(kw.CONTINENT_NAME),
                          size=22.0, realm_labels=realm_labels)
    cont_path = os.path.join(outdir, "the_known_world.svg")
    with open(cont_path, "w", encoding="utf-8") as f:
        f.write(svg)

    # ── home region ──
    rgrid = hh.region_grid()
    rsvg = worldmap.render(rgrid, hh.HR_COLS, hh.HR_ROWS,
                           title=hh.REGION_NAME,
                           subtitle="The frontier march of Halvedd — the party's home ground, "
                                    "between Aurenne, Valmoria, the Free Companies, and the Scar's edge.",
                           size=30.0)
    home_path = os.path.join(outdir, "halvedd_home_region.svg")
    with open(home_path, "w", encoding="utf-8") as f:
        f.write(rsvg)

    # ── validate ──
    # 1. every realm has at least one hex on the continent
    realm_hexcount = {}
    for cell in grid.values():
        if cell["realm"]:
            realm_hexcount[cell["realm"]] = realm_hexcount.get(cell["realm"], 0) + 1
    for code in kw.REALMS:
        if realm_hexcount.get(code, 0) == 0:
            errors.append("Realm {} ({}) has NO hexes on the map.".format(code, kw.REALMS[code]["name"]))

    # 2. every locale sits on an in-grid hex; warn if stranded in open sea
    SEA = {"sea", "water"}
    for name, kind, code, c, r, _ in kw.LOCALES:
        if not (0 <= c < kw.COLS and 0 <= r < kw.ROWS):
            errors.append("Locale {!r} at {},{} is OFF the grid.".format(name, c, r))
            continue
        cell = grid[(c, r)]
        if cell["terrain"] in SEA and kind not in ("port",):
            warnings.append("Locale {!r} ({}) sits on open {} at {},{}.".format(
                name, kind, cell["terrain"], c, r))
        if cell["realm"] != code and not (kind == "port"):
            warnings.append("Locale {!r} expected realm {} but hex {},{} is realm {}.".format(
                name, code, c, r, cell["realm"]))

    # 3. neighbor integrity: every neighbor of every hex is itself in-grid
    neigh = worldmap.compute_neighbors(kw.COLS, kw.ROWS, 22.0)
    for (c, r), adj in neigh.items():
        for (a, b) in adj:
            if not (0 <= a < kw.COLS and 0 <= b < kw.ROWS):
                errors.append("Hex {},{} lists out-of-grid neighbor {},{}.".format(c, r, a, b))
        if not adj:
            warnings.append("Hex {},{} has no neighbors (isolated).".format(c, r))

    # 4. home region locales in-bounds
    for cell in hh.HR_HEXES:
        if not (0 <= cell["col"] < hh.HR_COLS and 0 <= cell["row"] < hh.HR_ROWS):
            errors.append("Home locale {!r} off region grid.".format(cell.get("name")))

    # ── report ──
    print("=" * 64)
    print("THE KNOWN WORLD  -  build report")
    print("=" * 64)
    print("continent : {} x {} = {} hexes".format(kw.COLS, kw.ROWS, kw.COLS * kw.ROWS))
    land = sum(1 for cl in grid.values() if cl["realm"])
    print("land hexes: {}   sea hexes: {}".format(land, kw.COLS * kw.ROWS - land))
    print("realms    : {}   locales: {}".format(len(kw.REALMS), len(kw.LOCALES)))
    print("home region: {} x {}   locales: {}".format(hh.HR_COLS, hh.HR_ROWS, len(hh.HR_HEXES)))
    print("-" * 64)
    print("hexes per realm:")
    for code, rec in kw.REALMS.items():
        print("  {}  {:<26} {:>3} hexes".format(code, rec["name"], realm_hexcount.get(code, 0)))
    print("-" * 64)
    print("wrote: {}".format(cont_path))
    print("wrote: {}".format(home_path))
    print("-" * 64)
    if warnings:
        print("WARNINGS ({}):".format(len(warnings)))
        for w in warnings:
            print("  ! " + w)
    if errors:
        print("ERRORS ({}):".format(len(errors)))
        for e in errors:
            print("  X " + e)
        sys.exit(1)
    print("VALIDATION: OK (no hard errors)")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "maps")
    build(out)
