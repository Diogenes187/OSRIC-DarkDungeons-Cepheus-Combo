"""service.py -- orchestration that the web layer calls (framework-agnostic).

Holds the persistent, replayable character-creation flow: the build's seed and
ordered choices live in the database, and the live ``CharacterCreator`` is
rebuilt by deterministic replay on every request -- so a build survives a
restart, redeploy, or a player wandering off mid-creation. This is the same
pattern that made the Cepheus chargen restart-proof, lifted out of the web
framework so it can be unit-tested directly.
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Dict, Optional, Tuple

from engine.chargen import CharacterCreator
from state.repo import Repo


def _overrides(repo: Repo, cid: int) -> bool:
    camp = repo.get_campaign(cid)
    return bool(camp and camp["allow_race_overrides"])


def _rebuild(repo: Repo, cid: int, sid: str) -> Optional[Tuple[Any, CharacterCreator, list]]:
    """Load a session row and replay its stored choices into a live creator."""
    row = repo.get_chargen_session(cid, sid)
    if not row:
        return None
    cc = CharacterCreator(name=row["handle"], seed=row["seed"],
                          allow_overrides=_overrides(repo, cid))
    choices = json.loads(row["choices_json"] or "[]")
    for ch in choices:
        if cc.complete:
            break
        cc.choose(ch)
    return row, cc, choices


def chargen_start(repo: Repo, cid: int, name: Optional[str] = None) -> Dict[str, Any]:
    """Begin a build. No name up front -- a readable handle carries it until the
    player names the finished character. Returns the session id and first step."""
    import random
    seed = random.randint(0, 2**31 - 1)
    sid = uuid.uuid4().hex[:12]
    handle = (name or "").strip() or "Recruit {}".format(sid[:4].upper())
    cc = CharacterCreator(name=handle, seed=seed, allow_overrides=_overrides(repo, cid))
    repo.create_chargen_session(cid, sid, handle, seed)
    return {"session_id": sid, "pending": cc.pending()}


def chargen_get(repo: Repo, cid: int, sid: str) -> Optional[Dict[str, Any]]:
    loaded = _rebuild(repo, cid, sid)
    if not loaded:
        return None
    _row, cc, _choices = loaded
    return {"session_id": sid, "pending": cc.pending()}


def chargen_choose(repo: Repo, cid: int, sid: str,
                   payload: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Apply one choice. On completion, save the character and clear the session.
    Returns None if the session does not exist."""
    loaded = _rebuild(repo, cid, sid)
    if not loaded:
        return None
    row, cc, choices = loaded
    if cc.complete:
        return {"pending": cc.pending(), "complete": True}
    pending = cc.choose(payload)
    choices = choices + [payload or {}]
    if pending.get("step") == "complete":
        char = cc.result()
        chid = repo.save_character(cid, char.to_repo_dict(), is_npc=False)
        repo.delete_chargen_session(sid)
        repo.record_event(cid, "character",
                          "{} joined the party.".format(char.name),
                          detail={"character_id": chid})
        return {"pending": pending, "character_id": chid}
    repo.update_chargen_choices(sid, json.dumps(choices))
    return {"pending": pending}
