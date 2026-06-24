"""corpus.py -- the rules-lookup oracle over the 1e reference corpus.

Searches the uploaded `adnd_1e.db` (≈7,000 OCR'd/scraped rulebook pages with an
FTS5 full-text index) so the AI referee can ground its rulings in the actual
books -- PHB, DMG, UA, the Monster Manuals, the World of Greyhawk folio -- rather
than inventing rules. Read-only; never written to.

Set GREYHAWK_CORPUS to point at the db, or drop adnd_1e.db beside the project.
"""
from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from typing import List, Optional

# Candidate locations: env override, project root, the OSRIC folder (one up).
_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [
    os.environ.get("GREYHAWK_CORPUS", ""),
    os.path.join(_HERE, "..", "adnd_1e.db"),
    os.path.join(_HERE, "..", "..", "adnd_1e.db"),
]


def corpus_path() -> Optional[str]:
    for c in _CANDIDATES:
        if c and os.path.exists(c):
            return os.path.normpath(c)
    return None


@dataclass
class Hit:
    source_book: str
    title: str
    url: str
    snippet: str


def _snippet(text: str, query: str, width: int = 220) -> str:
    """A readable window of `text` around the first query keyword."""
    text = re.sub(r"\s+", " ", text or "").strip()
    terms = [t for t in re.findall(r"[A-Za-z]+", query) if len(t) > 2]
    lo = -1
    for t in terms:
        m = re.search(re.escape(t), text, re.I)
        if m:
            lo = m.start()
            break
    if lo < 0:
        return text[:width] + ("…" if len(text) > width else "")
    start = max(0, lo - width // 3)
    end = min(len(text), start + width)
    return ("…" if start else "") + text[start:end] + ("…" if end < len(text) else "")


def available() -> bool:
    return corpus_path() is not None


def search(query: str, limit: int = 5, db_path: Optional[str] = None) -> List[Hit]:
    """Full-text search the corpus. Falls back to LIKE if FTS is unavailable."""
    path = db_path or corpus_path()
    if not path:
        return []
    conn = sqlite3.connect(path)
    try:
        rows = []
        try:
            rows = conn.execute(
                "SELECT p.source_book, p.title, p.url, p.clean_text "
                "FROM pages_fts f JOIN pages p ON p.rowid = f.rowid "
                "WHERE pages_fts MATCH ? ORDER BY rank LIMIT ?",
                (query, limit)).fetchall()
        except sqlite3.OperationalError:
            like = "%{}%".format(query)
            rows = conn.execute(
                "SELECT source_book, title, url, clean_text FROM pages "
                "WHERE clean_text LIKE ? LIMIT ?", (like, limit)).fetchall()
        return [Hit(source_book=r[0] or "", title=r[1] or "", url=r[2] or "",
                    snippet=_snippet(r[3] or "", query)) for r in rows]
    finally:
        conn.close()
