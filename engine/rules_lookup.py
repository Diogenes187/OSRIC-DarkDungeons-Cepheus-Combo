"""rules_lookup.py -- the referee's two lookup paths, cleanly separated.

  rules(q)  -> OSRIC 3.0 text  (AUTHORITATIVE: matches the engine exactly)
  lore(q)   -> 1e / Greyhawk corpus  (SUPPLEMENTARY: setting, monsters, items, deities)

The referee is told: engine-computed numbers are final; `rules` is the rules
reference; `lore` is flavour and content the engine doesn't model. Every result
is source-labelled so provenance is always visible.
"""
from __future__ import annotations

from typing import Dict, List

from . import osric_text
from . import corpus


def rules(query: str, limit: int = 4) -> List[Dict[str, str]]:
    return [{"source": h.source, "text": h.snippet}
            for h in osric_text.search(query, limit)]


def lore(query: str, limit: int = 4) -> List[Dict[str, str]]:
    return [{"source": "{} — {}".format(h.source_book or "1e", h.title or ""),
             "text": h.snippet}
            for h in corpus.search(query, limit)]


def status() -> Dict[str, bool]:
    return {"rules_available": osric_text.available(),
            "lore_available": corpus.available()}
