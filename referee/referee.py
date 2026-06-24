"""referee.py -- the turn loop.

Takes a player's input, rebuilds context from the database, calls the model with
the tool set, executes any tool calls (the deterministic engine doing the actual
work), and loops until the model returns narration. Tool failures degrade
gracefully -- a turn never crashes the table.
"""
from __future__ import annotations

import json
from typing import List, Optional

from . import prompt
from . import tools as tools_mod
from .llm import LLMClient, make_client


class Referee:
    def __init__(self, repo, campaign_id: int, client: Optional[LLMClient] = None,
                 max_tool_iters: int = 12):
        self.repo = repo
        self.cid = campaign_id
        self.client = client or make_client("deepseek")
        self.tools = tools_mod.RefereeTools(repo, campaign_id)
        self.max_tool_iters = max_tool_iters

    def turn(self, player_input: str, speaker: Optional[str] = None) -> str:
        context = prompt.build_context(self.repo, self.cid)
        prefix = "[{}] ".format(speaker) if speaker else ""
        messages: List[dict] = [
            {"role": "system", "content": prompt.SYSTEM_PROMPT},
            {"role": "system", "content": "CURRENT STATE:\n" + context},
        ]
        # Conversation memory: replay the last few turns so the model remembers
        # what just happened. Each model call is otherwise stateless -- without
        # this, a journey narrated last turn is forgotten and the scene snaps
        # back to a default. The state block above is the truth for numbers;
        # this history is the truth for continuity.
        for past in self.repo.recent_turns(self.cid, limit=6):
            if past["player_input"]:
                messages.append({"role": "user", "content": past["player_input"]})
            if past["narration"]:
                messages.append({"role": "assistant", "content": past["narration"]})
        messages.append({"role": "user", "content": prefix + player_input + "\n\n"
                         + prompt.TURN_REMINDER})

        def _done(text: str) -> str:
            try:
                self.repo.log_turn(self.cid, prefix + player_input, text, speaker)
            except Exception:
                pass   # logging must never break a turn
            return text

        specs = tools_mod.specs()
        try:
            for _ in range(self.max_tool_iters):
                resp = self.client.chat(messages, tools=specs)
                if not resp.wants_tools:
                    return _done(resp.text or "(the referee says nothing)")
                messages.append({
                    "role": "assistant",
                    "content": resp.text or None,
                    "tool_calls": [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.name,
                                      "arguments": json.dumps(tc.arguments)}}
                        for tc in resp.tool_calls],
                })
                for tc in resp.tool_calls:
                    result = self.tools.dispatch(tc.name, tc.arguments)
                    messages.append({
                        "role": "tool", "tool_call_id": tc.id, "name": tc.name,
                        "content": json.dumps(result),
                    })
            messages.append({"role": "system", "content":
                             "Stop using tools now and reply to the players in "
                             "prose, using what the tools already returned. "
                             + prompt.TURN_REMINDER})
            resp = self.client.chat(messages, tools=None)
            return _done(resp.text or "(the referee gathers their thoughts)")
        except RuntimeError as e:
            return "[Referee error] {}".format(e)
