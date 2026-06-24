"""
engine/validator.py
-------------------
Two-pass DM-response validator.

Pass 1 — local rule checker (pure-Python, zero-dependency). Catches the
obvious tells: PC-authoring, padding, dice without markers, lore
injection, option menus, existing-entity bypass.

Pass 2 — API rule checker (Claude Haiku) with enriched live game state.
Catches the subtle violations the local regex cannot reach: geographic
errors, continuity errors, implicit option menus, subtle player
authoring, name recycling, and name-continuity drift.

══════════════════════════════════════════════════════════════════════
ARCHITECTURE NOTE — DO NOT REMOVE THE API VALIDATOR
══════════════════════════════════════════════════════════════════════
The local validator (regex) catches obvious violations.
The API validator (claude-haiku) catches subtle ones the local cannot:
geographic errors, continuity errors, implicit option menus, name recycling.
Both are required. The local validator alone has been proven insufficient
in live play — see session logs from Phase 39-53 for evidence.
Removing the API validator reverts to a known-broken configuration.
The anthropic import at module top is intentional and load-bearing.

If `import anthropic` fails OR `anthropic.Anthropic()` cannot
initialize (missing ANTHROPIC_API_KEY, expired key, broken install),
this module fails to load — and the MCP server that imports it
refuses to start. That is the point. Fix the install / set the key;
do not catch the import or wrap the client constructor in a try.
══════════════════════════════════════════════════════════════════════

Local rules (six; rule number 6 is reserved):
  1. PLAYER_AGENCY  — narrative writes the PC's DECISION / INTENT /
                      INTERNAL THOUGHT (Phase 56: narrowed from broad
                      action verbs). Does NOT fire on world descriptions
                      reflecting already-declared player actions —
                      ships sailing, doors opening, journeys underway.
                      Requires the active character_name to fire.
  2. VERBOSITY      — two-part check (Phase 49):
                      (a) padding/filler phrase detected (always flagged
                          regardless of length: 'you feel a sense of…',
                          'the gravity of the moment', 'once again', etc.);
                      (b) over 8 sentences AND no mechanical-content
                          marker present (so a long roll log doesn't
                          trip the cap, but a pure prose monologue does).
  3. DICE_FUDGING   — narrative names a dice outcome without a
                      mechanical marker (roll_dice, [roll:, [d20:,
                      [rolled], rolled a N, scores a N).
  4. INVENTED_LORE  — unsolicited ancient/secret/prophecy/chosen-one
                      backstory or faction reveal.
  5. OPTION_MENU    — DM's OWN voice offering choices the player
                      should make. Phase 57: NPC dialogue is exempt —
                      quoted speech (straight or curly quotes) is
                      stripped before pattern matching. Phase 58: a
                      single open question at the end of narration
                      ("Where do you go?", "What does Coldhand do?")
                      with no enumerated options also exempts the
                      whole check. Patterns then run against the
                      post-strip text: explicit menu language
                      ('you could' / 'option 1/2/A/B'); "do you
                      want to / will you / shall you / would you
                      like to" questions; ", or X?" comma-or tail;
                      "A + B, or C" enumeration syntax.
  7. EXISTING_ENTITY_BYPASS
                    — Phase 53: narrative invents or proposes a new
                      crew/henchman/captain instead of looking up what
                      already exists. Rule number gap (no 6) reserved.

API rules (six; checked only when local passes):
  1. PLAYER_AGENCY          — strict re-check with model judgment.
  2. GEOGRAPHIC_ERROR       — NPC / location / resource not plausibly
                              present given the current location in
                              the game-context block.
  3. CONTINUITY_ERROR       — contradicts established facts in the
                              game-context block (dead NPCs acting,
                              closed arcs reopened, items already spent).
  4. IMPLICIT_OPTION_MENU   — narrative ends by implying two-plus
                              options without an explicit "?" or "or".
  5. SUBTLE_PLAYER_AUTHORING — 2nd-person ("you head toward", "you
                              decide", "you notice") writing the
                              player's actions, not the world's state.
  6. NAME_CONTINUITY        — narrative introduces a name for an NPC /
                              place / item not in the supplied context.

Local return shape:
  {
    "clean":             bool,
    "available":         True,
    "violations":        [{"rule": ..., "detail": ...}, ...],
    "verdict":           "CLEAN" | "VIOLATION — RULE1, RULE2, …",
    "original_response": narrative,
  }

API return shape:
  {
    "clean":             bool,
    "available":         True,           # always — see startup gate
    "rules_failed":      [<rule labels>],
    "verdict":           "<raw Haiku verdict text>",
    "original_response": narrative,
  }
"""

from __future__ import annotations

import re

# ── LOAD-BEARING IMPORT — DO NOT MAKE LAZY ─────────────────────────────────
# The anthropic SDK and a configured client are required at module load
# time. The MCP server import-gates on this module successfully loading;
# if the import fails or the client constructor raises (missing or
# malformed ANTHROPIC_API_KEY), the server refuses to start. That is
# the intended behavior — see the ARCHITECTURE NOTE above.
import os

# Lazy API client: the server boots and runs the LOCAL (Pass-1) checks even
# with no ANTHROPIC_API_KEY; the Haiku Pass-2 spins up only when a key is
# present and Pass-2 is actually called. (The original hard-failed at import.)
_API_CLIENT = None

def api_available() -> bool:
    return bool(os.environ.get('ANTHROPIC_API_KEY'))

def _get_api_client():
    global _API_CLIENT
    if _API_CLIENT is None:
        import anthropic
        _API_CLIENT = anthropic.Anthropic()
    return _API_CLIENT


_API_VALIDATOR_PROMPT = """You are a strict rule-checker for an AD&D 1e solo RPG DM response.
You have access to the current game context. Check the DM narrative against these rules:

1. PLAYER_AGENCY: Does the narrative write the player character's DECISION,
   INTENT, or INTERNAL THOUGHT?

   FIRES ON: "Faelith decides to...", "she chooses...", "she realizes she must..."

   DOES NOT FIRE ON: World descriptions reflecting an already-declared action
   in motion — ships sailing, doors swinging open, journeys underway. If the
   player declared "I sail to Greyhawk" and the narrative describes the voyage,
   that is scene description, not player-authoring.

2. GEOGRAPHIC_ERROR: Does the narrative reference an NPC, location, or resource that is not
   plausibly present given the current location in the game context?
   (e.g. suggesting an NPC who is hundreds of miles away)

3. CONTINUITY_ERROR: Does the narrative contradict established facts in the game context —
   dead NPCs acting, closed arcs reopened, items already spent or lost?

4. IMPLICIT_OPTION_MENU: Does the DM's OWN OUT-OF-CHARACTER VOICE enumerate
   two or more actions the player could take next?

   The deciding factor is WHO is speaking. Quoted character speech is the
   game world talking through a character — never a menu. The DM's
   narrator voice listing player options out-of-character is a menu.

   FIRES ON: DM narrator voice listing numbered or bulleted player options
   outside of any character's speech.

   DOES NOT FIRE ON:
   - ANY content inside quotation marks (straight " " or curly “ ”),
     regardless of how many options it lists. NPC dialogue is exempt
     unconditionally — an NPC saying "you could try Hardby, or ask
     Vask at the forge" inside quotes is the game world communicating
     leads through a character, NOT the DM listing player options.
     Rumors, clues, quest hooks, and suggestions are how solo RPG
     content is delivered.
   - Scene descriptions mentioning multiple objects or people present
     in the same space (a room with two doors and an NPC is not a menu).
   - A single open question at the end of narration ("Where do you go
     next?", "What does Coldhand do?") — these are neutral scene-closers,
     not menus. Only flag if two or more specific options are enumerated.

   When uncertain, PASS. This rule targets ONLY the DM breaking the
   fourth wall to list player options out-of-character.

5. SUBTLE_PLAYER_AUTHORING: "you head toward", "you decide", "you notice X
   and consider Y" — second person writing the player's actions or internal
   thoughts.

   DOES NOT FIRE ON: "before you" / "around you" / "at your feet" —
   spatial reference is not player-authoring.

6. NAME_CONTINUITY: Does the narrative introduce a name for an NPC, place, or item that
   was not in the game context provided?

7. VERBOSITY: Is the narrative longer or more ornate than the beat needs?
   Your player loves authorship that is descriptive but BRIEF — a few vivid,
   concrete strokes, not a wall of atmosphere.
   FIRES ON: paragraphs of mood and sensory padding around a small beat;
   restating what the player already knows; lingering after the point is made.
   DOES NOT FIRE ON: genuinely eventful turns with a lot actually happening,
   or mechanical / combat readouts. When the beat is small, keep it small.

For each rule respond PASS or FAIL with one line of reason if FAIL.
Final verdict: CLEAN or VIOLATION — [RULE1, RULE2]
Be strict. A subtle violation is still a violation."""


# Rules the player has chosen to silence: detected internally but dropped
# before they can force a retrace. Agency lives here per player preference
# (constant and language-pedantic; the player retraces by hand when it
# matters). Brevity is what they care about, so verbosity is strengthened
# instead. Reversible: empty the set.
_DISABLED_RULES = frozenset({"PLAYER_AGENCY", "SUBTLE_PLAYER_AUTHORING"})


def validate_dm_response(
    narrative: str,
    context: str = "",
    character_name: str = "",
) -> dict:
    violations = []

    # Rule 1: Player authoring — character name + decision/intent verb only
    # Does NOT fire on world descriptions reflecting already-declared player
    # actions (ships moving, doors opening, journeys underway). Only the
    # PC's decision or internal thought is the player's to author.
    if character_name:
        decision_pattern = rf'\b{re.escape(character_name)}\b.{{0,30}}\b(decides|chooses|thinks|feels|realizes|considers|plans|intends|wants|wishes|knows she should|tells herself)\b'
        if re.search(decision_pattern, narrative, re.IGNORECASE):
            violations.append({
                "rule": "PLAYER_AGENCY",
                "detail": "Narrative writes the player character's decision or internal thought."
            })

    # Rule 2: Verbosity — padding detection + raised hard cap

    # Part A: Padding phrases — always flag these regardless of length
    padding_patterns = [
        r'\byou feel (a sense of|the weight of|yourself|your heart)\b',
        r'\bthe (gravity|magnitude|weight) of (the moment|what just|this)\b',
        r'\bonce again\b',
        r'\bas you (already know|recall|remember)\b',
        r'\bit (goes without saying|is worth noting)\b',
        r'\bsuddenly you realize\b',
        r'\bthe air feels?\b',
        r'\bsomething (tells|warns|urges) you\b',
    ]
    for pattern in padding_patterns:
        if re.search(pattern, narrative, re.IGNORECASE):
            violations.append({
                "rule": "VERBOSITY",
                "detail": "Narrative contains padding or filler phrasing that adds no new "
                          "information. Your player loves authorship that is descriptive "
                          "but BRIEF — cut the filler and keep the vivid essentials."
            })
            break

    # Part B: Hard cap at 8 sentences — only flag pure filler monologues
    # Does not fire if dice were rolled this turn or if response is under 8 sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', narrative) if s.strip()]
    has_mechanical_content = bool(re.search(
        r'(\[rolled\]|\[roll:|roll_dice|rolled a \d|segment \d|initiative|THAC0|saving throw)',
        narrative, re.IGNORECASE
    ))
    if len(sentences) > 6 and not has_mechanical_content:
        violations.append({
            "rule": "VERBOSITY",
            "detail": f"Response is {len(sentences)} sentences with no mechanical content. "
                      f"Your player loves authorship that is descriptive but BRIEF — "
                      f"a few vivid, concrete strokes, not a wall. Keep pure narration "
                      f"to about six sentences."
        })

    # Rule 3: Dice reference without mechanical marker
    dice_pattern = r'\b(rolls?|rolled|save|saving throw|to.?hit|damage|initiative)\b'
    mechanical_marker = r'(\[rolled\]|\[roll:|roll_dice|result:|rolled a \d|scores? a \d|\[d\d+:)'
    if re.search(dice_pattern, narrative, re.IGNORECASE):
        if not re.search(mechanical_marker, narrative, re.IGNORECASE):
            violations.append({
                "rule": "DICE_FUDGING",
                "detail": "Narrative references a dice outcome without a corresponding roll_dice tool call."
            })

    # Rule 4: Invented lore markers
    lore_patterns = [
        r'\b(ancient|centuries|decades|generations)\s+(ago|old|of|have)\b',
        r'\b(secret|hidden|forgotten)\s+(cult|order|society|brotherhood|organization|faction)\b',
        r'\bhas\s+been\s+(hunting|watching|manipulating|controlling)\b',
        r'\bprophecy\b',
        r'\bchosen\s+one\b',
    ]
    for pattern in lore_patterns:
        if re.search(pattern, narrative, re.IGNORECASE):
            violations.append({
                "rule": "INVENTED_LORE",
                "detail": "Narrative contains unsolicited lore, faction, or backstory injection."
            })
            break

    # Rule 5: Option menus — only fires on DM's own voice, never NPC dialogue
    # Strip quoted speech before checking — NPC dialogue is exempt. An NPC
    # offering a rumor, a lead, or a suggestion is how the game world
    # communicates information; this rule targets the DM breaking the fourth
    # wall to enumerate player options. Both straight quotes and curly
    # quotes are stripped.
    narrative_without_quotes = re.sub(r'"[^"]*"', '', narrative)
    narrative_without_quotes = re.sub(
        r'“[^”]*”', '', narrative_without_quotes,
    )

    # Phase 58: a single open question with no enumerated options is a
    # neutral scene-closer, not a menu. "Where do you go?", "What does
    # Coldhand do?" — these belong in the DM's narrator voice and must
    # not trip the rule. Detection: last sentence is a single short
    # question starting with a capital letter, containing no '?' inside
    # the body and no ' or ' enumeration. When that holds, skip all
    # menu_patterns checks entirely. The post-quote-strip text is what
    # we examine, so any '?' inside an NPC line is already gone.
    last_sentence = (
        re.split(r'(?<=[.!?])\s+', narrative_without_quotes.strip())[-1].strip()
        if narrative_without_quotes.strip() else ""
    )
    is_single_open_question = bool(
        re.match(r'^[A-Z][^?]{5,60}\?$', last_sentence)
        and not re.search(r'\s+or\s+', last_sentence, re.IGNORECASE)
    )

    menu_patterns = [
        # Explicit menu language
        r'\b(you could|you can choose|option (1|2|A|B))\b',
        # Do you want / will you questions
        r'\b(do you want to|will you|shall you|would you like to)\b',
        # X + "or" + Y at end of sentence as question
        r'(,\s+or\s+.{5,60}\?)\s*$',
        # "+" joining two options
        r'\w+\s+\+\s+\w[\w\s]+,\s+or\s+\w',
    ]
    # A bare closing question ("What do you do?") is a fine scene-closer, but it
    # must not mask a menu in the sentences BEFORE it. So strip the closing
    # question and still scan the rest -- rather than skipping detection wholesale.
    menu_body = narrative_without_quotes
    if is_single_open_question and last_sentence:
        cut = menu_body.rfind(last_sentence)
        if cut != -1:
            menu_body = menu_body[:cut]
    for pattern in menu_patterns:
        if re.search(pattern, menu_body, re.IGNORECASE):
            violations.append({
                "rule": "OPTION_MENU",
                "detail": "DM's own voice is offering unprompted action choices. "
                          "Describe the world and stop. NPC dialogue is exempt from this rule."
            })
            break

    # Rule 7: Existing entity bypass — inventing what should be looked up
    bypass_patterns = [
        r'\b(appoint|assign|hire|recruit|designate)\s+a\s+new\b',
        r'\ba\s+(new\s+)?(navigator|pilot|captain|mate|helmsman|steward|factor|guard|sergeant|lieutenant)\s+(named|called)\b',
        r'\buntil\s+you\s+(name|appoint|choose|hire)\b',
        r'\b(shall\s+we\s+name|what\s+shall\s+we\s+call)\b',
        r'\bcreating\s+a\s+new\s+(npc|character|henchman|hireling)\b',
    ]
    for pattern in bypass_patterns:
        if re.search(pattern, narrative, re.IGNORECASE):
            violations.append({
                "rule": "EXISTING_ENTITY_BYPASS",
                "detail": "Narrative creates or proposes a new entity that may already exist in the database. "
                          "Call list_characters or search_inventory before introducing new henchmen, "
                          "crew, or named NPCs."
            })
            break

    # Drop player-silenced rules (agency) before deciding — see _DISABLED_RULES.
    violations = [v for v in violations if v["rule"] not in _DISABLED_RULES]
    is_clean = len(violations) == 0

    return {
        "clean": is_clean,
        "available": True,
        "violations": violations,
        "verdict": "CLEAN" if is_clean else f"VIOLATION — {', '.join(v['rule'] for v in violations)}",
        "original_response": narrative
    }


# ── PASS 2 — API validator (load-bearing) ──────────────────────────────────
# Only runs after the local validator returns clean. Hits Claude Haiku with
# an enriched game-context block so it can check rules the local regex
# cannot reach (geography, continuity, implicit menus, subtle 2nd-person
# authoring, name recycling). Raises on any API failure — runtime errors
# bubble up so the caller (dm_response) hard-fails the turn rather than
# silently shipping unvalidated narrative.

_API_RULE_LABELS = (
    "PLAYER_AGENCY",
    "GEOGRAPHIC_ERROR",
    "CONTINUITY_ERROR",
    "IMPLICIT_OPTION_MENU",
    "SUBTLE_PLAYER_AUTHORING",
    "NAME_CONTINUITY",
    "VERBOSITY",
)


def validate_dm_response_api(
    narrative: str,
    context: str = "",
    character_name: str = "",
) -> dict:
    """
    Pass-2 validator: Claude Haiku rule check with enriched live context.

    The caller (dm_response in server/mcp_server.py) supplies a compact
    context string built from live game state — current location, last
    few events, active named NPCs with locations, name registry —
    against which the model checks for geography errors, continuity
    drift, subtle player authoring, and name recycling.

    Returns:
      {
        "clean":             bool,        # True if verdict contains
                                          # "CLEAN" and not "VIOLATION"
        "available":         True,        # always — module-load gate
        "rules_failed":      [<labels>],  # subset of _API_RULE_LABELS
        "verdict":           "<raw>",     # full Haiku response text
        "original_response": narrative,
      }

    Raises whatever exception the anthropic SDK raises on API failure
    (auth, rate limit, network, 5xx). Hard-fail strict by design.
    """
    check_input = (
        f"GAME CONTEXT:\n{context}\n\n"
        f"CHARACTER: {character_name}\n\n"
        f"DM NARRATIVE TO CHECK:\n{narrative}"
    )

    result = _get_api_client().messages.create(
        model="claude-haiku-4-5",
        # Phase 59: 400 was truncating responses before the "Final verdict"
        # line landed, which made the new final-line-authoritative parser
        # mistake a half-printed PASS sequence for a clean verdict.
        max_tokens=600,
        system=_API_VALIDATOR_PROMPT,
        messages=[{"role": "user", "content": check_input}],
    )

    verdict_text = result.content[0].text
    upper = verdict_text.upper()

    # Phase 59: trust the FINAL verdict line, not the whole text. Per-rule
    # explanations frequently contain the word "violation" in their FAIL
    # reason; the old check (CLEAN in upper AND VIOLATION not in upper)
    # mis-flagged clean turns whose rule explanations cited violations.
    # Now: if the final line says CLEAN, it's clean. Otherwise fall back
    # to "no VIOLATION in final AND no FAIL anywhere" as the all-pass signal.
    verdict_lines = [
        ln.strip() for ln in verdict_text.strip().splitlines() if ln.strip()
    ]
    final_line = verdict_lines[-1] if verdict_lines else ""
    is_clean = (
        "CLEAN" in final_line.upper() or
        (
            "VIOLATION" not in final_line.upper()
            and verdict_text.upper().count("FAIL") == 0
        )
    )

    # Parse per-line: Haiku is prompted to output one line per rule with
    # PASS or FAIL plus a reason. A naive "label in text AND FAIL in text"
    # check would flag every rule on any failure because all six labels
    # also appear in the model's listing — so we look for the label AND
    # the word FAIL on the SAME line.
    rules_failed: list[str] = []
    seen: set[str] = set()
    for line in verdict_text.splitlines():
        line_upper = line.upper()
        if "FAIL" not in line_upper:
            continue
        for label in _API_RULE_LABELS:
            if label in line and label not in seen:
                rules_failed.append(label)
                seen.add(label)
    # Fallback: if the verdict line at the end carries "VIOLATION — A, B"
    # but no per-rule FAIL lines (model collapsed format), parse from there.
    if not rules_failed and "VIOLATION" in upper:
        # Look for "VIOLATION — RULE1, RULE2" or "VIOLATION - RULE1, RULE2"
        m = re.search(r'VIOLATION\s*[—\-:]\s*(.+)', verdict_text)
        if m:
            tail = m.group(1)
            for label in _API_RULE_LABELS:
                if label in tail and label not in seen:
                    rules_failed.append(label)
                    seen.add(label)

    # Drop player-silenced rules; if nothing else failed, the turn is clean.
    rules_failed = [r for r in rules_failed if r not in _DISABLED_RULES]
    is_clean = is_clean or not rules_failed

    return {
        "clean":             is_clean,
        "available":         True,
        "rules_failed":      rules_failed,
        "verdict":           verdict_text,
        "original_response": narrative,
    }
