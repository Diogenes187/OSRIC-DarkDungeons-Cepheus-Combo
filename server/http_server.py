"""http_server.py -- serve the SAME MCP server over Streamable HTTP, for remote
hosting (fly.io) and any MCP-speaking client (AI-agnostic).

Only the transport changes. The fully-wired ``Server`` object -- all 87 engine
tools, the discipline tools, and the DM directive delivered as MCP
``instructions`` -- is imported unchanged from ``server.mcp_server``. stdio and
HTTP are two front doors to one engine; the local Claude-desktop connector keeps
using stdio, while this entrypoint exposes the identical capability set at an
HTTPS URL that Claude, an OpenAI agent, or your own loop can all connect to.

    Local:   uvicorn server.http_server:app --port 8080
    Docker:  CMD ["uvicorn", "server.http_server:app", "--host", "0.0.0.0", "--port", "8080"]

Endpoints:
    /mcp      -- the MCP Streamable HTTP transport (POST + GET/SSE)
    /health   -- plaintext 200 for fly.io health checks

Auth: set MCP_AUTH_TOKEN to require ``Authorization: Bearer <token>`` on /mcp.
Leave it unset for an open server (fine behind a private network / for testing).
"""
from __future__ import annotations

import contextlib
import os
from collections.abc import AsyncIterator

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import PlainTextResponse
from starlette.types import Receive, Scope, Send

from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

# Reuse the fully-wired server (tools + instructions + handlers). Importing this
# module also binds the engine to GREYHAWK_MCP_DB, exactly as the stdio build does.
from server.mcp_server import server  # noqa: E402

AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "").strip()

# One session manager wraps the low-level Server and speaks Streamable HTTP.
# stateless=False keeps a session id per client so multi-call turns (combat,
# chargen) stay coherent; json_response=False uses SSE streaming.
_session_manager = StreamableHTTPSessionManager(
    app=server,
    event_store=None,
    json_response=False,
    stateless=False,
)


async def _handle_mcp(scope: Scope, receive: Receive, send: Send) -> None:
    if AUTH_TOKEN:
        headers = dict(scope.get("headers") or [])
        presented = headers.get(b"authorization", b"").decode()
        if presented != f"Bearer {AUTH_TOKEN}":
            await send({"type": "http.response.start", "status": 401,
                        "headers": [(b"content-type", b"text/plain")]})
            await send({"type": "http.response.body", "body": b"unauthorized"})
            return
    await _session_manager.handle_request(scope, receive, send)


async def _health(_request) -> PlainTextResponse:
    return PlainTextResponse("ok")


@contextlib.asynccontextmanager
async def _lifespan(_app: Starlette) -> AsyncIterator[None]:
    # The session manager must be running for the lifetime of the app.
    async with _session_manager.run():
        yield


app = Starlette(
    debug=False,
    routes=[
        Route("/health", _health, methods=["GET"]),
        Mount("/mcp", app=_handle_mcp),
    ],
    lifespan=_lifespan,
)
