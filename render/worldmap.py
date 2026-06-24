"""worldmap.py -- the 'both readers' map generator for The Known World.

Renders a hex map as an SVG that is (a) pleasant for a human to look at and
(b) a machine-readable data structure: EVERY hex polygon carries

    data-hex        "col,row"           its coordinate
    data-terrain    e.g. "mountains"    what it is
    data-contents   text or ""          the locale/feature on it
    data-neighbors  "c,r;c,r;..."       its explicit adjacent hexes
    data-realm      realm code or ""    which realm owns it
    data-kind       e.g. "capital"      marker type, if any

The neighbor list is NOT a memorized offset table -- it is computed
GEOMETRICALLY from the engine's own hex-center math (the same formula
render/hexmap.py uses to draw). Two hexes are neighbors iff their centers sit
one hex-step apart. So 'read a hex's neighbors and move' is guaranteed to match
what the engine sees on the board.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

PARCHMENT = "#efe7d2"
INK = "#2b2118"
LINE = "#c9b98e"

# extended palette for the Known World's terrains
TERRAIN_FILL = {
    "plains": "#e7dba6", "grassland": "#dfe3a0", "steppe": "#d8d79a",
    "forest": "#8fb877", "woods": "#8fb877", "jungle": "#5f9e63",
    "hills": "#d2bd8a", "mountains": "#bdb4ab", "badlands": "#c9ad81",
    "desert": "#ecd9a0", "tundra": "#dde6ea", "snow": "#eef3f6",
    "swamp": "#8a9d72", "marsh": "#9bab7e",
    "water": "#9cc3d8", "sea": "#9cc3d8", "lake": "#9cc3d8",
    "river": "#a9cfe0", "coast": "#bcd4dd",
    "ruins": "#c8b9a6", "settled": "#e7dba6", "scar": "#9a8a93",
}


def _hex_center(col: int, row: int, size: float, ox: float, oy: float) -> Tuple[float, float]:
    # identical to render/hexmap.py: flat-top, odd columns shoved down
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


def compute_neighbors(cols: int, rows: int, size: float = 22.0) -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
    """Geometric adjacency from the engine's own hex centers. Robust: a hex's
    neighbors are exactly the in-grid hexes one hex-step (sqrt(3)*size) away."""
    centers = {(c, r): _hex_center(c, r, size, 0.0, 0.0)
               for c in range(cols) for r in range(rows)}
    step = math.sqrt(3) * size
    thresh = step * 1.15  # < distance to any 2-away hex, > distance to neighbors
    neigh: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
    for (c, r), (x0, y0) in centers.items():
        adj = []
        for (c2, r2), (x1, y1) in centers.items():
            if (c2, r2) == (c, r):
                continue
            if math.hypot(x1 - x0, y1 - y0) <= thresh:
                adj.append((c2, r2))
        adj.sort()
        neigh[(c, r)] = adj
    return neigh


def _esc(s: Any) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _marker(cx: float, cy: float, kind: str) -> str:
    k = (kind or "").lower()
    if k == "capital":
        # five-point star
        pts = []
        for i in range(10):
            ang = math.radians(-90 + i * 36)
            rr = 7.5 if i % 2 == 0 else 3.2
            pts.append("{:.1f},{:.1f}".format(cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        return '<polygon points="{}" fill="#6b2b1f" stroke="#2b2118" stroke-width="0.6"/>'.format(" ".join(pts))
    if k == "city":
        return '<circle cx="{:.1f}" cy="{:.1f}" r="5" fill="#6b2b1f" stroke="#2b2118" stroke-width="0.6"/>'.format(cx, cy)
    if k in ("town", "village", "keep"):
        return '<circle cx="{:.1f}" cy="{:.1f}" r="3.3" fill="#7a5a1e"/>'.format(cx, cy)
    if k == "port":
        return '<circle cx="{:.1f}" cy="{:.1f}" r="3.6" fill="#1f4a6b" stroke="#102733" stroke-width="0.6"/>'.format(cx, cy)
    if k in ("dungeon", "ruin", "lair"):
        s = 4.2
        return ('<rect x="{:.1f}" y="{:.1f}" width="{}" height="{}" fill="#3a2a20" '
                'transform="rotate(45 {:.1f} {:.1f})"/>').format(cx - s / 2, cy - s / 2, s, s, cx, cy)
    if k in ("shrine",):
        return '<polygon points="{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f}" fill="#b08a2a"/>'.format(
            cx, cy - 5, cx + 4.3, cy + 3.5, cx - 4.3, cy + 3.5)
    if k == "bridge":
        return '<rect x="{:.1f}" y="{:.1f}" width="8" height="2.4" fill="#4a3a28"/>'.format(cx - 4, cy - 1.2)
    # landmark / other -> green diamond
    return ('<polygon points="{:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f} {:.1f},{:.1f}" '
            'fill="#3a5a2a"/>').format(cx, cy - 5, cx + 4, cy, cx, cy + 5, cx - 4, cy)


def render(cells: Dict[Tuple[int, int], Dict[str, Any]], cols: int, rows: int,
           title: str, subtitle: str = "", size: float = 22.0,
           realm_labels: Optional[Dict[str, str]] = None) -> str:
    """cells: {(col,row): {terrain, realm?, name?, kind?, contents?}}."""
    ox, oy = 10.0, 10.0
    top = 30.0  # header band
    width = ox * 2 + size * (1.5 * cols + 0.5)
    height = oy * 2 + top + math.sqrt(3) * size * (rows + 1) + 24

    neigh = compute_neighbors(cols, rows, size)

    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {:.0f} {:.0f}" '
           'font-family="Georgia,serif">'.format(width, height)]
    out.append('<rect width="100%" height="100%" fill="{}"/>'.format(PARCHMENT))

    labels: List[str] = []
    markers: List[str] = []
    # accumulate realm hex centroids for faint realm-name labels
    realm_pts: Dict[str, List[Tuple[float, float]]] = {}

    for c in range(cols):
        for r in range(rows):
            cx, cy = _hex_center(c, r, size, ox, oy + top)
            cell = cells.get((c, r), {"terrain": "sea"})
            terr = (cell.get("terrain") or "sea").lower()
            fill = TERRAIN_FILL.get(terr, PARCHMENT)
            nb = ";".join("{},{}".format(a, b) for a, b in neigh[(c, r)])
            realm = cell.get("realm") or ""
            kind = cell.get("kind") or ""
            contents = cell.get("contents") or (cell.get("name") or "")
            out.append(
                '<polygon points="{pts}" fill="{fill}" stroke="{line}" stroke-width="0.7" '
                'data-hex="{c},{r}" data-terrain="{terr}" data-realm="{realm}" '
                'data-kind="{kind}" data-contents="{cont}" data-neighbors="{nb}"/>'.format(
                    pts=_hex_points(cx, cy, size), fill=fill, line=LINE, c=c, r=r,
                    terr=_esc(terr), realm=_esc(realm), kind=_esc(kind),
                    cont=_esc(contents), nb=nb))
            if realm:
                realm_pts.setdefault(realm, []).append((cx, cy))
            if cell.get("name"):
                markers.append(_marker(cx, cy, kind))
                labels.append('<text x="{:.1f}" y="{:.1f}" font-size="8.5" '
                              'text-anchor="middle" fill="{}" stroke="{}" stroke-width="2.2" '
                              'paint-order="stroke">{}</text>'.format(
                                  cx, cy + size - 2.5, INK, PARCHMENT, _esc(cell["name"])))

    # faint realm names at centroids
    if realm_labels:
        for code, pts in realm_pts.items():
            if code not in realm_labels or not pts:
                continue
            mx = sum(p[0] for p in pts) / len(pts)
            my = sum(p[1] for p in pts) / len(pts)
            out.append('<text x="{:.1f}" y="{:.1f}" font-size="13" text-anchor="middle" '
                       'fill="#6b2b1f" opacity="0.42" font-style="italic" '
                       'font-weight="bold">{}</text>'.format(mx, my, _esc(realm_labels[code])))

    out.extend(markers)
    out.extend(labels)
    # header
    out.append('<text x="{:.1f}" y="20" font-size="18" fill="{}" '
               'font-weight="bold">{}</text>'.format(ox + 2, INK, _esc(title)))
    if subtitle:
        out.append('<text x="{:.1f}" y="{:.1f}" font-size="11" fill="{}" '
                   'font-style="italic">{}</text>'.format(ox + 2, height - 8, INK, _esc(subtitle)))
    out.append('</svg>')
    return "".join(out)
