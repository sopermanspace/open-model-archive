from oma.adapters.agy import CliAdapter
from oma.adapters.anthropic import AnthropicAdapter
from oma.adapters.base import ModelAdapter
from oma.adapters.ollama import OllamaAdapter
from oma.adapters.openai_compatible import OpenAICompatibleAdapter
from oma.models.model_config import ModelConfig

_OPENAI_COMPATIBLE = {
    "openai",
    "openrouter",
    "together",
    "fireworks",
    "sarvam",
    "codex",
}


def create_adapter(config: ModelConfig) -> ModelAdapter:
    adapter = config.adapter.lower()
    if adapter == "ollama":
        return OllamaAdapter(config)
    if adapter in {"agy", "cli", "claude", "grok"}:
        return CliAdapter(config)
    if adapter == "anthropic":
        return AnthropicAdapter(config)
    if adapter in _OPENAI_COMPATIBLE:
        return OpenAICompatibleAdapter(config)
    raise ValueError(f"Unknown adapter type: {config.adapter}")