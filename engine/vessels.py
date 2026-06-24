"""vessels.py -- the unified cargo-carrier catalog (the trade "chassis").

A cargo carrier is a cargo carrier, whether it's a backpack, a mule train, a
wagon, a river barge, or an ocean-going cog. Each has the same shape: a capacity
(in tons), a cost, daily upkeep, a speed factor, the terrain it can actually
traverse, and addon slots. Capacity/economics unify across the whole range; the
TERRAIN it can cross is what keeps land and sea meaningfully distinct -- and what
makes multi-modal routes (mules over the pass, barge down the river, ship across
the bay) emerge on their own.

Movement itself comes from engine.travel (hexes/day by terrain), modified by a
vessel's speed_factor; this module is the chassis, not the motion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# The terrains a route can cross (shared with engine.travel / encounters).
LAND = ("road", "plains", "forest", "hills", "desert")
ROUGH_LAND = ("mountains", "swamp")
WATER = ("river", "coast", "sea")
ALL_TERRAIN = LAND + ROUGH_LAND + WATER


@dataclass(frozen=True)
class VesselType:
    name: str
    category: str                 # pack | land | water
    capacity_tons: float          # cargo capacity
    cost_gp: int
    upkeep_gp_day: float          # feed/wages/maintenance per day
    speed_factor: float           # multiplier on base overland/water speed
    terrains: Tuple[str, ...]     # what it can traverse
    crew: int = 0                 # people/animals it needs to operate
    addon_slots: int = 0
    note: str = ""

    def can_traverse(self, terrain: str) -> bool:
        return (terrain or "").lower() in self.terrains


# name -> VesselType. Capacity in tons (a person hauls ~0.02t; a war-galley ~60t).
VESSELS: Dict[str, VesselType] = {
    # --- carried / pack ---
    "Backpack": VesselType("Backpack", "pack", 0.02, 2, 0.0, 1.0,
                           LAND + ROUGH_LAND, crew=0, addon_slots=0,
                           note="A person's spare carrying capacity for trade."),
    "Porter": VesselType("Porter", "pack", 0.05, 0, 0.5, 1.0,
                         LAND + ROUGH_LAND, crew=1, addon_slots=0,
                         note="A hired bearer; upkeep is their daily wage."),
    "Mule": VesselType("Mule", "pack", 0.15, 30, 0.5, 0.8,
                       LAND + ("mountains",), crew=0, addon_slots=1,
                       note="Sure-footed; the backbone of overland caravans."),
    "Pack Horse": VesselType("Pack Horse", "pack", 0.2, 40, 0.7, 1.0,
                             LAND, crew=0, addon_slots=1),
    # --- land vehicles ---
    "Handcart": VesselType("Handcart", "land", 0.25, 15, 0.1, 0.6,
                           ("road", "plains"), crew=1, addon_slots=1),
    "Cart": VesselType("Cart", "land", 0.5, 50, 1.0, 0.7,
                       ("road", "plains", "desert"), crew=1, addon_slots=2,
                       note="Two-wheeled; needs a draft animal."),
    "Wagon": VesselType("Wagon", "land", 2.0, 150, 2.0, 0.6,
                        ("road", "plains", "desert"), crew=1, addon_slots=3,
                        note="Four-wheeled freight hauler; needs a team."),
    "Heavy Wagon": VesselType("Heavy Wagon", "land", 4.0, 300, 3.0, 0.5,
                              ("road", "plains"), crew=2, addon_slots=4),
    "Caravan": VesselType("Caravan", "land", 16.0, 1200, 12.0, 0.5,
                          ("road", "plains"), crew=4, addon_slots=6,
                          note="Dammarion-Vharn fleet: 4 heavy freight wagons run "
                               "as one caravan, one driver per wagon (people stay "
                               "flat; the draft teams do the work). One wagon "
                               "fitted out with livestock cages."),
    # --- watercraft ---
    "Raft": VesselType("Raft", "water", 1.0, 40, 0.2, 0.5,
                       ("river", "coast"), crew=1, addon_slots=1),
    "Rowboat": VesselType("Rowboat", "water", 0.5, 50, 0.2, 0.6,
                          ("river", "coast"), crew=2, addon_slots=1),
    "Keelboat": VesselType("Keelboat", "water", 5.0, 400, 1.5, 0.7,
                           ("river", "coast"), crew=4, addon_slots=2),
    "River Barge": VesselType("River Barge", "water", 12.0, 500, 2.0, 0.7,
                              ("river", "coast"), crew=4, addon_slots=3),
    "Coaster": VesselType("Coaster", "water", 20.0, 2000, 4.0, 1.2,
                          ("coast", "river"), crew=8, addon_slots=3,
                          note="Small single-masted trader; hugs the coast."),
    "Longship": VesselType("Longship", "water", 30.0, 5000, 8.0, 1.4,
                           ("sea", "coast", "river"), crew=40, addon_slots=4),
    "Cog": VesselType("Cog", "water", 100.0, 10000, 12.0, 1.3,
                      ("sea", "coast"), crew=18, addon_slots=4,
                      note="Round-hulled ocean trader; the bulk hauler of seas."),
    "Galley": VesselType("Galley", "water", 60.0, 15000, 25.0, 1.5,
                         ("sea", "coast"), crew=70, addon_slots=5),
    "Merchant Galleon": VesselType("Merchant Galleon", "water", 150.0, 30000, 30.0,
                                   1.3, ("sea", "coast"), crew=30, addon_slots=6),
    # --- added watercraft (variety) ---
    "Sloop": VesselType("Sloop", "water", 15.0, 1800, 3.0, 1.45,
                        ("river", "coast", "sea"), crew=6, addon_slots=3,
                        note="Small, fast, single-masted; nimble in river, coast, and "
                             "open water. The smuggler's and runner's favourite."),
    "Cutter": VesselType("Cutter", "water", 10.0, 1500, 2.5, 1.5,
                         ("coast", "sea"), crew=8, addon_slots=3,
                         note="Fastest of the small naval hulls; revenue-runner and "
                              "light raider."),
    "Caravel": VesselType("Caravel", "water", 40.0, 8000, 9.0, 1.35,
                          ("sea", "coast"), crew=20, addon_slots=4,
                          note="Seaworthy lateen-rigged explorer-trader; long range."),
    "Carrack": VesselType("Carrack", "water", 120.0, 20000, 26.0, 1.3,
                          ("sea", "coast"), crew=40, addon_slots=5,
                          note="Great oceangoing merchantman; trades or fights."),
    "War Galley": VesselType("War Galley", "water", 25.0, 20000, 35.0, 1.6,
                             ("sea", "coast"), crew=100, addon_slots=6,
                             note="Dedicated oared warship: little cargo, ramming "
                                  "speed, and slots for fighting fittings."),
    "Dromond": VesselType("Dromond", "water", 45.0, 28000, 40.0, 1.45,
                          ("sea", "coast"), crew=120, addon_slots=6,
                          note="The great war-galley / flagship; a floating fortress."),
    "Drakkar": VesselType("Drakkar", "water", 50.0, 9000, 14.0, 1.45,
                          ("sea", "coast", "river"), crew=60, addon_slots=5,
                          note="A great longship; ocean raider that also rows up "
                               "rivers to reach inland prey."),
}


@dataclass(frozen=True)
class Addon:
    name: str
    cost_gp: int
    applies_to: Tuple[str, ...]   # categories it can be fitted to
    capacity_mult: float = 1.0
    speed_mult: float = 1.0
    defense: int = 0              # bonus to defending the cargo / the ship (combat)
    attack: int = 0               # offensive rating in ship-to-ship naval combat
    hidden_tons: float = 0.0      # concealed capacity (smuggling)
    note: str = ""


ADDONS: Dict[str, Addon] = {
    "Reinforced Frame": Addon("Reinforced Frame", 80, ("land", "water"),
                              capacity_mult=1.25, speed_mult=0.95,
                              note="Stronger axles/hull; more load, a touch slower."),
    "Cargo Expansion": Addon("Cargo Expansion", 120, ("land", "water"),
                             capacity_mult=1.4, speed_mult=0.9,
                             note="Extra holds/racks at the cost of speed."),
    "Armed Escort": Addon("Armed Escort", 200, ("pack", "land", "water"),
                          defense=2, note="Hired guards; harder to rob."),
    "Draft Team Upgrade": Addon("Draft Team Upgrade", 100, ("land",),
                                speed_mult=1.3, note="Better animals; faster hauling."),
    "Extra Sail": Addon("Extra Sail", 300, ("water",), speed_mult=1.3,
                        note="More canvas; faster but more crew-hungry."),
    "Ram": Addon("Ram", 250, ("water",), defense=1, attack=2,
                 note="Bronze beak for naval combat (ship-to-ship)."),
    "Smuggling Compartment": Addon("Smuggling Compartment", 150,
                                   ("land", "water"), hidden_tons=0.5,
                                   note="A false bottom for contraband."),
    "Waterproofing": Addon("Waterproofing", 60, ("land", "water"),
                           note="Tarred seams/oilcloth; cargo survives a soaking."),
    "Weather Cover": Addon("Weather Cover", 40, ("land",),
                           note="Canvas tilt; protects goods from sun and rain."),
    # --- naval armaments (offensive fittings; cost an addon slot) ---
    "Ballista": Addon("Ballista", 400, ("water",), attack=2,
                      note="Deck bolt-thrower; ranged ship-to-ship, punches hull and crew."),
    "Catapult": Addon("Catapult", 800, ("water",), attack=3, speed_mult=0.95,
                      note="Heavy stone/fire thrower; smashes decks at range (weighty)."),
    "Marine Complement": Addon("Marine Complement", 500, ("water",),
                               attack=2, defense=2,
                               note="A company of fighting marines; boards enemies and "
                                    "repels boarders."),
    "Boarding Gear": Addon("Boarding Gear", 150, ("water",), attack=1,
                           note="Grapples, hooks and a corvus ramp; lets your crew swarm "
                                "an enemy deck."),
    "Fire Siphon": Addon("Fire Siphon", 1200, ("water",), attack=3,
                         note="Naphtha 'sea-fire' projector; devastating incendiary, "
                              "and dangerous to all."),
    "Fighting Castles": Addon("Fighting Castles", 600, ("water",),
                              attack=1, defense=2, speed_mult=0.95,
                              note="Raised fore/stern castles; height for archers, "
                                   "harder to board."),
    "Iron Plating": Addon("Iron Plating", 700, ("water",), defense=3, speed_mult=0.9,
                          note="Iron-banded hull; shrugs rams and missiles, heavier "
                               "and slower."),
}


@dataclass
class Vessel:
    """A configured carrier: a chassis plus fitted addons."""
    vtype: VesselType
    addons: List[Addon] = field(default_factory=list)

    @property
    def capacity_tons(self) -> float:
        cap = self.vtype.capacity_tons
        for a in self.addons:
            cap *= a.capacity_mult
        cap += sum(a.hidden_tons for a in self.addons)
        return round(cap, 3)

    @property
    def speed_factor(self) -> float:
        s = self.vtype.speed_factor
        for a in self.addons:
            s *= a.speed_mult
        return round(s, 3)

    @property
    def defense(self) -> int:
        return sum(a.defense for a in self.addons)

    @property
    def total_cost(self) -> int:
        return self.vtype.cost_gp + sum(a.cost_gp for a in self.addons)

    def can_traverse(self, terrain: str) -> bool:
        return self.vtype.can_traverse(terrain)


def get(name: str) -> Optional[VesselType]:
    return VESSELS.get(name) or next(
        (v for k, v in VESSELS.items() if k.lower() == (name or "").lower()), None)


def fit(name: str, addon_names: Optional[List[str]] = None) -> Optional[Vessel]:
    vt = get(name)
    if not vt:
        return None
    chosen = []
    for an in (addon_names or []):
        a = ADDONS.get(an)
        if a and vt.category in a.applies_to and len(chosen) < vt.addon_slots:
            chosen.append(a)
    return Vessel(vtype=vt, addons=chosen)


def vessels_for_terrain(terrain: str) -> List[str]:
    return [name for name, v in VESSELS.items() if v.can_traverse(terrain)]
