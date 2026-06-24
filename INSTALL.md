# Registering the new Greyhawk MCP game with Claude desktop

This is the melded OSRIC + Dark Dungeons + Cepheus engine, rebuilt as an MCP
server. Claude desktop is the DM; this server is the deterministic engine, the
database is the truth. It runs alongside your existing games and touches none of
them.

**Good news: your runtime is already set up.** Your existing greyhawk servers
run from a venv that already has `mcp` and `anthropic`, and your
`ANTHROPIC_API_KEY` is a Windows user env var. So there's nothing new to
install — you just point the new entry at the Python you already use.

## 1. Add the connector entry

Open `%APPDATA%\Claude\claude_desktop_config.json` and merge the `greyhawk-dnd`
entry from `connector_config.json` into `mcpServers` (keep your existing
entries). Two things to confirm:

- **`command`** — set it to the same venv Python your other greyhawk servers
  use (the config currently points at
  `ClaudeDnD\greyhawk-solo\.venv\Scripts\python.exe`; change it if yours lives
  elsewhere). That interpreter already has `mcp` + `anthropic`, and the engine
  itself is pure stdlib.
- The name stays **`greyhawk-dnd`** — that prefix is what the key-patcher keys on.

The launcher needs no working directory: `server/mcp_server.py` adds its own
project root to `sys.path`, so the absolute path in `args` is enough — even when
run by another project's venv Python.

## 2. Inject your API key (for Pass-2 validation)

Run your existing patcher — it adds `ANTHROPIC_API_KEY` to every `greyhawk-*`
entry, including the new one:

```
python C:\Users\Raymond\Documents\ClaudeDnD\greyhawk-solo\patch_claude_config.py
```

(Optional: without a key the server still runs every local check — agency,
verbosity, menus, dice, lore — and only skips the Haiku Pass-2 layer.)

## 3. Restart Claude desktop

**greyhawk-dnd** appears in your connectors. Open a chat and start playing —
"Set the scene; I'm a new adventurer arriving in Greyhawk," or ask it to roll up
a character. The DM has 90 tools: 87 deterministic engine tools (chargen,
combat, spells, domains, trade, naval, the bestiary, the rules corpus) plus
`dm_response`, `dm_quick`, and `save_turn`.

## Verified

- Real MCP handshake: `initialize` → `tools/list` returns 90 tools over stdio.
- `roll_dice`, `lookup_rule` (against the 105 MB corpus), `get_monster`,
  `generate_weather`, and the realm layer all dispatch through the bridge.
- `dm_response` validates (reject→rewrite→deliver-flagged), `dm_quick` bounces
  prose, `save_turn` writes the chronicle and flags bypasses.
- Engine self-tests: 43/43 in this folder.

## What's wired in

- **Directive**: the all-carrot "what your player loves" prompt, at connect time.
- **dm_response / dm_quick / save_turn**: tonight's discipline, adapted to this
  engine's `event` / `turn_log` spine.
- **Robustness**: the validator's Haiku client is lazy, so the server boots and
  runs local checks even with no key.
