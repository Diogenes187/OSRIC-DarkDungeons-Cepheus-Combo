"""hexmap.py -- render the Flanaess as an even-q offset hex map (SVG).

Flat-top hexes in even-q offset layout (the Traveller/Greyhawk convention).
Locations are placed at (col, row); the renderer colours each by terrain, marks
it by kind (city/town/dungeon/landmark/region), labels it, and can highlight the
party's current hex. The grid the party hasn't reached stays blank parchment --
a map that fills in as they explore.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

PARCHMENT = "#efe7d2"
INK = "#2b2118"
LINE = "#c9b98e"

TERRAIN_FILL = {
    "plains": "#e7dba6", "grassland": "#dfe3a0", "forest": "#9cbf83",
    "woods": "#9cbf83", "hills": "#d2bd8a", "mountains": "#c2bbb2",
    "desert": "#ecd9a0", "swamp": "#8fa67e", "marsh": "#8fa67e",
    "water": "#9cc3d8", "sea": "#9cc3d8", "lake": "#9cc3d8",
    "river": "#9cc3d8", "coast": "#bcd4dd", "settled": "#e7dba6",
}


def _hex_center(col: int, row: int, size: float, ox: float, oy: float) -> Tuple[float, float]:
    cx = ox + size + col * 1.5 * size
    cy = oy + math.sqrt(3) * size * (row + 0.5 * (col & 1)) + math.sqrt(3) / 2 * size
    return cx, cy


def _hex_points(cx: float, cy: float, size: float) -> str:
    pts = []
    for i in range(6):
        a = math.radians(60 * i)
        pts.append("{:.1f},{:.1f}".format(cx + size * math.cos(a),
                                          cy + size * math.sin(a)))
    return " ".join(pts)


def _marker(cx: float, cy: float, kind: str) -> str:
    k = (kind or "").lower()
    if k in ("city", "capital"):
        return ('<circle cx="{:.1f}" cy="{:.1f}" r="5.5" fill="#6b2b1f" '
                'stroke="#2b2118"/>').format(cx, cy)
    if k in ("town", "village", "keep", "stronghold"):
        return '<circle cx="{:.1f}" cy="{:.1f}" r="3.5" fill="#7a5a1e"/>'.format(cx, cy)
    if k in ("dungeon", "ruin", "lair"):
        s = 4
        return ('<rect x="{:.1f}" y="{:.1f}" width="{}" height="{}" '
                'fill="#3a2a20" transform="rotate(45 {:.1f} {:.1f})"/>').format(
                    cx - s / 2, cy - s / 2, s, s, cx, cy)
    # landmark / region / other -> diamond
    return ('<polygon points="{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f} '
            '{:.1f},{:.1f}" fill="#3a5a2a"/>').format(
                cx, cy - 5, cx + 4, cy, cx, cy + 5, cx - 4, cy)


def render_map(locations: List[Dict[str, Any]], cols: int = 22, rows: int = 16,
               party: Optional[Tuple[int, int]] = None,
               title: str = "The Flanaess", size: float = 22.0) -> str:
    ox, oy = 8.0, 8.0
    width = ox * 2 + size * (1.5 * cols + 0.5)
    height = oy * 2 + math.sqrt(3) * size * (rows + 1) + 18

    by_hex = {(int(l["col"]), int(l["row"])): l for l in locations
              if l.get("col") is not None and l.get("row") is not None}

    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {:.0f} {:.0f}" '
           'font-family="Georgia,serif">'.format(width, height)]
    out.append('<rect width="100%" height="100%" fill="{}"/>'.format(PARCHMENT))

    labels = []
    for col in range(cols):
        for row in range(rows):
            cx, cy = _hex_center(col, row, size, ox, oy)
            loc = by_hex.get((col, row))
            fill = TERRAIN_FILL.get((loc or {}).get("terrain", "").lower(), PARCHMENT) \
                if loc else "#f3ecd8"
            out.append('<polygon points="{}" fill="{}" stroke="{}" '
                       'stroke-width="0.7"/>'.format(_hex_points(cx, cy, size), fill, LINE))
            if loc:
                out.append(_marker(cx, cy, loc.get("kind", "")))
                name = str(loc.get("name", "")).replace("&", "&amp;").replace("<", "&lt;")
                labels.append('<text x="{:.1f}" y="{:.1f}" font-size="9" '
                              'text-anchor="middle" fill="{}">{}</text>'.format(
                                  cx, cy + size - 3, INK, name))
    if party:
        cx, cy = _hex_center(int(party[0]), int(party[1]), size, ox, oy)
        out.append('<polygon points="{}" fill="none" stroke="#6b2b1f" '
                   'stroke-width="2.5"/>'.format(_hex_points(cx, cy, size)))
    out.extend(labels)
    out.append('<text x="{:.1f}" y="{:.1f}" font-size="13" fill="{}" '
               'font-style="italic">{}</text>'.format(ox + 4, height - 6, INK, title))
    out.append('</svg>')
    return "".join(out)
