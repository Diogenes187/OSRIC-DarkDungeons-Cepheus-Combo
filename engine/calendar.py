"""calendar.py -- the Flanaess (World of Greyhawk) calendar and time advancement.

The Common Year (CY) is 364 days: twelve 28-day months with a 7-day festival
between each season. Dates read "Reaping 4, 576 CY". advance() moves a date
forward by whole days, rolling through months, festivals, and years.

(Stray dates from other reckonings -- e.g. an old 'AS' suffix -- simply fail to
parse, so callers fall back to the campaign's default start date.)
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

# (name, length) in calendar order.
MONTHS = [
    ("Needfest", 7),  ("Fireseek", 28),  ("Readying", 28),   ("Coldeven", 28),
    ("Growfest", 7),  ("Planting", 28),  ("Flocktime", 28),  ("Wealsun", 28),
    ("Richfest", 7),  ("Reaping", 28),   ("Goodmonth", 28),  ("Harvester", 28),
    ("Brewfest", 7),  ("Patchwall", 28), ("Ready'reat", 28), ("Sunsebb", 28),
]
YEAR_DAYS = sum(length for _, length in MONTHS)     # 364
_INDEX = {name.lower(): i for i, (name, _) in enumerate(MONTHS)}

_DATE = re.compile(r"^\s*([A-Za-z'’]+)\s+(\d{1,2})\s*,\s*(\d+)\s*(CY)?\s*$")


def parse(date_str: str) -> Optional[Tuple[int, int, int]]:
    """'Reaping 4, 576 CY' -> (month_index, day, year), or None."""
    m = _DATE.match(date_str or "")
    if not m:
        return None
    mi = _INDEX.get(m.group(1).replace("’", "'").lower())
    if mi is None:
        return None
    return mi, int(m.group(2)), int(m.group(3))


def format_date(month_index: int, day: int, year: int) -> str:
    return "{} {}, {} CY".format(MONTHS[month_index][0], day, year)


def advance(date_str: str, days: int) -> Optional[str]:
    """Move a date forward by `days` whole days."""
    parsed = parse(date_str)
    if parsed is None:
        return None
    mi, day, year = parsed
    offset = sum(length for _, length in MONTHS[:mi]) + (day - 1) + int(days)
    year += offset // YEAR_DAYS
    doy = offset % YEAR_DAYS
    for i, (_, length) in enumerate(MONTHS):
        if doy < length:
            return format_date(i, doy + 1, year)
        doy -= length
    return format_date(0, 1, year)                  # unreachable


def is_festival(date_str: str) -> bool:
    p = parse(date_str)
    return p is not None and MONTHS[p[0]][1] == 7
