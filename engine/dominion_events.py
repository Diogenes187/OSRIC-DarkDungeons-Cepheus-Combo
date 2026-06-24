"""dominion_events.py -- roll a dominion's yearly events (deterministic, seeded).

Rolls 1d4 events (or a given count), each a d100 on the type table followed by a
draw from that category's premade deck. Pure rolling; the caller applies the
effects to the dominion record.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .data import dominion_events as deck


def roll_yearly(dice, count: Optional[int] = None) -> Dict[str, Any]:
    n = int(count) if count else dice.d4()
    events: List[Dict[str, Any]] = []
    for _ in range(max(1, n)):
        r = dice.d100()
        cat = deck.category_for(r)
        pool = deck.EVENTS[cat]
        name, conf, income, pop, desc = pool[dice.d(len(pool)) - 1]
        events.append({
            "type_roll": r, "category": cat,
            "category_label": deck.CATEGORY_LABEL[cat],
            "event": name, "description": desc,
            "confidence": conf, "income_pct": income, "population_pct": pop,
        })
    return {"count": len(events), "events": events,
            "total_confidence": sum(e["confidence"] for e in events)}
