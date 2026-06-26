# Deploying the Known World engine as a remote MCP server on fly.io

Same engine as the local Claude-desktop connector; only the transport changes
(stdio → Streamable HTTP). Any MCP-speaking client — Claude, an OpenAI agent, or
your own loop — connects to one HTTPS URL and gets all 87 engine tools plus the
DM directive (delivered via MCP `instructions`).

## What was added (all additive; the stdio build is untouched)
- `server/http_server.py` — Streamable HTTP entrypoint (`/mcp`) + `/health`, optional bearer auth.
- `Dockerfile`, `.dockerignore` — container image running `uvicorn server.http_server:app`.
- `fly.toml` — http service on 8080, HTTPS, a persistent volume at `/data`.
- `requirements.txt` — `mcp` pinned to a version with Streamable HTTP; anthropic made optional.
- `engine/validator.py` — Pass-2 validator is now provider-agnostic (uses `referee/llm.py`).

## One-time deploy
```bash
# 0. Install flyctl and log in
fly auth login

# 1. Create the app (don't deploy yet)
fly launch --no-deploy --copy-config --name tkw-dnd

# 2. Create the persistent volume for the SQLite campaign DB
#    (same region as the app; 1 GB is plenty)
fly volumes create tkw_data --region ord --size 1

# 3. Secrets (never put keys in fly.toml)
fly secrets set MCP_AUTH_TOKEN="$(openssl rand -hex 24)"   # require Bearer auth on /mcp
fly secrets set DEEPSEEK_API_KEY="sk-..."                  # or OPENAI_API_KEY / OPENROUTER_API_KEY

# 4. Deploy
fly deploy

# 5. Keep exactly ONE machine (SQLite is single-writer)
fly scale count 1
```
Your server is then at `https://tkw-dnd.fly.dev/mcp` (health at `/health`).

## Connecting a client
- URL: `https://tkw-dnd.fly.dev/mcp`
- Header: `Authorization: Bearer <the MCP_AUTH_TOKEN you set>`
- It's standard MCP Streamable HTTP, so any compliant client works. The DM rules
  arrive automatically via the server's `instructions`.

## Environment / config reference
| Var | Purpose | Default |
|-----|---------|---------|
| `GREYHAWK_MCP_DB` | SQLite path (on the volume) | `/data/campaign.db` |
| `GREYHAWK_CAMPAIGN_ID` | which campaign row to bind | `1` |
| `GREYHAWK_VALIDATOR_PROVIDER` | Pass-2 model provider | `deepseek` |
| `MCP_AUTH_TOKEN` | bearer token gate on `/mcp` (unset = open) | — |
| `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` / `OPENROUTER_API_KEY` | provider key for Pass-2 | — |

Pass-2 is optional: with no provider key the server still runs all local (Pass-1)
checks and the full game. With a key, validation runs on **your** chosen model.

## Caveat: SQLite is single-writer
`fly.toml` keeps one machine warm (`min_machines_running = 1`) and you should not
`fly scale count` above 1 on this design — two machines writing one SQLite file
on one volume will corrupt it. That's fine for a private/solo server.

---

## Phase 2 — multi-user & true multi-tenancy (the real product work)
The engine already keys *everything* by `campaign_id` (see `state/repo.py`), so the
data model is multi-tenant-ready. Two pieces remain:

1. **Per-request campaign routing.** Today `server/mcp_server.py` binds a single
   `CAMPAIGN_ID` at process start (`_TOOLS = _bind_tools()`). For many users,
   resolve the campaign from the authenticated session instead: map each bearer
   token / OAuth subject → a `campaign_id`, and construct `RefereeTools(repo, cid)`
   per request (cheap; `Repo.open` just wraps the connection). The discipline
   tools’ module-level `_ATTEMPT`/`_DELIVERY` state would move into the session too.

2. **Auth → identity.** The bearer gate in `http_server.py` is a single shared
   secret. Swap it for either (a) per-user API keys stored in a small `users`
   table keyed to `campaign_id`, or (b) MCP's OAuth flow. Add rate limiting at the
   Fly/edge layer.

3. **Scaling past one writer (only if needed).** To run >1 machine, move state off
   plain SQLite: LiteFS (keeps SQLite, adds replication) is the least-change path;
   Postgres via `state/db.py` (swap the connector, keep `repo.py`’s interface) is
   the heavier but most scalable option. Per-tenant DB files on the volume also
   work for modest user counts.

Estimated effort: a weekend for a private authed server (done — this is it); ~1–2
weeks for multi-tenant + OAuth + a managed DB.
