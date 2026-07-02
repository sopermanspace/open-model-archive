from dataclasses import dataclass, field

from oma.models.model_config import ModelConfig


@dataclass
class AdapterResult:
    response: str
    duration_ms: int
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    model_version: str = ""
    cost_usd: float | None = None
    raw_metadata: dict = field(default_factory=dict)


class ModelAdapter:
    """Base adapter for executing prompts against a model provider."""

    def __init__(self, config: ModelConfig):
        self.config = config

    def execute(self, prompt: str) -> AdapterResult:
        raise NotImplementedError