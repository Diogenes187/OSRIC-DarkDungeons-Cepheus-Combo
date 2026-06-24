"""osric_text.py -- the AUTHORITATIVE rules-lookup oracle, over the OSRIC 3.0 text.

The extracted OSRIC books (Player Guide, Gamemaster Guide, the four spellbooks)
are the rules source that exactly matches our engine. The referee searches THIS
for anything rules-shaped -- class abilities, spell effects, optional rules,
procedures -- and uses engine.corpus (the 1e/Greyhawk corpus) only for setting
lore and supplementary content. Engine-computed numbers always win over text.

Pure-Python keyword search over page-chunked text; no build step or DB needed.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
TEXT_DIR = os.path.normpath(os.path.join(_HERE, "..", "reference", "osric_text"))

_PAGE = re.compile(r"=====\s*PAGE\s+(\d+)\s*=====")
_WORD = re.compile(r"[A-Za-z][A-Za-z'-]+")


@dataclass
class Hit:
    source: str          # e.g. "OSRIC Player Guide p.13"
    snippet: str
    score: int


def _book_label(fn: str) -> str:
    name = fn.replace("OSRIC_3.0_", "").replace(".txt", "").replace("_", " ")
    return "OSRIC " + name


@lru_cache(maxsize=1)
def _chunks() -> Tuple[Tuple[str, int, str], ...]:
    """(book_label, page_number, page_text) for every page of the OSRIC books."""
    out: List[Tuple[str, int, str]] = []
    if not os.path.isdir(TEXT_DIR):
        return tuple(out)
    for fn in sorted(os.listdir(TEXT_DIR)):
        if not (fn.startswith("OSRIC_3.0_") and fn.endswith(".txt")):
            continue
        label = _book_label(fn)
        text = open(os.path.join(TEXT_DIR, fn), encoding="utf-8").read()
        parts = _PAGE.split(text)
        # parts = [pre, pageno, body, pageno, body, ...]
        for i in range(1, len(parts) - 1, 2):
            page = int(parts[i])
            body = parts[i + 1].strip()
            if body:
                out.append((label, page, body))
    return tuple(out)


def available() -> bool:
    return len(_chunks()) > 0


def _snippet(text: str, terms: List[str], width: int = 260) -> str:
    flat = re.sub(r"\s+", " ", text).strip()
    lo = -1
    for t in terms:
        m = re.search(re.escape(t), flat, re.I)
        if m:
            lo = m.start()
            break
    if lo < 0:
        return flat[:width]
    start = max(0, lo - width // 3)
    end = min(len(flat), start + width)
    return ("…" if start else "") + flat[start:end] + ("…" if end < len(flat) else "")


def search(query: str, limit: int = 4) -> List[Hit]:
    """Keyword search the OSRIC rules text; returns the best-matching pages."""
    terms = [t.lower() for t in _WORD.findall(query) if len(t) > 2]
    if not terms:
        return []
    scored: List[Hit] = []
    for label, page, body in _chunks():
        low = body.lower()
        score = sum(low.count(t) for t in terms)
        if score:
            scored.append(Hit(source="{} p.{}".format(label, page),
                              snippet=_snippet(body, terms), score=score))
    scored.sort(key=lambda h: h.score, reverse=True)
    return scored[:limit]
