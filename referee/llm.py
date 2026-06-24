"""llm.py -- the model-agnostic LLM client (the "AI Pagan" adapter).

One interface, many gods. OpenAICompatibleClient speaks the chat/tool-calling
protocol shared by DeepSeek, Ollama, OpenRouter and OpenAI, so swapping models is
a config change. ScriptedClient returns pre-programmed responses for offline
tests -- which lets the whole referee turn loop be tested with no key or network.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .config import ModelConfig, get_config

# DeepSeek (and some others) sometimes emit a tool call as TEXT in a private
# markup instead of the structured tool_calls field. We salvage it.
_INVOKE = re.compile(r'invoke name="([^"]+)"(.*?)(?:</[^>]*invoke>|\Z)', re.S)
_PARAM = re.compile(r'parameter name="([^"]+)"[^>]*>(.*?)(?:</[^>]*parameter>|\Z)', re.S)
_CONTROL = re.compile(r'<[^>]*(?:DSML|tool_calls|begin\W*of|end\W*of)[^>]*>', re.I)


def _salvage_tool_calls(content: str) -> List["ToolCall"]:
    out: List[ToolCall] = []
    for i, m in enumerate(_INVOKE.finditer(content or "")):
        name = m.group(1).strip()
        args: Dict[str, Any] = {}
        for p in _PARAM.finditer(m.group(2) or ""):
            args[p.group(1).strip()] = p.group(2).strip().strip('"').strip()
        out.append(ToolCall(id="salv{}".format(i), name=name, arguments=args))
    return out


def _strip_control(text: str) -> str:
    return _CONTROL.sub("", text or "").strip()


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    text: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


class LLMClient(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict[str, Any]],
             tools: Optional[List[Dict[str, Any]]] = None) -> LLMResponse:
        ...


class OpenAICompatibleClient(LLMClient):
    """Works against any OpenAI-compatible /chat/completions endpoint."""

    def __init__(self, config: Optional[ModelConfig] = None, timeout: int = 90):
        self.config = config or get_config("deepseek")
        self.timeout = timeout

    def chat(self, messages, tools=None) -> LLMResponse:
        key = self.config.api_key
        if not key and self.config.provider != "ollama":
            raise RuntimeError(
                "No API key in ${} -- set it to use the {} provider.".format(
                    self.config.api_key_env, self.config.provider))
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        req = urllib.request.Request(
            self.config.base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer {}".format(key or "ollama")},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")[:300]
            except Exception:
                pass
            hint = ""
            if e.code in (401, 403):
                hint = (" -- the key in ${} was rejected. Check it's valid, has "
                        "credit, and is set in the shell that runs the server."
                        .format(self.config.api_key_env))
            raise RuntimeError("{} API HTTP {}{} {}".format(
                self.config.provider, e.code, hint, body))
        except urllib.error.URLError as e:
            raise RuntimeError("{} API unreachable: {}".format(
                self.config.provider, e.reason))
        return self._parse(data)

    @staticmethod
    def _parse(data: Dict[str, Any]) -> LLMResponse:
        msg = data["choices"][0]["message"]
        calls = []
        for tc in (msg.get("tool_calls") or []):
            fn = tc.get("function", {})
            args = fn.get("arguments") or "{}"
            try:
                args = json.loads(args) if isinstance(args, str) else args
            except json.JSONDecodeError:
                args = {}
            calls.append(ToolCall(id=tc.get("id", ""), name=fn.get("name", ""),
                                  arguments=args))
        content = msg.get("content")
        # Salvage tool calls the model leaked into text (DeepSeek markup), and
        # never let that control markup reach the players.
        if not calls and content and "invoke name=" in content:
            salvaged = _salvage_tool_calls(content)
            if salvaged:
                return LLMResponse(text=None, tool_calls=salvaged)
        if content:
            content = _strip_control(content)
        return LLMResponse(text=content, tool_calls=calls)


class ScriptedClient(LLMClient):
    """Returns a fixed sequence of LLMResponses -- for tests and demos."""

    def __init__(self, steps: List[LLMResponse]):
        self.steps = list(steps)
        self.calls: List[Dict[str, Any]] = []

    def chat(self, messages, tools=None) -> LLMResponse:
        self.calls.append({"messages": messages, "tools": tools})
        if not self.steps:
            return LLMResponse(text="(the referee falls silent)")
        return self.steps.pop(0)


class NoKeyClient(LLMClient):
    """Stands in when no key is configured: explains how to go live."""

    def chat(self, messages, tools=None) -> LLMResponse:
        return LLMResponse(text=(
            "[The referee is offline. Set DEEPSEEK_API_KEY (or another provider's "
            "key) to wake the Dungeon Master. The map, sheets, dice and rules "
            "lookup all work without it.]"))


def make_client(provider: str = "deepseek") -> LLMClient:
    return OpenAICompatibleClient(get_config(provider))
