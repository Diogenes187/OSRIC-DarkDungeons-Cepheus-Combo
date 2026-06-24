"""trade.py -- caravan/shipping speculative trade (Cepheus-adapted, medieval).

Buy a good cheap where it's produced, haul it (by whatever vessel suits the
route), sell it dear where it's demanded. Prices come from a 2d6 haggle check
plus the trader's CHARISMA modifier (OSRIC's reaction adjustment, finally
mechanical) and the good's supply/demand modifiers for the settlement's economy.

Pricing model (per Cepheus): a check indexes a Modified Price table for a
percentage of base price.
  purchase result = 2d6 + haggle(CHA) + (where it's abundant) - (where it's wanted)
  sale result     = 2d6 + haggle(CHA) + (where it's wanted)   - (where it's abundant)
Higher result is better for the trader (buy cheaper / sell dearer).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .dice import Dice

# Settlement economy profiles (a town can have several).
ECONOMIES = ["Agricultural", "Pastoral", "Forest", "Mining", "Coastal", "Port",
             "Craft", "Industrial", "Capital", "Rich", "Frontier", "Poor"]

# Modified Price table: haggle result -> (purchase %, sale %) of base price.
PRICE_TABLE = {
    2: (175, 30), 3: (150, 40), 4: (135, 50), 5: (125, 60), 6: (115, 70),
    7: (110, 80), 8: (105, 90), 9: (100, 100), 10: (95, 110), 11: (90, 120),
    12: (85, 130), 13: (80, 140), 14: (75, 150), 15: (70, 160), 16: (60, 175),
}


@dataclass(frozen=True)
class TradeGood:
    name: str
    base_price: int               # gp per ton
    tons_dice: str                # how much is available in a lot
    abundant: Dict[str, int]      # economies where it's produced (cheap to buy)
    wanted: Dict[str, int]        # economies where it's demanded (dear to sell)


# gp/ton base prices and where each good is produced vs. demanded.
GOODS: Dict[str, TradeGood] = {
    "Grain":     TradeGood("Grain", 10, "3d6", {"Agricultural": 3, "Pastoral": 1},
                           {"Mining": 2, "Frontier": 3, "Capital": 1, "Port": 1}),
    "Livestock": TradeGood("Livestock", 60, "2d6", {"Pastoral": 3, "Agricultural": 1},
                           {"Capital": 2, "Mining": 1, "Frontier": 2}),
    "Wool":      TradeGood("Wool", 50, "2d6", {"Pastoral": 3, "Frontier": 1},
                           {"Craft": 3, "Industrial": 2, "Capital": 1}),
    "Timber":    TradeGood("Timber", 15, "3d6", {"Forest": 3},
                           {"Mining": 1, "Port": 2, "Capital": 2, "Craft": 1}),
    "Furs":      TradeGood("Furs", 200, "1d6", {"Forest": 3, "Frontier": 2},
                           {"Capital": 3, "Rich": 3, "Craft": 1}),
    "Honey":     TradeGood("Honey", 40, "1d6", {"Forest": 2, "Agricultural": 2},
                           {"Capital": 1, "Craft": 1}),
    "Iron":      TradeGood("Iron", 100, "2d6", {"Mining": 3, "Industrial": 1},
                           {"Craft": 3, "Frontier": 2, "Capital": 1}),
    "Salt":      TradeGood("Salt", 30, "2d6", {"Mining": 2, "Coastal": 3},
                           {"Frontier": 3, "Agricultural": 2, "Forest": 1}),
    "Gems":      TradeGood("Gems", 800, "1d4", {"Mining": 3, "Frontier": 1},
                           {"Capital": 3, "Rich": 3}),
    "Cloth":     TradeGood("Cloth", 120, "2d6", {"Craft": 3, "Industrial": 2},
                           {"Capital": 2, "Frontier": 2, "Pastoral": 1, "Rich": 1}),
    "Tools":     TradeGood("Tools", 150, "1d6", {"Craft": 3, "Industrial": 3},
                           {"Frontier": 3, "Agricultural": 2, "Mining": 1}),
    "Weapons":   TradeGood("Weapons", 300, "1d6", {"Craft": 2, "Industrial": 3},
                           {"Frontier": 3, "Capital": 1}),
    "Pottery":   TradeGood("Pottery", 40, "2d6", {"Craft": 3},
                           {"Frontier": 2, "Agricultural": 1, "Capital": 1}),
    "Wine":      TradeGood("Wine", 80, "2d6", {"Agricultural": 3, "Coastal": 1},
                           {"Capital": 3, "Rich": 2, "Frontier": 1, "Mining": 1}),
    "Mead":      TradeGood("Mead", 45, "2d6", {"Agricultural": 2, "Forest": 1},
                           {"Mining": 2, "Frontier": 2, "Port": 1}),
    "Spices":    TradeGood("Spices", 500, "1d6", {"Port": 3, "Coastal": 1},
                           {"Capital": 3, "Rich": 3, "Craft": 1}),
    "Dyes":      TradeGood("Dyes", 250, "1d4", {"Port": 2, "Craft": 2},
                           {"Capital": 2, "Craft": 1, "Rich": 2}),
    "Oil":       TradeGood("Oil", 60, "2d6", {"Agricultural": 2, "Coastal": 1},
                           {"Mining": 1, "Capital": 1, "Frontier": 1}),
    "Horses":    TradeGood("Horses", 120, "1d4", {"Pastoral": 3, "Frontier": 1},
                           {"Capital": 2, "Industrial": 1, "Frontier": 2}),
    "Cheese":    TradeGood("Cheese", 50, "2d6", {"Pastoral": 2, "Agricultural": 1},
                           {"Mining": 1, "Capital": 1, "Frontier": 1}),
    "Fish":      TradeGood("Fish", 35, "2d6", {"Coastal": 3, "Port": 1},
                           {"Mining": 2, "Frontier": 1, "Capital": 1}),
    "Leather":   TradeGood("Leather", 70, "2d6", {"Pastoral": 2, "Frontier": 2},
                           {"Craft": 3, "Industrial": 1, "Capital": 1}),
    "Spirits":   TradeGood("Spirits", 110, "1d6", {"Agricultural": 2, "Craft": 1},
                           {"Frontier": 3, "Mining": 2, "Port": 1}),
    "Copper":    TradeGood("Copper", 150, "2d6", {"Mining": 3, "Industrial": 1},
                           {"Craft": 3, "Industrial": 1, "Capital": 1}),
    "Silver":    TradeGood("Silver", 400, "1d4", {"Mining": 3},
                           {"Craft": 2, "Capital": 2, "Rich": 2}),
    "Glassware": TradeGood("Glassware", 180, "1d6", {"Craft": 3, "Industrial": 1},
                           {"Rich": 2, "Capital": 2, "Frontier": 1}),
    "Silk":      TradeGood("Silk", 450, "1d4", {"Port": 3, "Craft": 1},
                           {"Rich": 3, "Capital": 3}),
    "Ivory":     TradeGood("Ivory", 600, "1d4", {"Port": 2, "Frontier": 1},
                           {"Rich": 3, "Capital": 2, "Craft": 1}),
    "Incense":   TradeGood("Incense", 350, "1d4", {"Port": 3, "Coastal": 1},
                           {"Rich": 2, "Capital": 2, "Craft": 1}),
    "Artwork":   TradeGood("Artwork", 700, "1d4", {"Craft": 2, "Capital": 1},
                           {"Rich": 3, "Capital": 2}),
    "Pemmican":  TradeGood("Pemmican", 90, "2d6", {"Pastoral": 2, "Agricultural": 1},
                           {"Port": 3, "Frontier": 3, "Mining": 2, "Capital": 1}),
}


def haggle_dm(charisma: int) -> int:
    """OSRIC Charisma as a 2d6 haggle modifier."""
    if charisma <= 5:
        return -2
    if charisma <= 8:
        return -1
    if charisma <= 12:
        return 0
    if charisma <= 15:
        return 1
    if charisma <= 17:
        return 2
    return 3


def _best(dms: Dict[str, int], economies: List[str]) -> int:
    hits = [dm for econ, dm in dms.items() if econ in economies]
    return max(hits) if hits else 0


def _pct(result: int, sale: bool) -> int:
    result = max(2, min(16, result))
    return PRICE_TABLE[result][1 if sale else 0]


@dataclass
class Quote:
    good: str
    result: int
    percent: int
    price_per_ton: int


def _quote(dice: Dice, good: TradeGood, economies: List[str], charisma: int,
           selling: bool) -> Quote:
    # Deterministic price: NO hidden 2d6 re-roll. The number market_goods shows
    # is exactly what buy_goods / sell_goods charges, because price is now a pure
    # function of base value, local supply/demand, and the trader's Charisma.
    # (7 is the fixed centre of the old 2d6 haggle; `dice` kept for signature.)
    check = 7 + haggle_dm(charisma)
    abundant = _best(good.abundant, economies)
    wanted = _best(good.wanted, economies)
    if selling:
        result = check + wanted - abundant
        pct = _pct(result, sale=True)
    else:
        result = check + abundant - wanted
        pct = _pct(result, sale=False)
    return Quote(good.name, result, pct, max(1, round(good.base_price * pct / 100)))


def purchase_price(dice: Dice, good: str, economies: List[str],
                   charisma: int = 10) -> Optional[Quote]:
    g = GOODS.get(good)
    return _quote(dice, g, economies, charisma, selling=False) if g else None


def sale_price(dice: Dice, good: str, economies: List[str],
               charisma: int = 10) -> Optional[Quote]:
    g = GOODS.get(good)
    return _quote(dice, g, economies, charisma, selling=True) if g else None


def available_goods(dice: Dice, economies: List[str],
                    count: Optional[int] = None) -> List[Dict[str, object]]:
    """What a market offers: goods abundant in this economy, plus a couple of
    others passing through. Returns name + available tons."""
    local = [g for g in GOODS.values() if _best(g.abundant, economies) > 0]
    others = [g for g in GOODS.values() if g not in local]
    dice.rng.shuffle(others)
    # Show everything a town actually produces, plus a handful of goods passing
    # through, soft-capped at a dozen so even a rich port stays readable.
    pool = local + others[:6]
    n = count if count is not None else min(len(pool), 12)
    out = []
    for g in pool[:n]:
        out.append({"good": g.name, "base_price": g.base_price,
                    "tons_available": dice.notation(g.tons_dice).total})
    return out
