"""repo.py -- the access layer over the campaign SQLite database.

The database is the source of truth. Every read or write goes through here; the
web and referee layers never touch raw SQL. Mirrors the Cepheus repo that proved
out: small, explicit methods, JSON columns for the flexible bits (a character's
classes, gear, and spells).
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional

from . import db


def _insert(conn: sqlite3.Connection, table: str, values: Dict[str, Any]) -> int:
    cols = ", ".join(values)
    ph = ", ".join("?" for _ in values)
    cur = conn.execute(
        "INSERT INTO {} ({}) VALUES ({})".format(table, cols, ph),
        tuple(values.values()))
    conn.commit()
    return cur.lastrowid


class Repo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @classmethod
    def open(cls, path: str) -> "Repo":
        return cls(db.connect(path))

    @classmethod
    def memory(cls) -> "Repo":
        return cls(db.connect_memory())

    def close(self) -> None:
        self.conn.commit()
        self.conn.close()

    # ---- campaigns -----------------------------------------------------
    def create_campaign(self, name: str, setting: str = "World of Greyhawk",
                        current_date: Optional[str] = None,
                        allow_race_overrides: bool = False) -> int:
        return _insert(self.conn, "campaign", {
            "name": name, "setting": setting, "current_date": current_date,
            "allow_race_overrides": 1 if allow_race_overrides else 0,
        })

    def get_campaign(self, cid: int) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM campaign WHERE id=?", (cid,)).fetchone()

    def list_campaigns(self) -> List[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM campaign ORDER BY id").fetchall()

    def set_date(self, cid: int, in_game_date: str) -> None:
        self.conn.execute("UPDATE campaign SET current_date=? WHERE id=?",
                          (in_game_date, cid))
        self.conn.commit()

    def set_training_required(self, cid: int, on: bool) -> None:
        self.conn.execute("UPDATE campaign SET training_required=? WHERE id=?",
                          (1 if on else 0, cid))
        self.conn.commit()

    # ---- characters ----------------------------------------------------
    def save_character(self, cid: int, char: Dict[str, Any],
                       is_npc: bool = False) -> int:
        """Persist a character from a plain dict of fields.

        JSON columns accept python lists/dicts via json.dumps. Ability keys are
        the short names (str, dex, con, int, wis, cha); hp_current defaults to
        hp_max; alive defaults to True.
        """
        row = {
            "campaign_id": cid,
            "name": char.get("name", "Unnamed"),
            "player": char.get("player", ""),
            "race": char.get("race"),
            "classes_json": json.dumps(char.get("classes", [])),
            "alignment": char.get("alignment"),
            "str_score": char.get("str"), "str_pct": char.get("str_pct", 0),
            "dex_score": char.get("dex"), "con_score": char.get("con"),
            "int_score": char.get("int"), "wis_score": char.get("wis"),
            "cha_score": char.get("cha"),
            "hp_max": char.get("hp_max"),
            "hp_current": char.get("hp_current", char.get("hp_max")),
            "ac_descending": char.get("ac_descending"),
            "ac_ascending": char.get("ac_ascending"),
            "damage_dice": char.get("damage_dice"),
            "gold": char.get("gold", 0),
            "gear_json": json.dumps(char.get("gear", [])),
            "spellbook_json": json.dumps(char.get("spellbook", [])),
            "memorized_json": json.dumps(char.get("memorized", [])),
            "age": char.get("age"),
            "status": char.get("status", "ok"),
            "alive": 1 if char.get("alive", True) else 0,
            "is_npc": 1 if is_npc else 0,
            "notes": char.get("notes", ""),
        }
        return _insert(self.conn, "character", row)

    def get_character(self, chid: int) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM character WHERE id=?", (chid,)).fetchone()

    def list_characters(self, cid: int, include_npcs: bool = True) -> List[sqlite3.Row]:
        q = "SELECT * FROM character WHERE campaign_id=?"
        if not include_npcs:
            q += " AND is_npc=0"
        return self.conn.execute(q + " ORDER BY id", (cid,)).fetchall()

    def delete_character(self, chid: int) -> bool:
        cur = self.conn.execute("DELETE FROM character WHERE id=?", (chid,))
        self.conn.commit()
        return cur.rowcount > 0

    # ---- chargen sessions (persistent, replayable creation) -----------
    def create_chargen_session(self, cid: int, sid: str, handle: str, seed: int,
                               method: Optional[str] = None) -> str:
        _insert(self.conn, "chargen_session", {
            "id": sid, "campaign_id": cid, "handle": handle, "seed": seed,
            "method": method, "choices_json": "[]",
        })
        return sid

    def get_chargen_session(self, cid: int, sid: str) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM chargen_session WHERE id=? AND campaign_id=?",
            (sid, cid)).fetchone()

    def update_chargen_choices(self, sid: str, choices_json: str) -> None:
        self.conn.execute(
            "UPDATE chargen_session SET choices_json=?, updated_at=datetime('now') "
            "WHERE id=?", (choices_json, sid))
        self.conn.commit()

    def delete_chargen_session(self, sid: str) -> None:
        self.conn.execute("DELETE FROM chargen_session WHERE id=?", (sid,))
        self.conn.commit()

    # ---- dominions (the realm layer) ----------------------------------
    def create_dominion(self, cid: int, name: str, ruler: Optional[str] = None,
                        title: Optional[str] = None, confidence: int = 50,
                        fiefs: Optional[list] = None) -> int:
        # Idempotent by (campaign, name): re-founding an existing dominion updates
        # it in place rather than inserting a duplicate row.
        existing = self.conn.execute(
            "SELECT id FROM dominion WHERE campaign_id=? AND lower(name)=lower(?) "
            "ORDER BY id DESC LIMIT 1", (cid, name)).fetchone()
        fields = {"ruler": ruler, "title": title, "confidence": confidence,
                  "fiefs_json": json.dumps(fiefs or [])}
        if existing:
            self.update_dominion(existing["id"], **fields)
            return existing["id"]
        return _insert(self.conn, "dominion", {
            "campaign_id": cid, "name": name, **fields,
        })

    def get_dominion(self, cid: int, name: str) -> Optional[sqlite3.Row]:
        # Newest wins, so a re-founded dominion is the one that's acted upon.
        return self.conn.execute(
            "SELECT * FROM dominion WHERE campaign_id=? AND lower(name)=lower(?) "
            "ORDER BY id DESC LIMIT 1",
            (cid, name)).fetchone()

    def list_dominions(self, cid: int) -> List[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM dominion WHERE campaign_id=? ORDER BY id", (cid,)).fetchall()

    def update_dominion(self, dom_id: int, **fields) -> None:
        if not fields:
            return
        cols = ", ".join("{}=?".format(k) for k in fields)
        self.conn.execute("UPDATE dominion SET {} WHERE id=?".format(cols),
                          tuple(fields.values()) + (dom_id,))
        self.conn.commit()

    # ---- map locations ------------------------------------------------
    def add_location(self, cid: int, name: str, kind: Optional[str] = None,
                     terrain: Optional[str] = None, hex_col: Optional[int] = None,
                     hex_row: Optional[int] = None, notes: str = "",
                     economies: Optional[str] = None) -> int:
        # Upsert by (campaign, name): re-placing a known location moves it.
        existing = self.conn.execute(
            "SELECT id FROM location WHERE campaign_id=? AND lower(name)=lower(?)",
            (cid, name)).fetchone()
        if existing:
            self.conn.execute(
                "UPDATE location SET kind=?, terrain=?, hex_col=?, hex_row=?, "
                "notes=?, economies=COALESCE(?, economies) WHERE id=?",
                (kind, terrain, hex_col, hex_row, notes, economies, existing["id"]))
            self.conn.commit()
            return existing["id"]
        return _insert(self.conn, "location", {
            "campaign_id": cid, "name": name, "kind": kind, "terrain": terrain,
            "hex_col": hex_col, "hex_row": hex_row, "notes": notes,
            "economies": economies})

    def list_locations(self, cid: int) -> List[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM location WHERE campaign_id=? ORDER BY id", (cid,)).fetchall()

    def set_party_hex(self, cid: int, col: int, row: int) -> None:
        self.add_location(cid, "Party", kind="party", hex_col=col, hex_row=row)

    # ---- retainers (hirelings & henchmen) -----------------------------
    def add_retainer(self, cid: int, character_id: int, master: str,
                     **factors) -> int:
        row = {"campaign_id": cid, "character_id": character_id, "master": master}
        for k in ("status", "relationship", "service", "training", "payment",
                  "treatment", "discipline", "notes"):
            if k in factors and factors[k] is not None:
                row[k] = factors[k]
        return _insert(self.conn, "retainer", row)

    def get_retainer_by_character(self, character_id: int) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM retainer WHERE character_id=?", (character_id,)).fetchone()

    def list_retainers(self, cid: int, master: Optional[str] = None
                       ) -> List[sqlite3.Row]:
        if master:
            return self.conn.execute(
                "SELECT * FROM retainer WHERE campaign_id=? AND lower(master)=lower(?) "
                "ORDER BY id", (cid, master)).fetchall()
        return self.conn.execute(
            "SELECT * FROM retainer WHERE campaign_id=? ORDER BY id", (cid,)).fetchall()

    def update_retainer(self, retainer_id: int, **fields) -> None:
        fields = {k: v for k, v in fields.items() if v is not None}
        if not fields:
            return
        cols = ", ".join("{}=?".format(k) for k in fields)
        self.conn.execute("UPDATE retainer SET {} WHERE id=?".format(cols),
                          tuple(fields.values()) + (retainer_id,))
        self.conn.commit()

    # ---- combat tracker -----------------------------------------------
    def active_combat(self, cid: int) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM combat WHERE campaign_id=? AND active=1 "
            "ORDER BY id DESC LIMIT 1", (cid,)).fetchone()

    def start_combat(self, cid: int, combatants_json: str, order_json: str) -> int:
        # End any prior combat first.
        self.conn.execute("UPDATE combat SET active=0 WHERE campaign_id=? AND active=1",
                          (cid,))
        return _insert(self.conn, "combat", {
            "campaign_id": cid, "round": 1, "active": 1,
            "combatants_json": combatants_json, "order_json": order_json,
            "acted_json": "[]"})

    def update_combat(self, combat_id: int, **fields) -> None:
        if not fields:
            return
        cols = ", ".join("{}=?".format(k) for k in fields)
        self.conn.execute("UPDATE combat SET {} WHERE id=?".format(cols),
                          tuple(fields.values()) + (combat_id,))
        self.conn.commit()

    def end_combat(self, cid: int) -> None:
        self.conn.execute("UPDATE combat SET active=0 WHERE campaign_id=? AND active=1",
                          (cid,))
        self.conn.commit()

    # ---- events (the chronicle spine) ---------------------------------
    def record_event(self, cid: int, kind: str, summary: str,
                     detail: Optional[dict] = None,
                     in_game_date: Optional[str] = None) -> int:
        return _insert(self.conn, "event", {
            "campaign_id": cid, "kind": kind, "summary": summary,
            "detail_json": json.dumps(detail or {}), "in_game_date": in_game_date,
        })

    def recent_events(self, cid: int, limit: int = 20) -> List[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM event WHERE campaign_id=? ORDER BY id DESC LIMIT ?",
            (cid, limit)).fetchall()

    # ---- turn log (conversation memory the referee replays) -----------
    def log_turn(self, cid: int, player_input: str, narration: str,
                 speaker: Optional[str] = None) -> int:
        return _insert(self.conn, "turn_log", {
            "campaign_id": cid, "speaker": speaker,
            "player_input": player_input, "narration": narration,
        })

    def recent_turns(self, cid: int, limit: int = 6) -> List[sqlite3.Row]:
        rows = self.conn.execute(
            "SELECT * FROM turn_log WHERE campaign_id=? ORDER BY id DESC LIMIT ?",
            (cid, limit)).fetchall()
        return list(reversed(rows))
