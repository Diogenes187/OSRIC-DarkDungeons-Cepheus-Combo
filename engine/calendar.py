"""calendar.py -- The Known World calendar and time advancement.

Years are reckoned After the Sundering (AS): the cataclysm is year 0, "before"
is BS, and the campaign opens in 211 AS. The year is 364 days -- twelve 28-day
months with a 7-day festival between each season. Dates read "Longlight 13,
211 AS". advance() moves a date forward by whole days, rolling through months,
festivals, and years.

Legacy Flanaess month names and the 'CY' suffix still PARSE (they occupy the
same 16 ordinal slots), so any old saved date converts cleanly into the Known
World calendar.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

# (name, length) in calendar order: a season's festival, then its three months.
MONTHS = [
    ("Emberwake", 7),  ("Frostmere", 28), ("Ironnight", 28), ("Lastfrost", 28),    # winter
    ("Greenwake", 7),  ("Seedfall", 28),  ("Rainmoot", 28),  ("Blossomtide", 28),  # spring
    ("Highmere", 7),   ("Longlight", 28), ("Highsun", 28),   ("Goldgrass", 28),    # summer
    ("Reckoning", 7),  ("Harvestide", 28),("Duskfall", 28),  ("Greymoot", 28),     # autumn
]
YEAR_DAYS = sum(length for _, length in MONTHS)     # 364
_INDEX = {name.lower(): i for i, (name, _) in enumerate(MONTHS)}

# Legacy Flanaess names occupy the SAME ordinal slots, so "Reaping 13, 576 CY"
# parses to the matching Known World month (Longlight) and can be re-dated to AS.
_LEGACY = ["Needfest", "Fireseek", "Readying", "Coldeven", "Growfest", "Planting",
           "Flocktime", "Wealsun", "Richfest", "Reaping", "Goodmonth", "Harvester",
           "Brewfest", "Patchwall", "Ready'reat", "Sunsebb"]
for _i, _name in enumerate(_LEGACY):
    _INDEX.setdefault(_name.lower(), _i)

_DATE = re.compile(r"^\s*([A-Za-z'’]+)\s+(\d{1,2})\s*,\s*(\d+)\s*(AS|BS|CY)?\s*$")


def parse(date_str: str) -> Optional[Tuple[int, int, int]]:
    """'Longlight 13, 211 AS' (or a legacy 'Reaping 13, 576 CY') -> (month_index, day, year)."""
    m = _DATE.match(date_str or "")
    if not m:
        return None
    mi = _INDEX.get(m.group(1).replace("’", "'").lower())
    if mi is None:
        return None
    return mi, int(m.group(2)), int(m.group(3))


def format_date(month_index: int, day: int, year: int) -> str:
    return "{} {}, {} AS".format(MONTHS[month_index][0], day, year)


def advance(date_str: str, days: int) -> Optional[str]:
    """Move a date forward by `days` whole days."""
    parsed = parse(date_str)
    if parsed is None:
        return None
    mi, day, year = parsed
    # absolute day-of-year (0-based) + days, then re-decompose
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
