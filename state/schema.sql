-- OSRIC / World of Greyhawk campaign state (SQLite).
-- The database is the source of truth: every meaningful change is written here,
-- and mutations also append to the `event` chronicle. This mirrors the Cepheus
-- design that proved solid. `CREATE TABLE IF NOT EXISTS` means every connect
-- auto-migrates new tables.

PRAGMA foreign_keys = ON;

-- A campaign is the top-level container: it holds many characters, NPCs, and
-- (later) domains, ships, and its own chronicle.
CREATE TABLE IF NOT EXISTS campaign (
    id                    INTEGER PRIMARY KEY,
    name                  TEXT NOT NULL,
    setting               TEXT NOT NULL DEFAULT 'World of Greyhawk',
    current_date          TEXT,                 -- in-game date, e.g. 'Reaping 4, 576 CY'
    -- Old-school toggle: when 1, racial class restrictions and level limits are
    -- waived for this campaign (Greyhawk "anything goes"); 0 = by the book.
    allow_race_overrides  INTEGER NOT NULL DEFAULT 0,
    -- When 1, gaining a level requires training (time + gold); XP banks until then.
    training_required     INTEGER NOT NULL DEFAULT 0,
    notes                 TEXT DEFAULT '',
    created_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS character (
    id             INTEGER PRIMARY KEY,
    campaign_id    INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    name           TEXT NOT NULL,
    player         TEXT DEFAULT '',              -- who runs this PC ('' for NPCs)
    race           TEXT,
    classes_json   TEXT NOT NULL DEFAULT '[]',   -- [{class, level, xp}] multi/dual-class
    alignment      TEXT,
    -- Ability scores as columns (queryable). str_pct = exceptional Strength %.
    str_score      INTEGER, str_pct INTEGER DEFAULT 0,
    dex_score      INTEGER, con_score INTEGER,
    int_score      INTEGER, wis_score INTEGER, cha_score INTEGER,
    hp_max         INTEGER, hp_current INTEGER,
    ac_descending  INTEGER,                       -- classic AC (lower is better)
    ac_ascending   INTEGER,                       -- ascending AC (higher is better)
    damage_dice    TEXT,                           -- default attack damage (mainly for NPC/monster combatants)
    cargo_json     TEXT,                           -- trade cargo: [{good, tons, buy_price}]
    vessel_json    TEXT,                           -- assigned carrier: {type, addons}
    specialization_json TEXT,                      -- weapon specialisation: {weapon, double}
    dual_class_json     TEXT,                       -- dual-class: {from, from_level, to}
    proficiencies_json  TEXT,                       -- proficient weapon names (else assume all)
    gold           INTEGER NOT NULL DEFAULT 0,
    gear_json      TEXT NOT NULL DEFAULT '[]',
    spellbook_json TEXT NOT NULL DEFAULT '[]',    -- spells known/scribed
    memorized_json TEXT NOT NULL DEFAULT '[]',    -- spells currently memorized
    age            INTEGER,
    status         TEXT DEFAULT 'ok',             -- ok | injured | unconscious | dead
    alive          INTEGER NOT NULL DEFAULT 1,
    is_npc         INTEGER NOT NULL DEFAULT 0,
    notes          TEXT DEFAULT '',
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_char_campaign ON character(campaign_id);

-- Append-only narrative/event spine -- the "write it down" backbone that the
-- referee rebuilds its memory from each turn.
CREATE TABLE IF NOT EXISTS event (
    id            INTEGER PRIMARY KEY,
    campaign_id   INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    ts            TEXT NOT NULL DEFAULT (datetime('now')),
    in_game_date  TEXT,
    kind          TEXT,                          -- combat | travel | trade | note ...
    summary       TEXT NOT NULL,
    detail_json   TEXT DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_event_campaign ON event(campaign_id);

-- In-progress, replayable character creation. Persisted so an interactive build
-- survives restarts/redeploys: we store the seed and the ordered list of choices
-- and deterministically replay them to rebuild the live builder.
CREATE TABLE IF NOT EXISTS chargen_session (
    id            TEXT PRIMARY KEY,             -- opaque session id (uuid hex)
    campaign_id   INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    handle        TEXT NOT NULL,                -- working label until named at the end
    seed          INTEGER NOT NULL,             -- RNG seed for deterministic replay
    method        TEXT,                         -- 4d6 | 5d6 | input
    choices_json  TEXT NOT NULL DEFAULT '[]',   -- ordered choice payloads
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_chargen_campaign ON chargen_session(campaign_id);

-- A ruler's dominion (the realm/domain layer).
CREATE TABLE IF NOT EXISTS dominion (
    id            INTEGER PRIMARY KEY,
    campaign_id   INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    ruler         TEXT,                          -- character name
    title         TEXT,                          -- Baron, Count, ...
    confidence    INTEGER NOT NULL DEFAULT 50,
    tax_rate_gp   REAL NOT NULL DEFAULT 1.0,
    has_liege     INTEGER NOT NULL DEFAULT 1,
    fiefs_json    TEXT NOT NULL DEFAULT '[]',     -- [{terrain, civ_level, families, resources}]
    troops_json   TEXT NOT NULL DEFAULT '[]',     -- [{name, count, cost_each}]
    notes         TEXT DEFAULT '',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_dominion_campaign ON dominion(campaign_id);

-- Map locations on the Flanaess hex grid (kind 'party' marks the party's hex).
CREATE TABLE IF NOT EXISTS location (
    id            INTEGER PRIMARY KEY,
    campaign_id   INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    kind          TEXT,                          -- city | town | dungeon | landmark | region | party
    terrain       TEXT,                          -- plains | forest | hills | mountains | water ...
    hex_col       INTEGER, hex_row INTEGER,
    economies     TEXT,                          -- comma-separated economy tags (Port, Mining...)
    notes         TEXT DEFAULT '',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_location_campaign ON location(campaign_id);

-- Hirelings and henchmen: an NPC character (character_id) bound to a master PC,
-- with the loyalty circumstances from OSRIC Section 2.2.4. Loyalty is recomputed
-- from these factors plus the master's Charisma whenever it is tested.
CREATE TABLE IF NOT EXISTS retainer (
    id            INTEGER PRIMARY KEY,
    campaign_id   INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    character_id  INTEGER REFERENCES character(id) ON DELETE CASCADE,
    master        TEXT NOT NULL,                  -- the PC they serve
    status        TEXT NOT NULL DEFAULT 'follower',   -- conscript/hireling/follower/henchman
    relationship  TEXT NOT NULL DEFAULT 'similar',    -- alignment fit to the master
    service       TEXT NOT NULL DEFAULT '0-1 years',
    training      TEXT NOT NULL DEFAULT 'trained',
    payment       TEXT NOT NULL DEFAULT 'standard',
    treatment     TEXT NOT NULL DEFAULT 'normal',
    discipline    TEXT NOT NULL DEFAULT 'indifferent',
    notes         TEXT DEFAULT '',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_retainer_campaign ON retainer(campaign_id);

-- An active combat: its roster of combatants and the current round's initiative
-- order. OSRIC re-rolls initiative each round, so order_json is rebuilt per round.
CREATE TABLE IF NOT EXISTS combat (
    id            INTEGER PRIMARY KEY,
    campaign_id   INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    round         INTEGER NOT NULL DEFAULT 1,
    active        INTEGER NOT NULL DEFAULT 1,
    combatants_json TEXT NOT NULL DEFAULT '[]',  -- [{name, side, dex, weapon_speed, action, casting_time}]
    order_json    TEXT NOT NULL DEFAULT '[]',     -- this round's resolved order
    acted_json    TEXT NOT NULL DEFAULT '[]',     -- names who have acted this round
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_combat_campaign ON combat(campaign_id);

-- Per-turn narration log. The referee replays the last few of these as
-- conversation history so the model remembers what just happened -- each
-- model call is otherwise stateless, so without this a journey narrated
-- last turn is forgotten and the scene snaps back to a default. The DB
-- tables above are the source of truth for numbers; this is the source of
-- truth for continuity.
CREATE TABLE IF NOT EXISTS turn_log (
    id            INTEGER PRIMARY KEY,
    campaign_id   INTEGER NOT NULL REFERENCES campaign(id) ON DELETE CASCADE,
    ts            TEXT NOT NULL DEFAULT (datetime('now')),
    speaker       TEXT,
    player_input  TEXT,
    narration     TEXT
);
CREATE INDEX IF NOT EXISTS idx_turnlog_campaign ON turn_log(campaign_id);
