"""dungeonmap.py -- schematic 'both readers' renderer for a room-graph dungeon.

Draws each room as a node and each exit as an edge, and embeds the graph as
data on every node:

    data-room       room id
    data-name       display name
    data-exits      "to|via|flags; to|via|flags; ..."   (flags: locked/hidden/trapped)
    data-contents   the room's contents text
    data-flags      the room's own tags (entrance/boss/key/clue/trap...)

Edges are styled by how you pass them (door dashed, passage/stair solid, grate/
chute blue, trapped red) and tagged L/H/T for locked/hidden/trapped, so a human
reads the dungeon at a glance while a machine reads the exact graph. Movement is
a lookup against `data-exits`, never the drawing.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

PARCH = "#efe7d2"; INK = "#2b2118"; LINE = "#b8a578"
NODE_FILL = {"entrance": "#bcd9a6", "boss": "#d8a59a", "key": "#e8cf86"}
DEFAULT_FILL = "#f4eeda"

SPACING_X = 190.0
SPACING_Y = 130.0
NODE_W = 150.0
NODE_H = 78.0
MARGIN = 40.0


def _esc(s: Any) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def _exit_flags(e: Dict[str, Any]) -> List[str]:
    f = []
    if e.get("locked"): f.append("locked")
    if e.get("hidden"): f.append("hidden")
    if e.get("trapped"): f.append("trapped")
    return f


def _exits_attr(room: Dict[str, Any]) -> str:
    parts = []
    for e in room.get("exits", []):
        parts.append("{}|{}|{}".format(e["to"], e.get("via", "passage"),
                                       "+".join(_exit_flags(e))))
    return "; ".join(parts)


def _wrap(text: str, width: int) -> List[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def render(dungeon: Dict[str, Any]) -> str:
    rooms = dungeon["rooms"]
    by_id = {r["id"]: r for r in rooms}
    maxx = max(r["x"] for r in rooms); maxy = max(r["y"] for r in rooms)
    W = MARGIN * 2 + maxx * SPACING_X + NODE_W
    H = MARGIN * 2 + 46 + maxy * SPACING_Y + NODE_H

    def cx(r): return MARGIN + r["x"] * SPACING_X + NODE_W / 2
    def cy(r): return MARGIN + 46 + r["y"] * SPACING_Y + NODE_H / 2

    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {:.0f} {:.0f}" '
           'font-family="Georgia,serif">'.format(W, H)]
    out.append('<rect width="100%" height="100%" fill="{}"/>'.format(PARCH))
    out.append('<text x="{:.0f}" y="26" font-size="20" font-weight="bold" '
               'fill="#6b2b1f">{}</text>'.format(MARGIN, _esc(dungeon["name"])))
    out.append('<text x="{:.0f}" y="42" font-size="11" font-style="italic" '
               'fill="{}">A room-graph delve · levels {} · arc: {}</text>'.format(
                   MARGIN, INK, _esc(dungeon.get("level_range", "?")), _esc(dungeon.get("arc", ""))))

    # ── edges (dedupe bidirectional, merge flags) ──
    drawn = {}
    for r in rooms:
        for e in r.get("exits", []):
            if e["to"] not in by_id:
                continue
            key = frozenset((r["id"], e["to"]))
            flags = set(_exit_flags(e))
            via = e.get("via", "passage")
            if key in drawn:
                drawn[key]["flags"] |= flags
            else:
                drawn[key] = {"a": r["id"], "b": e["to"], "via": via, "flags": flags}
    for d in drawn.values():
        ra, rb = by_id[d["a"]], by_id[d["b"]]
        x1, y1, x2, y2 = cx(ra), cy(ra), cx(rb), cy(rb)
        via, flags = d["via"], d["flags"]
        if "trapped" in flags:
            col, dash = "#9c3322", "4,3"
        elif via in ("grate", "chute"):
            col, dash = "#2f6f93", "1,4"
        elif via == "door" or "locked" in flags or "hidden" in flags:
            col, dash = "#7a5a1e", "6,4"
        else:
            col, dash = INK, "none"
        out.append('<line x1="{:.1f}" y1="{:.1f}" x2="{:.1f}" y2="{:.1f}" '
                   'stroke="{}" stroke-width="2" stroke-dasharray="{}"/>'.format(
                       x1, y1, x2, y2, col, dash))
        tag = "".join(t[0].upper() for t in
                      (["locked"] if "locked" in flags else []) +
                      (["hidden"] if "hidden" in flags else []) +
                      (["trapped"] if "trapped" in flags else []))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        label = via if via in ("stair", "grate", "chute", "door") else ""
        cap = (label + (" " + tag if tag else "")).strip()
        if cap:
            out.append('<rect x="{:.1f}" y="{:.1f}" width="{}" height="13" rx="2" '
                       'fill="{}" opacity="0.92"/>'.format(mx - len(cap)*3.2 - 3, my - 9,
                                                           len(cap)*6.4 + 6, PARCH))
            out.append('<text x="{:.1f}" y="{:.1f}" font-size="9" text-anchor="middle" '
                       'fill="{}">{}</text>'.format(mx, my + 1.5, col, _esc(cap)))

    # ── nodes ──
    for r in rooms:
        x = MARGIN + r["x"] * SPACING_X
        y = MARGIN + 46 + r["y"] * SPACING_Y
        flagset = [f.split(":")[0] for f in r.get("flags", [])]
        fill = DEFAULT_FILL
        for k in ("entrance", "boss", "key"):
            if k in flagset:
                fill = NODE_FILL[k]; break
        out.append('<rect x="{:.1f}" y="{:.1f}" width="{}" height="{}" rx="7" '
                   'fill="{}" stroke="{}" stroke-width="1.5" '
                   'data-room="{}" data-name="{}" data-exits="{}" '
                   'data-flags="{}" data-contents="{}"/>'.format(
                       x, y, NODE_W, NODE_H, fill, LINE,
                       _esc(r["id"]), _esc(r["name"]), _esc(_exits_attr(r)),
                       _esc(",".join(r.get("flags", []))), _esc(r.get("contents", ""))))
        out.append('<text x="{:.1f}" y="{:.1f}" font-size="11" font-weight="bold" '
                   'text-anchor="middle" fill="#6b2b1f">{}</text>'.format(
                       x + NODE_W / 2, y + 16, _esc(r["name"])))
        # a couple of hint lines: monsters / key flags
        hint = []
        if r.get("monsters"):
            hint.append("foe: " + ", ".join(m.split(" (")[0] for m in r["monsters"])[:40])
        special = [f for f in r.get("flags", []) if f.split(":")[0] in
                   ("boss", "key", "clue", "trap", "danger", "entrance")]
        if special:
            hint.append(" ".join(special)[:42])
        ty = y + 32
        for h in hint[:2]:
            out.append('<text x="{:.1f}" y="{:.1f}" font-size="8.5" '
                       'text-anchor="middle" fill="{}">{}</text>'.format(
                           x + NODE_W / 2, ty, INK, _esc(h)))
            ty += 12
        out.append('<text x="{:.1f}" y="{:.1f}" font-size="7.5" text-anchor="middle" '
                   'fill="#8a7a5a" font-style="italic">{}</text>'.format(
                       x + NODE_W / 2, y + NODE_H - 6, _esc(r["id"])))

    # legend
    ly = H - 16
    out.append('<text x="{:.0f}" y="{:.0f}" font-size="9" fill="{}">'
               'edges: — passage/stair · - - door (L lock, H hidden) · '
               '·· grate/chute · red = trapped</text>'.format(MARGIN, ly, INK))
    out.append('</svg>')
    return "".join(out)
