"""Tests for the Flanaess hex map: renderer, persistence, tools, seed set."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from render.hexmap import render_map, _hex_center
from engine.data import flanaess
from state.repo import Repo
from referee.tools import RefereeTools


def test_renderer_emits_valid_svg():
    locs = [{"name": "Greyhawk", "kind": "city", "terrain": "settled",
             "col": 11, "row": 8},
            {"name": "Nyr Dyv", "kind": "landmark", "terrain": "water",
             "col": 11, "row": 6}]
    svg = render_map(locs, party=(11, 8))
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert "Greyhawk" in svg and "Nyr Dyv" in svg
    # party highlight stroke present
    assert "#6b2b1f" in svg


def test_hex_centers_offset_odd_columns():
    # Even-q offset: odd columns are pushed down half a hex.
    _, y_even = _hex_center(0, 0, 22.0, 8.0, 8.0)
    _, y_odd = _hex_center(1, 0, 22.0, 8.0, 8.0)
    assert y_odd > y_even


def test_persistence_upsert_moves_location():
    repo = Repo.memory()
    cid = repo.create_campaign("Map Test")
    repo.add_location(cid, "Hommlet", kind="village", terrain="plains",
                      hex_col=6, hex_row=8)
    repo.add_location(cid, "hommlet", kind="town", terrain="plains",
                      hex_col=6, hex_row=9)        # same name -> update
    rows = [r for r in repo.list_locations(cid)]
    assert len(rows) == 1
    assert rows[0]["kind"] == "town" and rows[0]["hex_row"] == 9


def test_party_hex_roundtrips():
    repo = Repo.memory()
    cid = repo.create_campaign("Party Test")
    repo.set_party_hex(cid, 11, 8)
    repo.set_party_hex(cid, 12, 8)
    parties = [r for r in repo.list_locations(cid) if r["kind"] == "party"]
    assert len(parties) == 1 and parties[0]["hex_col"] == 12


def test_tools_map_flow():
    repo = Repo.memory()
    cid = repo.create_campaign("Tool Test")
    t = RefereeTools(repo, cid)
    seeded = t.seed_flanaess()
    assert seeded["seeded"] == len(flanaess.FLANAESS_ANCHORS)
    t.add_location(name="Moathouse", kind="dungeon", terrain="swamp",
                   col=6, row=9, notes="ruined")
    t.set_party_position(col=6, row=8, place="Hommlet")
    state = t.list_locations()
    names = [l["name"] for l in state["locations"]]
    assert "City of Greyhawk" in names and "Moathouse" in names
    assert state["party"] == {"col": 6, "row": 8}
    # map events recorded
    evs = repo.recent_events(cid)
    assert any(e["kind"] == "map" for e in evs)


def test_seed_set_is_well_formed():
    for name, kind, terrain, col, row in flanaess.FLANAESS_ANCHORS:
        assert name and kind and terrain
        assert 0 <= col < 22 and 0 <= row < 16


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All hexmap tests passed.")
