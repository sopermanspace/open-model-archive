from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    id: str
    display_name: str
    provider: str
    adapter: str
    model_ref: str = ""
    cli_model: str = ""
    api_model: str = ""
    api_key_env: str = ""
    api_base: str = ""
    cost_per_1k_input: float | None = None
    cost_per_1k_output: float | None = None
    cost_per_1k_reasoning: float | None = None
    pricing_source: str = ""
    cost_estimate: bool = True
    notes: str = ""
    enabled: bool = True
    timeout_seconds: int = Field(default=600, ge=30)