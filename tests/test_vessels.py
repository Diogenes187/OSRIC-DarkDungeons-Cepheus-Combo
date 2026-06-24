"""Tests for the unified vessel/cargo-carrier catalog."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import vessels as ves


def test_catalog_spans_backpack_to_galleon():
    assert ves.get("Backpack").capacity_tons < ves.get("Mule").capacity_tons
    assert ves.get("Mule").capacity_tons < ves.get("Wagon").capacity_tons
    assert ves.get("Wagon").capacity_tons < ves.get("Cog").capacity_tons
    assert ves.get("Cog").capacity_tons == 100.0


def test_terrain_capability_keeps_land_and_sea_distinct():
    wagon = ves.get("Wagon")
    cog = ves.get("Cog")
    mule = ves.get("Mule")
    assert wagon.can_traverse("road") and not wagon.can_traverse("sea")
    assert cog.can_traverse("sea") and not cog.can_traverse("mountains")
    assert mule.can_traverse("mountains")           # the pass a wagon can't take
    # Multi-modal: no single vessel crosses both a mountain pass and open sea.
    assert not any(v.can_traverse("mountains") and v.can_traverse("sea")
                   for v in ves.VESSELS.values())


def test_addons_modify_capacity_and_speed():
    w = ves.fit("Wagon", ["Reinforced Frame", "Cargo Expansion"])
    assert w.capacity_tons > ves.get("Wagon").capacity_tons
    assert w.speed_factor < ves.get("Wagon").speed_factor   # heavier, slower
    assert w.total_cost == 150 + 80 + 120
    # Smuggling compartment adds concealed capacity.
    s = ves.fit("River Barge", ["Smuggling Compartment"])
    assert s.capacity_tons >= ves.get("River Barge").capacity_tons + 0.5


def test_addon_compatibility_and_slots():
    # An Extra Sail can't be fitted to a wagon (land), and slots are capped.
    w = ves.fit("Handcart", ["Extra Sail", "Reinforced Frame", "Armed Escort"])
    assert all(a.name != "Extra Sail" for a in w.addons)
    assert len(w.addons) <= ves.get("Handcart").addon_slots


def test_vessels_for_terrain():
    sea = ves.vessels_for_terrain("sea")
    assert "Cog" in sea and "Wagon" not in sea
    land = ves.vessels_for_terrain("road")
    assert "Wagon" in land and "Cog" not in land


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All vessel tests passed.")
