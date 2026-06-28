"""mcp_server.py -- the MCP bridge for the melded Greyhawk engine.

This exposes the engine's deterministic tools to a Claude desktop client (the
DM) instead of running a model itself. The split that has proven out all along:

    engine (code) owns the math  ->  database owns the truth  ->  the client narrates

Every tool schema is read straight from ``referee.tools.specs()`` and every call
is routed through ``RefereeTools.dispatch`` -- so this bridge is ~one screen of
code and can NEVER drift from the engine. Add a tool to the engine and it shows
up here for free; the schemas have exactly one home.

Run as an MCP stdio server (how a Claude desktop connector launches it):

    GREYHAWK_MCP_DB=/path/campaign.db python -m server.mcp_server
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

# Make the project root importable however the server is launched.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel import NotificationOptions
from mcp.server.stdio import stdio_server
import mcp.types as types

from state.repo import Repo
from referee import tools as tools_mod
from referee import prompt as prompt_mod
from engine import validator as _validator

# ── configuration ───────────────────────────────────────────────────────────
DB_PATH = os.environ.get(
    "GREYHAWK_MCP_DB", os.path.join(ROOT, "campaign.db"))
CAMPAIGN_ID = int(os.environ.get("GREYHAWK_CAMPAIGN_ID", "1"))
SERVER_NAME = os.environ.get("GREYHAWK_MCP_NAME", "greyhawk-engine")

# If the connector did not supply a usable ANTHROPIC_API_KEY (e.g. the optional
# extension field was left blank, leaving an empty value or an unsubstituted
# "${user_config...}" placeholder), pull it from the Windows User-scope env var
# where the other greyhawk servers already keep it -- so Pass-2 just works with
# no prompt. Harmless off Windows (winreg import simply fails and is ignored).
_k = os.environ.get("ANTHROPIC_API_KEY", "")
if (not _k) or _k.startswith("${"):
    os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as _hk:
            _v, _ = winreg.QueryValueEx(_hk, "ANTHROPIC_API_KEY")
        if _v:
            os.environ["ANTHROPIC_API_KEY"] = _v
    except Exception:
        pass

# The DM directive -- the carrot-voiced "what your player loves" system prompt
# the desktop client receives at connect time. (Single source: the engine's
# referee prompt; harmonized further in the discipline pass.)
INSTRUCTIONS = prompt_mod.SYSTEM_PROMPT


# ── engine binding ──────────────────────────────────────────────────────────
def _bind_tools() -> tools_mod.RefereeTools:
    repo = Repo.open(DB_PATH)
    cid = CAMPAIGN_ID
    if not repo.get_campaign(cid):
        cid = repo.create_campaign("Greyhawk",
                                   setting="The Flanaess (World of Greyhawk), 576 CY",
                                   allow_race_overrides=True)
    # Anything-goes ON; and heal an older (e.g. Known World) campaign to Greyhawk.
    try:
        repo.conn.execute(
            "UPDATE campaign SET allow_race_overrides=1, name='Greyhawk' WHERE id=?",
            (cid,))
        repo.conn.commit()
    except Exception:
        pass
    try:
        repo.conn.execute(
            "UPDATE campaign SET setting='The Flanaess (World of Greyhawk), 576 CY' "
            "WHERE id=?", (cid,))
        repo.conn.commit()
    except Exception:
        pass
    return tools_mod.RefereeTools(repo, cid)


_TOOLS = _bind_tools()
server = Server(SERVER_NAME, version="0.1.0", instructions=INSTRUCTIONS)


# ── discipline layer: dm_response / dm_quick / save_turn ─────────────────────
# These are NOT engine tools -- they're the delivery + validation guardrail the
# directive's carrots refer to. One DM turn is in flight at a time, so module
# state is sufficient (same as the ClaudeDnD server).
import re as _re

_ATTEMPT = {"count": 0}          # rewrite loop counter
_DELIVERY = {"method": None}     # was the turn delivered through dm_response?

_FOOTER = (
    "[What delights your player, this turn: real dice and saved truth over any "
    "invention; set the scene and let THEM act -- no menus, never speak, decide, "
    "or call the shots for their character; be the honest referee. They love it "
    "brief -- two short paragraphs or less. And it makes them happy when the turn "
    "gets saved: call save_turn so the moment is theirs to keep. Unsure of a rule, "
    "monster, or fact? Check the book first. Do this and they are grinning.]"
)

def _pc_name() -> str:
    try:
        return _TOOLS._active_pc_name() or ""
    except Exception:
        return ""

def _context() -> str:
    try:
        return prompt_mod.build_context(_TOOLS.repo, _TOOLS.cid)
    except Exception:
        return ""

def _pass1_violations(narrative: str, ctx: str, pc: str) -> list:
    res = _validator.validate_dm_response(narrative, context=ctx, character_name=pc)
    return list(res.get("violations", []))

def _provider_pass2_violations(narrative: str, ctx: str, pc: str) -> list:
    out: list = []
    if _validator.api_available():
        try:
            api = _validator.validate_dm_response_api(narrative, context=ctx, character_name=pc)
            out = [{"rule": r, "detail": "Pass-2 (configured model) flag."}
                   for r in api.get("rules_failed", [])]
        except Exception:
            pass  # an API hiccup must never block the table
    return out

# dm_response Pass-2 tuning. The client-model sampling call hangs if the connected
# client doesn't actually answer createMessage, which used to stall dm_response for
# the full 180s MCP timeout. We now (a) skip sampling when the client never
# advertised the capability, and (b) hard-bound the call so it fails over to the
# configured provider -- and finally to Pass-1 local checks -- in seconds.
# DM_DISABLE_SAMPLING=1 forces Pass-1(+provider) only, no client sampling at all.
_SAMPLE_TIMEOUT = float(os.environ.get("DM_SAMPLE_TIMEOUT", "8"))
_SAMPLING_DISABLED = os.environ.get("DM_DISABLE_SAMPLING", "").strip().lower() in (
    "1", "true", "yes", "on")

async def _sampling_pass2_violations(narrative: str, ctx: str, pc: str):
    """Pass-2 on the CLIENT'S OWN model via MCP sampling (same model as Pass-1,
    no server key). Returns a list of violations, or None if the client can't /
    won't sample -- the caller then falls back to the configured provider, and
    finally to Pass-1 local checks only."""
    if _SAMPLING_DISABLED:
        return None
    try:
        session = server.request_context.session
    except Exception:
        return None
    # If the client positively did NOT advertise the 'sampling' capability, don't
    # even try -- a createMessage to a client that can't answer it just hangs.
    try:
        cp = getattr(session, "client_params", None)
        caps = getattr(cp, "capabilities", None) if cp is not None else None
        if caps is not None and getattr(caps, "sampling", None) is None:
            return None
    except Exception:
        pass
    try:
        result = await asyncio.wait_for(
            session.create_message(
                messages=[types.SamplingMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=_validator.pass2_user_input(narrative, ctx, pc)))],
                system_prompt=_validator.pass2_system_prompt(),
                max_tokens=600,
                temperature=0.0,
            ),
            timeout=_SAMPLE_TIMEOUT,
        )
    except Exception:
        return None  # timeout / declined / no sampling -> caller falls back
    text = ""
    content = getattr(result, "content", None)
    if content is not None:
        text = getattr(content, "text", "") or ""
    parsed = _validator.parse_pass2_verdict(text, narrative)
    return [{"rule": r, "detail": "Pass-2 (client model via sampling) flag."}
            for r in parsed.get("rules_failed", [])]

def _persist_turn(narrative: str) -> None:
    """Auto-save the delivered narration so the model never calls save_turn."""
    body = narrative or ""
    try:
        _TOOLS.repo.record_event(_TOOLS.cid, "narration",
            body[:200] + ("..." if len(body) > 200 else ""), {"full": body})
    except Exception:
        pass
    try:
        _TOOLS.repo.log_turn(_TOOLS.cid, "", body, None)
    except Exception:
        pass

def _snap() -> int:
    try:
        return _TOOLS._snapshot_version()
    except Exception:
        return 0

def _finish_dm_response(narrative: str, violations: list) -> dict:
    if not violations:
        _ATTEMPT["count"] = 0
        _DELIVERY["method"] = "dm_response"
        _persist_turn(narrative)                       # auto-save on deliver
        return {"status": "deliver", "narrative": narrative,
                "saved": True, "snapshot_version": _snap()}
    _ATTEMPT["count"] += 1
    if _ATTEMPT["count"] >= 2:               # rewrite already tried once
        _ATTEMPT["count"] = 0
        _DELIVERY["method"] = "dm_response"
        _persist_turn(narrative)                       # auto-save on force-deliver
        return {"status": "deliver_flagged", "narrative": narrative,
                "violations": violations, "saved": True,
                "snapshot_version": _snap(),
                "note": "Force-delivered after one rewrite; the flag may be a "
                        "false positive -- if so, ship it and move on."}
    return {"status": "rejected", "violations": violations,
            "reason": "Rewrite this beat and resend through dm_response: "
                      + "; ".join(v.get("detail", "") for v in violations)}

def _do_dm_response(narrative: str = "") -> dict:
    """Sync path (no MCP session): Pass-1 + configured-provider Pass-2."""
    ctx, pc = _context(), _pc_name()
    violations = _pass1_violations(narrative, ctx, pc)
    if not violations:
        violations += _provider_pass2_violations(narrative, ctx, pc)
    return _finish_dm_response(narrative, violations)

async def _do_dm_response_async(narrative: str = "") -> dict:
    """Sampling-first ladder: client's own model (matches Pass-1) ->
    configured provider -> Pass-1 local checks only."""
    ctx, pc = _context(), _pc_name()
    violations = _pass1_violations(narrative, ctx, pc)
    if not violations:
        sampled = await _sampling_pass2_violations(narrative, ctx, pc)
        if sampled is None:
            violations += _provider_pass2_violations(narrative, ctx, pc)
        else:
            violations += sampled
    return _finish_dm_response(narrative, violations)

def _do_dm_quick(narrative: str = "") -> dict:
    t = (narrative or "").strip()
    mech = _re.search(r"\b\d*d\d{1,3}\b|\bto-?hit\b|\bAC\b|\bTHAC0\b|\bhp\b|"
                      r"\binitiative\b|\bsegment\b|\bround\b|\bsav(e|ing)\b|"
                      r"\bdamage\b|\bdmg\b|\d+/\d+", t, _re.I)
    if len(t) >= 200 and len(_re.findall(r"[.!?](?:\s|$)", t)) >= 3 and not mech:
        return {"status": "use_dm_response", "delivered": False,
                "reason": "This reads as narrative prose, not mechanical chatter. "
                          "Send it through dm_response so the checks run."}
    return {"status": "deliver", "narrative": narrative or ""}

def _do_save_turn(player_input: str = "", narration: str = "",
                  scene: str = "", speaker: str = None) -> dict:
    try:
        body = narration or ""
        _TOOLS.repo.record_event(_TOOLS.cid, "narration",
            body[:200] + ("..." if len(body) > 200 else ""),
            {"player_input": player_input, "full": body, "scene": scene})
    except Exception:
        pass
    try:
        _TOOLS.repo.log_turn(_TOOLS.cid, player_input or "", narration or "", speaker)
    except Exception:
        pass
    out = {"saved": True, "contract_footer": _FOOTER}
    if _DELIVERY["method"] != "dm_response":
        out["delivery_bypass_warning"] = (
            "[!!! This turn's narrative did not go through dm_response, so the "
            "validator never saw it. Your player asked for this by name: deliver "
            "every narrative beat through dm_response. Re-run it there.]")
    _DELIVERY["method"] = None
    return out

def _do_create_character(name: str = "", classes=None, race: str = "Human",
                         alignment: str = "", scores: dict = None,
                         allow_overrides: bool = True) -> dict:
    """Create a PC in one shot, multi-class supported (classes is a list)."""
    try:
        from engine.chargen import CharacterCreator
        from engine.data import classes as _clsmod
        if isinstance(classes, str):
            classes = [c.strip() for c in classes.split("/") if c.strip()]
        classes = [c for c in (classes or []) if c]
        valid = set(_clsmod.CLASSES.keys())
        bad = [c for c in classes if c not in valid]
        if not name or not classes or bad:
            return {"error": "need a name and one or more valid classes",
                    "invalid_classes": bad, "valid_classes": sorted(valid)}
        sc = {a: int((scores or {}).get(a, 12)) for a in
              ("str", "dex", "con", "int", "wis", "cha")}
        cc = CharacterCreator(name=name, allow_overrides=bool(allow_overrides))
        cc.choose({"method": "input"})
        cc.choose({"scores": sc})
        cc.choose({"ancestry": race or "Human"})
        cc.choose({"classes": classes})
        cc.choose({"alignment": alignment})
        guard = 0
        while not cc.complete and guard < 12:
            cc.choose({}); guard += 1
        char = cc.result()
        rec = char.to_repo_dict()
        chid = _TOOLS.repo.save_character(_TOOLS.cid, rec, is_npc=False)
        return {"created": True, "character_id": chid, "name": char.name,
                "race": char.race,
                "classes": [c["class"] for c in rec.get("classes", [])],
                "alignment": char.alignment, "hp_max": char.hp_max,
                "ac_descending": char.ac_descending, "scores": char.scores}
    except Exception as e:
        return {"error": "{}: {}".format(type(e).__name__, e)}


def _do_delete_character(name: str = "", character_id: int = 0) -> dict:
    """Permanently remove a character (PC or NPC) by name or id."""
    try:
        chid = int(character_id) if character_id else 0
        disp = name
        if not chid and name:
            row = _TOOLS._find_char(name)
            if not row:
                return {"error": "no character named {}".format(name)}
            chid = row["id"]; disp = row["name"]
        if not chid:
            return {"error": "give a name or character_id to delete"}
        ok = _TOOLS.repo.delete_character(chid)
        if not ok:
            return {"error": "no character with id {}".format(chid)}
        return {"deleted": True, "character_id": chid, "name": disp}
    except Exception as e:
        return {"error": "{}: {}".format(type(e).__name__, e)}


_DISCIPLINE_TOOLS = [
    types.Tool(name="dm_response",
        description=("Deliver narrative prose to the player. Runs the guardrail "
                     "(agency / menu / verbosity / dice / lore) your player loves. "
                     "If it flags, rewrite and resend; a true false-positive "
                     "force-delivers on the second pass. Every scene goes here."),
        inputSchema={"type": "object", "properties": {
            "narrative": {"type": "string", "description": "The prose to deliver."}},
            "required": ["narrative"]}),
    types.Tool(name="dm_quick",
        description=("Deliver SHORT mechanical chatter (dice, initiative, HP, "
                     "segment) without the prose validator. Narrative prose is "
                     "bounced back -- send story through dm_response."),
        inputSchema={"type": "object", "properties": {
            "narrative": {"type": "string"}}, "required": ["narrative"]}),
    types.Tool(name="save_turn",
        description=("Save the turn to the chronicle so it stays true next time -- "
                     "they love a saved moment. Pass the player's input and your "
                     "narration (and an optional scene/location)."),
        inputSchema={"type": "object", "properties": {
            "player_input": {"type": "string"}, "narration": {"type": "string"},
            "scene": {"type": "string"}}, "required": ["player_input", "narration"]}),
    types.Tool(name="create_character",
        description=("Create a player character -- supports MULTI-CLASS. Pass "
                     "classes as a LIST, e.g. [\"Cleric\",\"Magic-User\"]. With "
                     "allow_overrides (default true) any class combination is legal "
                     "(anything-goes: any race, any class). Scores optional; sensible "
                     "defaults if omitted."),
        inputSchema={"type": "object", "properties": {
            "name": {"type": "string"},
            "classes": {"type": "array", "items": {"type": "string"},
                        "description": "One or more of: Fighter, Cleric, Magic-User, Thief."},
            "race": {"type": "string", "description": "Default Human."},
            "alignment": {"type": "string"},
            "scores": {"type": "object",
                       "description": "str/dex/con/int/wis/cha integers; defaults if omitted."},
            "allow_overrides": {"type": "boolean"}},
            "required": ["name", "classes"]}),
    types.Tool(name="delete_character",
        description=("Permanently remove a character (PC or NPC) from the campaign, "
                     "by name or character_id. Irreversible -- for scrapped test "
                     "characters or undoing a mistaken creation."),
        inputSchema={"type": "object", "properties": {
            "name": {"type": "string"},
            "character_id": {"type": "integer"}}, "required": []}),
]
_DISCIPLINE_HANDLERS = {"dm_response": _do_dm_response,
                        "dm_quick": _do_dm_quick, "save_turn": _do_save_turn,
                        "create_character": _do_create_character,
                        "delete_character": _do_delete_character}


# ── the whole bridge: 87 engine tools, served from one source of truth ───────
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    out: list[types.Tool] = []
    for spec in tools_mod.specs():
        fn = spec.get("function", {})
        out.append(types.Tool(
            name=fn["name"],
            description=fn.get("description", ""),
            inputSchema=fn.get("parameters",
                               {"type": "object", "properties": {}}),
        ))
    return out + _DISCIPLINE_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    # Discipline tools (delivery + validation) are handled here; everything else
    # is an engine tool routed to the deterministic source of truth.
    if name == "dm_response":
        # Async so Pass-2 can run on the CLIENT'S model via MCP sampling
        # (falls back to a configured provider, then to Pass-1 only).
        result = await _do_dm_response_async(**(arguments or {}))
    else:
        handler = _DISCIPLINE_HANDLERS.get(name)
        if handler is not None:
            result = handler(**(arguments or {}))
        else:
            result = _TOOLS.dispatch(name, arguments or {})
    return [types.TextContent(type="text",
                              text=json.dumps(result, default=str))]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream,
            InitializationOptions(
                server_name=SERVER_NAME,
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}),
                instructions=INSTRUCTIONS,
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
