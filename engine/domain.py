"""domain.py -- dominion economy (Dark Dungeons "Strongholds & Dominions").

A ruler's dominion is one or more fiefs. Each game month you run a turn: tally
income (worked resources, service, poll tax), pay expenses (tithes, salt tax to
your liege, troops, festivals), and the population grows. Confidence tracks how
content the populace is and shifts with taxation and rule. Deterministic from a
seeded Dice -- the buggy hand-bookkeeping made solid.

Income per family by worked resource: animal 2gp, vegetable 1gp, mineral 3gp.
Service income is 10gp/family (offsets expenses, never banked). Poll tax is the
ruler's coin (default 1gp/family). Tithes take 10% of GROSS (cash+service), salt
tax 20%. XP equals gross CASH income (resources + poll tax).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .dice import Dice

RESOURCE_GP = {"animal": 2, "vegetable": 1, "mineral": 3}

# civ level -> (settling dice, multiplier, max families per fief)
CIV_LEVELS = {
    "wilderness": ("1d10", 10, 1500),
    "borderlands": ("2d6", 100, 3000),
    "civilized": ("1d10", 500, 6000),
}

# (family ceiling, monthly growth %)
_POP_GROWTH = [(100, 25), (200, 20), (300, 15), (400, 10), (500, 5),
               (750, 3), (1000, 2), (10**9, 1)]


def _resource_count(d10: int) -> int:
    if d10 == 1:
        return 1
    if d10 <= 7:
        return 2
    if d10 <= 9:
        return 3
    return 4


def _resource_type(d10: int) -> str:
    if d10 <= 3:
        return "animal"
    if d10 <= 8:
        return "vegetable"
    return "mineral"


@dataclass
class Fief:
    terrain: str
    civ_level: str
    families: int
    resources: List[str] = field(default_factory=list)

    @property
    def max_families(self) -> int:
        return CIV_LEVELS.get(self.civ_level, CIV_LEVELS["wilderness"])[2]

    def resource_income(self) -> int:
        if not self.resources:
            return 0
        per = self.families / len(self.resources)
        return round(sum(per * RESOURCE_GP[r] for r in self.resources))

    def service_income(self) -> int:
        return 10 * self.families

    def poll_tax(self, rate_gp: float) -> int:
        return round(rate_gp * self.families)


def found_fief(dice: Dice, terrain: str, civ_level: str = "wilderness") -> Fief:
    sett_dice, mult, _ = CIV_LEVELS.get(civ_level, CIV_LEVELS["wilderness"])
    families = dice.notation(sett_dice).total * mult
    n = _resource_count(dice.d10())
    resources = [_resource_type(dice.d10()) for _ in range(n)]
    return Fief(terrain=terrain, civ_level=civ_level, families=families,
                resources=resources)


@dataclass
class Troop:
    name: str
    count: int
    cost_each: int          # gp/month


@dataclass
class Dominion:
    name: str
    fiefs: List[Fief] = field(default_factory=list)
    confidence: int = 50
    tax_rate_gp: float = 1.0
    has_liege: bool = True
    troops: List[Troop] = field(default_factory=list)

    @property
    def families(self) -> int:
        return sum(f.families for f in self.fiefs)


def _grow(dice: Dice, fief: Fief) -> None:
    pct = next(g for cap, g in _POP_GROWTH if fief.families <= cap)
    fief.families = round(fief.families * (1 + pct / 100.0))
    if fief.families < 250:                     # small fiefs see random swings
        delta = dice.notation("1d10").total
        fief.families += delta if dice.d6() >= 4 else -delta
    fief.families = max(0, min(fief.families, fief.max_families))


def monthly_turn(dice: Dice, dom: Dominion, festivals: int = 0,
                 extra_expenses: int = 0) -> Dict[str, Any]:
    """Run one month: tally income & expenses, grow population, return a report.

    `extra_expenses` covers one-offs like entertaining visiting nobles (see
    TITLES) or rebuilding after a siege."""
    resource_income = sum(f.resource_income() for f in dom.fiefs)
    service = sum(f.service_income() for f in dom.fiefs)
    poll = sum(f.poll_tax(dom.tax_rate_gp) for f in dom.fiefs)

    # A discontented populace pays less (or nothing, in open revolt).
    factor = income_factor(dom.confidence)
    resource_income = round(resource_income * factor)
    service = round(service * factor)
    poll = round(poll * factor)

    gross_cash = resource_income + poll
    gross_total = gross_cash + service
    tithe = round(0.10 * gross_total)
    salt_tax = round(0.20 * gross_total) if dom.has_liege else 0
    festival_cost = 5 * dom.families * max(0, festivals)
    troop_cost = sum(t.count * t.cost_each for t in dom.troops)
    expenses = tithe + salt_tax + festival_cost + troop_cost + max(0, extra_expenses)

    # Expenses draw on (un-bankable) service income first, then cash.
    from_service = min(service, expenses)
    from_cash = expenses - from_service
    net_cash = gross_cash - from_cash
    xp = gross_cash                              # cash income earns the ruler XP

    before = dom.families
    for f in dom.fiefs:
        _grow(dice, f)

    return {
        "dominion": dom.name, "families": before,
        "income": {"resources": resource_income, "service": service,
                   "poll_tax": poll, "gross_cash": gross_cash},
        "expenses": {"tithe": tithe, "salt_tax": salt_tax,
                     "festivals": festival_cost, "troops": troop_cost,
                     "other": max(0, extra_expenses), "total": expenses},
        "net_cash": net_cash, "xp": xp, "confidence": dom.confidence,
        "confidence_level": confidence_level(dom.confidence),
        "population_after": dom.families,
    }


# --- Confidence (the populace's contentment; low enough = revolt) -----------
# (rating ceiling, level name)
CONFIDENCE_LEVELS = [
    (49, "Turbulent"), (99, "Belligerent"), (149, "Rebellious"), (199, "Defiant"),
    (229, "Unsteady"), (269, "Average"), (299, "Steady"), (349, "Healthy"),
    (399, "Prosperous"), (449, "Thriving"), (10**9, "Ideal"),
]
# How much income a dominion can collect at each level.
_INCOME_FACTOR = {
    "Turbulent": 0.0, "Belligerent": 0.25, "Rebellious": 0.33, "Defiant": 0.5,
    "Unsteady": 0.9, "Average": 1.0, "Steady": 1.0, "Healthy": 1.1,
    "Prosperous": 1.1, "Thriving": 1.1, "Ideal": 1.1,
}


def confidence_level(rating: int) -> str:
    for ceiling, name in CONFIDENCE_LEVELS:
        if rating <= ceiling:
            return name
    return "Ideal"


def income_factor(rating: int) -> float:
    return _INCOME_FACTOR[confidence_level(rating)]


def initial_confidence(dice: Dice, ruler_ability_total: int) -> int:
    """A new dominion's confidence = ruler's six ability scores + 150 + d100."""
    return ruler_ability_total + 150 + dice.d100()


def in_revolt(dom: "Dominion") -> bool:
    """Turbulent (<=49): the populace is overthrowing the ruler."""
    return confidence_level(dom.confidence) == "Turbulent"


def set_tax_rate(dom: Dominion, new_rate_gp: float) -> int:
    """Change the poll-tax rate; returns the immediate Confidence shift and
    applies it. (Raising taxes angers the populace; lowering pleases them.)"""
    shift = 10 if new_rate_gp < dom.tax_rate_gp else (-25 if new_rate_gp > dom.tax_rate_gp else 0)
    dom.tax_rate_gp = new_rate_gp
    dom.confidence = max(0, dom.confidence + shift)
    return shift


# --- Stronghold construction (Stronghold Elements table) -------------------
STRONGHOLD_ELEMENTS = {
    "Arrow Slit": 10, "Barbican": 37000, "Battlement (100ft)": 500,
    "Building, Stone": 3000, "Building, Wood": 1500,
    "Door, Exterior Iron/Stone": 100, "Door, Interior Iron/Stone": 50,
    "Door, Interior Reinforced": 20, "Door, Interior Wood": 10,
    "Drawbridge": 250, "Dungeon Corridor": 500, "Floor, Flagstone": 100,
    "Floor, Tile": 100, "Floor, Wood": 40, "Gate, Wooden": 1000,
    "Gatehouse": 6500, "Keep, Square": 75000, "Moat, Filled": 800,
    "Moat, Unfilled": 400, "Shifting Wall": 1000, "Shutters, Window": 5,
    "Staircase, Stone": 60, "Staircase, Wood": 20, "Tower, Bastion": 9000,
    "Tower, Round Large": 30000, "Tower, Round Small": 15000,
    "Wall, Castle": 5000, "Wall, Wood": 1000, "Window, Barred": 20,
    "Window, Open": 10,
}
# Region cost modifier: remote-but-accessible is the baseline.
REGION_MULT = {"normal": 1.0, "remote": 1.0, "inaccessible": 2.0,
               "settled": 0.5, "heavily settled": 0.5}


def build_stronghold(elements: Dict[str, int], region: str = "normal") -> Dict[str, Any]:
    """Total cost, build time and engineers for a set of {element: quantity}.
    Build time is 1 day per 500gp; 1 engineer per 100,000gp of total cost."""
    mult = REGION_MULT.get((region or "normal").lower(), 1.0)
    total, breakdown, unknown = 0, [], []
    for name, qty in elements.items():
        unit = STRONGHOLD_ELEMENTS.get(name)
        if unit is None:
            unknown.append(name)
            continue
        line = round(unit * int(qty) * mult)
        total += line
        breakdown.append({"element": name, "qty": int(qty), "cost": line})
    days = -(-total // 500) if total else 0           # ceil(total/500)
    engineers = max(1, -(-total // 100000)) if total else 0
    return {"total_cost": total, "build_days": days, "engineers": engineers,
            "region": region, "breakdown": breakdown, "unknown": unknown}


# --- Titles of nobility (ascending), with entertaining-visitor cost/day ----
@dataclass
class Title:
    rank: int
    name: str
    dominions: str
    entertain_cost_day: int


TITLES = [
    Title(1, "Knight", "none (landless; sworn sword)", 0),
    Title(2, "Baron", "1 dominion (a barony)", 100),
    Title(3, "Viscount", "2 dominions", 150),
    Title(4, "Count", "3+ dominions (a county); one won by conquest", 300),
    Title(5, "Marquis", "a county plus continued expansion", 400),
    Title(6, "Duke", "a duchy (highest non-royal rank)", 600),
    Title(7, "Archduke", "a royal duke", 700),
    Title(8, "Prince", "a principality (royal blood)", 100),
    Title(9, "King", "an entire kingdom", 1000),
    Title(10, "Emperor", "an empire of client kingdoms", 1500),
]


def title(name: str) -> "Title":
    nl = (name or "").strip().lower()
    for t in TITLES:
        if t.name.lower() == nl:
            return t
    return TITLES[0]
