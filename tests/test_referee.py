"""Tests the referee turn loop with a scripted client (no key / network)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state.repo import Repo
from referee.referee import Referee
from referee.llm import (ScriptedClient, NoKeyClient, LLMResponse, ToolCall,
                         OpenAICompatibleClient)
from referee.tools import RefereeTools
from referee import prompt


def _campaign_with_pc():
    repo = Repo.memory()
    cid = repo.create_campaign("Greyhawk", current_date="Reaping 4, 576 CY")
    repo.save_character(cid, {
        "name": "Faelith", "race": "Human",
        "classes": [{"class": "Fighter", "level": 1, "xp": 0}],
        "alignment": "CG", "str": 16, "dex": 13, "con": 14,
        "int": 10, "wis": 11, "cha": 12, "hp_max": 9, "ac_descending": 5,
    })
    return repo, cid


def test_context_has_party_and_date():
    repo, cid = _campaign_with_pc()
    ctx = prompt.build_context(repo, cid)
    assert "Faelith" in ctx and "Fighter" in ctx
    assert "576 CY" in ctx


def test_turn_executes_tool_then_narrates():
    repo, cid = _campaign_with_pc()
    # The model first records an event, then narrates.
    client = ScriptedClient([
        LLMResponse(tool_calls=[ToolCall(
            id="1", name="record_event",
            arguments={"summary": "The party descends into the Maure Castle dungeon.",
                       "kind": "travel"})]),
        LLMResponse(text="Cold air rises from the stair. Torchlight gutters. "
                         "What do you do?"),
    ])
    ref = Referee(repo, cid, client=client)
    out = ref.turn("We head down the stairs.", speaker="Faelith")
    assert "Torchlight" in out
    # The tool actually ran -- the event is on the chronicle.
    evs = repo.recent_events(cid)
    assert any("Maure Castle" in e["summary"] for e in evs)


def test_turn_uses_dice_tool():
    repo, cid = _campaign_with_pc()
    client = ScriptedClient([
        LLMResponse(tool_calls=[ToolCall(id="1", name="roll_dice",
                                         arguments={"notation": "1d20+2"})]),
        LLMResponse(text="The blade bites home."),
    ])
    ref = Referee(repo, cid, client=client)
    out = ref.turn("I attack the goblin.")
    assert out == "The blade bites home."
    assert len(client.calls) == 2          # one tool round, one narration


def test_no_key_client_is_graceful():
    repo, cid = _campaign_with_pc()
    ref = Referee(repo, cid, client=NoKeyClient())
    out = ref.turn("Hello?")
    assert "offline" in out.lower()


def test_salvages_leaked_tool_call():
    # DeepSeek sometimes emits a tool call as TEXT in its private markup.
    content = ('<｜｜DSML｜｜tool_calls> '
               '<｜｜DSML｜｜invoke name="lookup_rule"> '
               '<｜｜DSML｜｜parameter name="query" string="true">'
               'cleric spells per day</｜｜DSML｜｜parameter> '
               '</｜｜DSML｜｜invoke> </｜｜DSML｜｜tool_calls>')
    data = {"choices": [{"message": {"content": content, "tool_calls": None}}]}
    resp = OpenAICompatibleClient._parse(data)
    assert resp.wants_tools
    assert resp.tool_calls[0].name == "lookup_rule"
    assert "cleric" in resp.tool_calls[0].arguments.get("query", "").lower()


def test_strips_leftover_control_markup():
    data = {"choices": [{"message":
            {"content": "You enter the hall.<｜end▁of▁sentence｜>",
             "tool_calls": None}}]}
    resp = OpenAICompatibleClient._parse(data)
    assert "You enter the hall." in resp.text
    assert "DSML" not in (resp.text or "") and "｜" not in (resp.text or "")


def test_spell_tools_answer_from_engine():
    repo = Repo.memory()
    cid = repo.create_campaign("Greyhawk")
    repo.save_character(cid, {
        "name": "Jodi", "race": "Human",
        "classes": [{"class": "Cleric", "level": 1, "xp": 0}], "alignment": "N",
        "str": 10, "dex": 10, "con": 10, "int": 10, "wis": 18, "cha": 10,
        "hp_max": 8, "ac_descending": 10})
    t = RefereeTools(repo, cid)
    av = t.spells_available("Jodi")
    assert av["caster"] is True
    # Cleric level 1 with WIS 18 -> 1 base + 2 Wisdom bonus = 3 first-level slots.
    assert av["slots_by_spell_level"][1] == 3
    names = t.list_spells("Cleric", 1)["spells"]
    assert names
    res = t.memorize_spell("Jodi", names[0])
    assert names[0] in res["memorized"]


def test_economy_tools_persist():
    repo, cid = _campaign_with_pc()
    t = RefereeTools(repo, cid)
    t.set_gold("Faelith", 100)
    r = t.spend_gold("Faelith", 75)
    assert r["gold"] == 25
    assert "error" in t.spend_gold("Faelith", 999)        # can't overspend
    t.add_gear("Faelith", "chain mail")
    assert "chain mail" in t.get_character("Faelith")["gear"]


def test_spawn_monster_and_fight():
    repo, cid = _campaign_with_pc()
    t = RefereeTools(repo, cid)
    # The DM looks up and spawns three goblins.
    info = t.get_monster("Goblin")
    assert info["ac"] == 6 and "d" in info["primary_damage"]
    res = t.spawn_monster("Goblin", label="Goblin Sentry", count=3)
    assert len(res["spawned"]) == 3
    names = [s["name"] for s in res["spawned"]]
    assert names == ["Goblin Sentry 1", "Goblin Sentry 2", "Goblin Sentry 3"]
    # The spawned goblin is a real, fightable NPC with the monster's damage.
    t.start_combat(combatants=[{"name": "Faelith", "side": "party"},
                               {"name": "Goblin Sentry 1", "side": "foes"}])
    atk = t.attack("Faelith", "Goblin Sentry 1")
    assert "hit" in atk and atk["target_ac"] == 6
    # It shows up in the roster as an NPC.
    chars = t.list_characters()["characters"]
    assert any(c["name"] == "Goblin Sentry 1" and c["is_npc"] for c in chars)


def test_generate_treasure_tool():
    repo, cid = _campaign_with_pc()
    t = RefereeTools(repo, cid)
    out = t.generate_treasure("Hoard 3, Cache 4")
    assert out["loot_classes"] == ["Hoard 3", "Cache 4"]
    assert "coins" in out and "gems" in out and "total_value_gp" in out
    assert out["total_value_gp"] >= 0


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("All referee tests passed.")
