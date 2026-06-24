"""selfplay_gym.py -- the training gym: automated player + engine-as-judge.

The loop you asked for: a model plays the DM, the engine grades every turn with a
deterministic, verifiable reward (did it call the tool the action required? did
any tool error?), and the turns that PASS are written to the training corpus.
Run it fast against a hosted model and keep only the survivors -- expert
iteration / "corrected until it stops."

The engine is the referee AND the reward function. Nothing here trusts the model;
it executes the model's tool calls and checks the result against what the action
demanded.

Plug in your model by passing a `policy(scenario, tools, ctx) -> response` where
response = {"tool_calls": [{"name","args"}], "narration": str}. The built-in
reference_policy emits the canonical correct calls, so you can run the gym today
(it both smoke-tests the loop and mints clean synthetic gold examples).
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List

from state.repo import Repo
from engine.dice import Dice
from engine.data import advancement as adv
from referee.tools import RefereeTools

SYSTEM = ("You are the Dungeon Master for an AD&D 1e / OSRIC game. The engine owns "
          "all mechanics: for any action with a mechanical outcome you MUST call "
          "the matching tool and narrate ONLY from what it returns. Never invent a "
          "number, a hit, a death, or a state change.")


# ---- the reward: deterministic, engine-backed -------------------------
def grade(required: set, calls: List[Dict[str, Any]],
          results: List[Any], narration: str) -> Dict[str, Any]:
    """Score one turn. pass = the required tool(s) were called and nothing errored.
    A soft check flags numbers in the prose that no tool produced (likely invented)."""
    called = {c.get("name") for c in calls}
    missing = sorted(required - called)
    errors = [r for r in results if isinstance(r, dict) and "error" in r]
    # soft: did the narration assert a number that appears in no tool result?
    tool_blob = " ".join(json.dumps(r) for r in results)
    invented = [n for n in re.findall(r"\b\d{1,4}\b", narration or "")
                if n not in tool_blob]
    reasons = []
    if missing:
        reasons.append("did not call required tool(s): {}".format(", ".join(missing)))
    if errors:
        reasons.append("tool error(s): {}".format("; ".join(
            e.get("error", "?") for e in errors)))
    passed = not missing and not errors
    return {"reward": 1.0 if passed else 0.0, "passed": passed,
            "missing": missing, "errors": [e.get("error") for e in errors],
            "invented_numbers": invented, "reasons": reasons}


# ---- scenarios: the automated player ----------------------------------
def _pc(t, name, cls="Fighter", level=1, **kw):
    base = {"name": name, "race": "Human", "classes": [{"class": cls, "level": level}],
            "alignment": "N", "str": 14, "dex": 13, "con": 12, "int": 10, "wis": 12,
            "cha": 10, "hp_max": 12, "hp_current": 12, "ac_descending": 5, "gold": 5000}
    base.update(kw)
    return t.repo.save_character(t.cid, base, is_npc=kw.get("is_npc", False))


class Scenario:
    name = "base"
    text = ""
    required: set = set()
    def setup(self, t) -> Dict[str, Any]: return {}
    def gold(self, t, ctx) -> List[Dict[str, Any]]: return []


class Attack(Scenario):
    name = "attack"
    text = "I close with the goblin and swing my longsword!"
    required = {"attack"}
    def setup(self, t):
        _pc(t, "Bron", "Fighter", 3, str=16)
        _pc(t, "Goblin", "Fighter", 1, is_npc=True, race="Goblin", hp_max=6, hp_current=6, ac_descending=6)
        t.start_combat(combatants=[{"name": "Bron", "side": "party"},
                                   {"name": "Goblin", "side": "foes"}])
        return {"a": "Bron", "d": "Goblin"}
    def gold(self, t, ctx):
        return [{"name": "attack", "args": {"attacker": ctx["a"], "defender": ctx["d"],
                                            "weapon": "Sword, long"}}]


class Heal(Scenario):
    name = "heal"
    text = "I lay hands on Hurt and call a cure upon his wounds."
    required = {"cast_spell"}
    def setup(self, t):
        _pc(t, "Priest", "Cleric", 3, wis=16, memorized=["Cure Light Wounds"])
        _pc(t, "Hurt", "Fighter", 2, hp_max=16, hp_current=3)
        return {}
    def gold(self, t, ctx):
        return [{"name": "cast_spell", "args": {"name": "Priest",
                "spell": "Cure Light Wounds", "targets": ["Hurt"]}}]


class ThiefSkill(Scenario):
    name = "thief_skill"
    text = "I creep down the hall, moving silently."
    required = {"thief_skill"}
    def setup(self, t):
        _pc(t, "Sly", "Thief", 4, dex=17)
        return {}
    def gold(self, t, ctx):
        return [{"name": "thief_skill", "args": {"name": "Sly", "skill": "move silently"}}]


class Search(Scenario):
    name = "search"
    text = "I tap the walls, searching for a secret door."
    required = {"search"}
    def setup(self, t):
        _pc(t, "Scout", "Fighter", 2, race="Elf")
        return {}
    def gold(self, t, ctx):
        return [{"name": "search", "args": {"name": "Scout", "what": "secret doors"}}]


class Rest(Scenario):
    name = "rest"
    text = "We make camp and rest for three days to recover."
    required = {"rest"}
    def setup(self, t):
        t.repo.set_date(t.cid, "Reaping 1, 576 CY")
        _pc(t, "Bron", "Fighter", 2, hp_max=16, hp_current=8)
        return {}
    def gold(self, t, ctx):
        return [{"name": "rest", "args": {"days": 3}}]


class GrantXP(Scenario):
    name = "grant_xp"
    text = "We split the treasure and tally our experience from the fight."
    required = {"grant_xp"}
    def setup(self, t):
        _pc(t, "Bron", "Fighter", 1)
        return {}
    def gold(self, t, ctx):
        return [{"name": "grant_xp", "args": {"amount": adv.xp_for_level("Fighter", 2),
                                              "name": "Bron"}}]


SCENARIOS = [Attack(), Heal(), ThiefSkill(), Search(), Rest(), GrantXP()]


# ---- policies ---------------------------------------------------------
def reference_policy(scenario: Scenario, tools: RefereeTools,
                     ctx: Dict[str, Any]) -> Dict[str, Any]:
    """The deterministic expert: emits the canonical correct tool calls and
    narrates from their results. Use it to mint gold data and to sanity-check."""
    calls = scenario.gold(tools, ctx)
    results = [tools.dispatch(c["name"], c.get("args", {})) for c in calls]
    return {"tool_calls": calls, "narration": _narrate(scenario, results),
            "_results": results}


def lazy_policy(scenario, tools, ctx):
    """A deliberately bad DM that just narrates and skips the tools -- for testing
    that the grader actually fails fabrication."""
    return {"tool_calls": [], "narration": "You strike true for 7 damage and it dies."}


def _narrate(scenario, results):
    if not results:
        return "Nothing of mechanical note happens."
    return "{}: {}".format(scenario.name, json.dumps(results[0])[:200])


# ---- the loop ---------------------------------------------------------
def _fresh_tools(seed: int) -> RefereeTools:
    repo = Repo.memory()
    cid = repo.create_campaign("Gym")
    return RefereeTools(repo, cid, dice=Dice(seed))


def run(policy: Callable = reference_policy, rounds: int = 1, seed: int = 0,
        out_path: str = None) -> Dict[str, Any]:
    """Play every scenario `rounds` times through `policy`, grade each turn, and
    (optionally) append every PASSING turn to an SFT JSONL corpus. Returns stats
    and the full transcript."""
    transcript, n_pass = [], 0
    out = open(out_path, "a", encoding="utf-8") if out_path else None
    s = seed
    for _ in range(rounds):
        for scn in SCENARIOS:
            s += 1
            tools = _fresh_tools(s)
            ctx = scn.setup(tools)
            resp = policy(scn, tools, ctx)
            calls = resp.get("tool_calls", [])
            # If the policy didn't pre-execute, run its calls now through the engine.
            results = resp.get("_results")
            if results is None:
                results = [tools.dispatch(c["name"], c.get("args", {})) for c in calls]
            g = grade(scn.required, calls, results, resp.get("narration", ""))
            transcript.append({"scenario": scn.name, "passed": g["passed"],
                               "reasons": g["reasons"]})
            if g["passed"]:
                n_pass += 1
                if out:
                    out.write(json.dumps({"messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": "PLAYER: " + scn.text},
                        {"role": "assistant", "content": resp.get("narration", ""),
                         "tool_calls": calls}]}) + "\n")
    if out:
        out.close()
    total = len(transcript)
    return {"episodes": total, "passed": n_pass,
            "pass_rate": round(n_pass / total, 3) if total else 0.0,
            "transcript": transcript}


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else None
    rep = run(rounds=5, out_path=out)
    print("self-play (reference policy): {}/{} passed ({})".format(
        rep["passed"], rep["episodes"], rep["pass_rate"]))
    if out:
        print("wrote passing turns ->", out)
