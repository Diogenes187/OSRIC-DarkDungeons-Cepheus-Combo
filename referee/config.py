"""config.py -- model configuration for the model-agnostic referee.

DeepSeek is the default (cheap, strong DM prose), but any OpenAI-compatible
endpoint works by swapping the provider. Keys come from environment variables;
nothing secret is stored here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ModelConfig:
    provider: str
    model: str
    base_url: str
    api_key_env: str
    temperature: float = 0.85
    max_tokens: int = 1500

    @property
    def api_key(self) -> str:
        return os.environ.get(self.api_key_env, "")


_CONFIGS = {
    "deepseek": ModelConfig("deepseek", "deepseek-chat",
                            "https://api.deepseek.com", "DEEPSEEK_API_KEY"),
    "openai": ModelConfig("openai", "gpt-4o-mini",
                          "https://api.openai.com/v1", "OPENAI_API_KEY"),
    "openrouter": ModelConfig("openrouter", "deepseek/deepseek-chat",
                              "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "ollama": ModelConfig("ollama", "llama3.1",
                          "http://localhost:11434/v1", "OLLAMA_API_KEY"),
}


def get_config(provider: str = "deepseek") -> ModelConfig:
    return _CONFIGS.get(provider, _CONFIGS["deepseek"])
