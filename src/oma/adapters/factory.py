from oma.adapters.agy import CliAdapter
from oma.adapters.base import ModelAdapter
from oma.adapters.ollama import OllamaAdapter
from oma.models.model_config import ModelConfig


def create_adapter(config: ModelConfig) -> ModelAdapter:
    adapter = config.adapter.lower()
    if adapter == "ollama":
        return OllamaAdapter(config)
    if adapter in {"agy", "cli"}:
        return CliAdapter(config)
    raise ValueError(f"Unknown adapter type: {config.adapter}")