"""oauth.py -- a minimal but spec-correct OAuth 2.1 authorization server for the
MCP endpoint, so OAuth-only clients (e.g. Claude's custom connector) can connect.

Implements what the MCP Authorization spec expects:
  - RFC 9728 Protected Resource Metadata   GET /.well-known/oauth-protected-resource
  - RFC 8414 Authorization Server Metadata GET /.well-known/oauth-authorization-server
  - RFC 7591 Dynamic Client Registration   POST /register
  - OAuth 2.1 Authorization Code + PKCE     GET/POST /authorize, POST /token

Access control is a single shared password (env MCP_LOGIN_PASSWORD) shown on the
consent screen; PKCE (S256) protects the code exchange. Clients and tokens persist
to a JSON file on the data volume so a machine restart doesn't force re-auth.

Stdlib only (json/secrets/hashlib/base64/time) + Starlette responses.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from typing import Any, Dict, Optional

from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse, RedirectResponse, Response
from starlette.routing import Route

# ── config ───────────────────────────────────────────────────────────────────
BASE_URL = os.environ.get("BASE_URL", "https://tkw-dnd.fly.dev").rstrip("/")
LOGIN_PASSWORD = os.environ.get("MCP_LOGIN_PASSWORD", "")   # empty => auto-approve
RESOURCE = BASE_URL + "/mcp"
_TOKEN_TTL = int(os.environ.get("OAUTH_TOKEN_TTL", str(30 * 24 * 3600)))   # 30 days
_CODE_TTL = 300                                                            # 5 min

_STORE_PATH = os.environ.get(
    "OAUTH_STORE",
    os.path.join(os.path.dirname(os.environ.get("GREYHAWK_MCP_DB", "/data/x")),
                 "oauth_store.json"))

# ── persistent store (clients + tokens) ──────────────────────────────────────
def _load() -> Dict[str, Any]:
    try:
        with open(_STORE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"clients": {}, "access": {}, "refresh": {}}

def _save(store: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(_STORE_PATH), exist_ok=True)
        tmp = _STORE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(store, f)
        os.replace(tmp, _STORE_PATH)
    except Exception:
        pass

_STORE = _load()
_CODES: Dict[str, Dict[str, Any]] = {}   # short-lived auth codes, in-memory


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def validate_token(token: str) -> bool:
    """True if `token` is an unexpired access token we issued."""
    if not token:
        return False
    rec = _STORE.get("access", {}).get(token)
    return bool(rec and rec.get("exp", 0) > time.time())


# ── metadata endpoints ───────────────────────────────────────────────────────
async def protected_resource_metadata(_req: Request) -> JSONResponse:
    return JSONResponse({
        "resource": RESOURCE,
        "authorization_servers": [BASE_URL],
        "bearer_methods_supported": ["header"],
    })

async def authorization_server_metadata(_req: Request) -> JSONResponse:
    return JSONResponse({
        "issuer": BASE_URL,
        "authorization_endpoint": BASE_URL + "/authorize",
        "token_endpoint": BASE_URL + "/token",
        "registration_endpoint": BASE_URL + "/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": ["mcp"],
    })


# ── dynamic client registration (RFC 7591) ───────────────────────────────────
async def register(req: Request) -> JSONResponse:
    try:
        body = await req.json()
    except Exception:
        body = {}
    redirect_uris = body.get("redirect_uris") or []
    if not isinstance(redirect_uris, list) or not redirect_uris:
        return JSONResponse({"error": "invalid_redirect_uri",
                             "error_description": "redirect_uris required"}, 400)
    client_id = "c_" + secrets.token_hex(16)
    _STORE.setdefault("clients", {})[client_id] = {
        "redirect_uris": redirect_uris,
        "created": int(time.time()),
        "client_name": body.get("client_name", ""),
    }
    _save(_STORE)
    return JSONResponse({
        "client_id": client_id,
        "client_id_issued_at": int(time.time()),
        "redirect_uris": redirect_uris,
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
    }, 201)


# ── authorization endpoint (code + PKCE) ─────────────────────────────────────
_FORM = """<!doctype html><html><head><meta charset=utf-8>
<title>Sign in - Greyhawk</title><style>body{{font-family:Georgia,serif;
background:#f7efd9;color:#3a2f25;display:flex;min-height:90vh;align-items:center;
justify-content:center}}form{{background:#fff;padding:28px 32px;border:1px solid
#3a2f25;border-radius:8px;max-width:340px}}h1{{font-size:20px;margin:0 0 12px}}
input[type=password]{{width:100%;padding:8px;margin:8px 0;font-size:15px}}
button{{padding:8px 18px;font-size:15px;cursor:pointer}}.err{{color:#7a2d12}}
</style></head><body><form method=post action="/authorize">
<h1>Greyhawk - sign in</h1><p>Enter the campaign password to connect this client.</p>
{err}<input type=password name=password autofocus placeholder="password"/>
{hidden}<button type=submit>Authorize</button></form></body></html>"""

def _hidden(params: Dict[str, str]) -> str:
    keep = ("client_id", "redirect_uri", "state", "code_challenge",
            "code_challenge_method", "scope", "response_type")
    out = []
    for k in keep:
        v = params.get(k)
        if v:
            out.append('<input type=hidden name="{}" value="{}"/>'.format(
                k, v.replace('"', "&quot;")))
    return "".join(out)

def _client_ok(client_id: str, redirect_uri: str) -> bool:
    c = _STORE.get("clients", {}).get(client_id)
    return bool(c and redirect_uri in c.get("redirect_uris", []))

async def authorize_get(req: Request) -> Response:
    p = dict(req.query_params)
    if p.get("response_type") != "code":
        return JSONResponse({"error": "unsupported_response_type"}, 400)
    if not _client_ok(p.get("client_id", ""), p.get("redirect_uri", "")):
        return JSONResponse({"error": "invalid_client",
                             "error_description": "unknown client_id/redirect_uri"}, 400)
    if p.get("code_challenge_method") != "S256" or not p.get("code_challenge"):
        return JSONResponse({"error": "invalid_request",
                             "error_description": "PKCE S256 required"}, 400)
    return HTMLResponse(_FORM.format(err="", hidden=_hidden(p)))

async def authorize_post(req: Request) -> Response:
    form = dict(await req.form())
    if not _client_ok(form.get("client_id", ""), form.get("redirect_uri", "")):
        return JSONResponse({"error": "invalid_client"}, 400)
    if LOGIN_PASSWORD and form.get("password", "") != LOGIN_PASSWORD:
        return HTMLResponse(_FORM.format(
            err='<p class=err>Wrong password.</p>', hidden=_hidden(form)), 401)
    code = secrets.token_urlsafe(24)
    _CODES[code] = {
        "client_id": form["client_id"],
        "redirect_uri": form["redirect_uri"],
        "code_challenge": form["code_challenge"],
        "scope": form.get("scope", "mcp"),
        "exp": time.time() + _CODE_TTL,
    }
    sep = "&" if "?" in form["redirect_uri"] else "?"
    loc = "{}{}code={}".format(form["redirect_uri"], sep, code)
    if form.get("state"):
        loc += "&state=" + form["state"]
    return RedirectResponse(loc, status_code=302)


# ── token endpoint ───────────────────────────────────────────────────────────
def _issue(client_id: str, scope: str) -> Dict[str, Any]:
    at = secrets.token_urlsafe(32)
    rt = secrets.token_urlsafe(32)
    now = time.time()
    _STORE.setdefault("access", {})[at] = {
        "client_id": client_id, "scope": scope, "exp": now + _TOKEN_TTL}
    _STORE.setdefault("refresh", {})[rt] = {
        "client_id": client_id, "scope": scope}
    _save(_STORE)
    return {"access_token": at, "token_type": "Bearer",
            "expires_in": _TOKEN_TTL, "refresh_token": rt, "scope": scope}

async def token(req: Request) -> JSONResponse:
    form = dict(await req.form())
    grant = form.get("grant_type")
    if grant == "authorization_code":
        code = form.get("code", "")
        rec = _CODES.pop(code, None)
        if not rec or rec["exp"] < time.time():
            return JSONResponse({"error": "invalid_grant"}, 400)
        if form.get("client_id") != rec["client_id"] or \
           form.get("redirect_uri") != rec["redirect_uri"]:
            return JSONResponse({"error": "invalid_grant"}, 400)
        verifier = form.get("code_verifier", "")
        challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
        if not verifier or challenge != rec["code_challenge"]:
            return JSONResponse({"error": "invalid_grant",
                                 "error_description": "PKCE check failed"}, 400)
        return JSONResponse(_issue(rec["client_id"], rec["scope"]))
    if grant == "refresh_token":
        rt = form.get("refresh_token", "")
        rec = _STORE.get("refresh", {}).get(rt)
        if not rec:
            return JSONResponse({"error": "invalid_grant"}, 400)
        return JSONResponse(_issue(rec["client_id"], rec.get("scope", "mcp")))
    return JSONResponse({"error": "unsupported_grant_type"}, 400)


def routes() -> list:
    return [
        Route("/.well-known/oauth-protected-resource",
              protected_resource_metadata, methods=["GET"]),
        Route("/.well-known/oauth-protected-resource/mcp",
              protected_resource_metadata, methods=["GET"]),
        Route("/.well-known/oauth-authorization-server",
              authorization_server_metadata, methods=["GET"]),
        Route("/register", register, methods=["POST"]),
        Route("/authorize", authorize_get, methods=["GET"]),
        Route("/authorize", authorize_post, methods=["POST"]),
        Route("/token", token, methods=["POST"]),
    ]
