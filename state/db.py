"""db.py -- SQLite connection and schema management for campaign state.

A single SQLite file is the campaign's source of truth. This module handles
connecting, initializing the schema (idempotently -- every connect re-runs the
`CREATE TABLE IF NOT EXISTS` script, so new tables auto-migrate), and giving
callers row-dict access.
"""
from __future__ import annotations

import os
import sqlite3

_SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")


def connect(path: str) -> sqlite3.Connection:
    """Open (creating if needed) a campaign database and ensure the schema."""
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_schema(conn)
    return conn


def connect_memory() -> sqlite3.Connection:
    """An in-memory database (tests / ephemeral use)."""
    return connect(":memory:")


def init_schema(conn: sqlite3.Connection) -> None:
    with open(_SCHEMA, encoding="utf-8") as f:
        conn.executescript(f.read())
    _migrate(conn)
    conn.commit()


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns to existing databases that the schema gained over time
    (CREATE TABLE IF NOT EXISTS won't alter an existing table)."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(character)")}
    if "damage_dice" not in cols:
        conn.execute("ALTER TABLE character ADD COLUMN damage_dice TEXT")
    if "cargo_json" not in cols:
        conn.execute("ALTER TABLE character ADD COLUMN cargo_json TEXT")
    if "vessel_json" not in cols:
        conn.execute("ALTER TABLE character ADD COLUMN vessel_json TEXT")
    if "specialization_json" not in cols:
        conn.execute("ALTER TABLE character ADD COLUMN specialization_json TEXT")
    if "dual_class_json" not in cols:
        conn.execute("ALTER TABLE character ADD COLUMN dual_class_json TEXT")
    if "proficiencies_json" not in cols:
        conn.execute("ALTER TABLE character ADD COLUMN proficiencies_json TEXT")
    ccols = {r[1] for r in conn.execute("PRAGMA table_info(combat)")}
    if ccols and "acted_json" not in ccols:
        conn.execute("ALTER TABLE combat ADD COLUMN acted_json TEXT NOT NULL DEFAULT '[]'")
    campcols = {r[1] for r in conn.execute("PRAGMA table_info(campaign)")}
    if "training_required" not in campcols:
        conn.execute("ALTER TABLE campaign ADD COLUMN training_required INTEGER NOT NULL DEFAULT 0")
    lcols = {r[1] for r in conn.execute("PRAGMA table_info(location)")}
    if lcols and "economies" not in lcols:
        conn.execute("ALTER TABLE location ADD COLUMN economies TEXT")
