"""dominion_events.py -- premade yearly Dominion Events (Dark Dungeons ch.13).

Each year a dominion sees 1d4 random events. The d100 TYPE_TABLE decides the
flavour (major/minor positive, neutral, major/minor negative, disaster); a
PREMADE deck of concrete events is then drawn from for that category -- so the
table is rolled, never invented at the table. Each event carries bounded
effects: a Confidence shift, a one-month income modifier (percent), and a
population change (percent), all within the category's caps.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# d100 -> category (bands made contiguous; the source leaves 21-24 implied).
TYPE_TABLE: List[Tuple[int, str]] = [
    (5, "major_positive"),
    (24, "minor_positive"),
    (40, "neutral"),
    (75, "minor_negative"),
    (95, "major_negative"),
    (100, "disaster"),
]

CATEGORY_LABEL = {
    "major_positive": "Major Positive Event",
    "minor_positive": "Minor Positive Event",
    "neutral": "Neutral Event",
    "minor_negative": "Minor Negative Event",
    "major_negative": "Major Negative Event",
    "disaster": "Disaster",
}


def category_for(roll: int) -> str:
    for top, cat in TYPE_TABLE:
        if roll <= top:
            return cat
    return "disaster"


# Premade decks. Each: (name, confidence, income_pct, population_pct, description)
EVENTS: Dict[str, List[Tuple[str, int, int, int, str]]] = {
    "major_positive": [
        ("New Resource Discovered", 10, 50, 0,
         "Prospectors strike a new vein of ore or a rich timber stand."),
        ("Ancient Treasure Unearthed", 15, 100, 0,
         "Labourers uncover a buried hoard on the ruler's land."),
        ("A Power Takes Patronage", 25, 0, 10,
         "A deity or great lord adopts the dominion as a favoured cause."),
        ("Demi-human Refugees Settle", 10, 0, 25,
         "A clan of dwarves or gnomes, displaced elsewhere, asks to settle."),
        ("Bumper Harvest", 15, 75, 10,
         "A perfect season fills every granary to bursting."),
    ],
    "minor_positive": [
        ("New Trade Route Proposed", 10, 50, 0,
         "Merchants seek to run a caravan road through the dominion."),
        ("Hostile Tribe Departs", 10, 0, 0,
         "A troublesome humanoid tribe migrates out of the region."),
        ("Wandering Heroes Clear Bandits", 15, 0, 0,
         "Passing adventurers rout the local brigands, asking nothing."),
        ("A Druid Settles Nearby", 5, 0, 5,
         "A druid takes up the warding of the dominion's wild marches."),
        ("Fair Weather", 5, 25, 0,
         "Gentle seasons ease the work of field and road."),
    ],
    "neutral": [
        ("A VIP Visitor Arrives", 5, -10, 0,
         "An unexpected dignitary must be hosted -- at some expense."),
        ("Omens in the Sky", -5, 0, 0,
         "Comets and portents trouble the superstitious folk."),
        ("Heresy in a Local Church", -10, 0, 0,
         "A doctrinal scandal sets the faithful at odds."),
        ("A Tribe is Displaced Inward", 0, 0, 5,
         "Folk fleeing a neighbour's war drift into the dominion."),
        ("Border Dispute", -5, 0, 0,
         "A quarrel with a neighbour over a boundary stone festers."),
    ],
    "minor_negative": [
        ("Bandits Begin Raiding", -10, -25, 0,
         "Brigands prey on the roads and outlying farms."),
        ("An Official is Assassinated", -15, 0, 0,
         "A trusted reeve or steward is found murdered."),
        ("Monsters Infest the Wilds", -10, -10, 0,
         "Low-level beasts den in the borderlands and harry travellers."),
        ("A Disease Breaks Out", -10, 0, -5,
         "A sickness spreads through a crowded quarter."),
        ("Poor Weather", -5, -25, 0,
         "Cold rains and blight thin the season's yield."),
    ],
    "major_negative": [
        ("A Fief's Resource Runs Out", -10, -50, 0,
         "A mine plays out or a forest is logged bare."),
        ("An Epidemic Strikes", -15, 0, -15,
         "A virulent plague races through the dominion."),
        ("A Powerful Monster Stalks the Land", -20, -25, 0,
         "A high-level predator makes the roads deadly."),
        ("Agitators Foment Rebellion", -25, 0, 0,
         "Rabble-rousers turn the populace against the ruler."),
        ("A Great Fire", -15, -40, -5,
         "Flames sweep a town, gutting homes and warehouses."),
    ],
    "disaster": [
        ("Plague Sweeps the Dominion", -25, -50, -25,
         "A great pestilence empties whole villages."),
        ("A Dragon Descends", -25, -50, -10,
         "A wyrm claims the dominion as its hunting ground."),
        ("Earthquake", -20, -60, -10,
         "The earth heaves; walls and bridges fall."),
        ("Tempest Sweeps the Land", -20, -75, -15,
         "A hurricane, tornado, or avalanche devastates the region."),
        ("A Dark Power Smites the Land", -25, -50, -20,
         "A vengeful Power blights field, beast, and folk alike."),
    ],
}
