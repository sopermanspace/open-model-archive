from oma.adapters.agy import AgyAdapter
from oma.adapters.base import ModelAdapter
from oma.adapters.ollama import OllamaAdapter
from oma.models.model_config import ModelConfig


def create_adapter(config: ModelConfig) -> ModelAdapter:
    adapter = config.adapter.lower()
    if adapter == "ollama":
        return OllamaAdapter(config)
    if adapter == "agy":
        return AgyAdapter(config)
    raise ValueError(f"Unknown adapter type: {config.adapter}")