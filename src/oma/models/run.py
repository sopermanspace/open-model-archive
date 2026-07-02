from typing import Literal

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    input: int = 0
    output: int = 0
    reasoning: int = 0
    source: str = "provider"  # provider | estimated


class CostBreakdown(BaseModel):
    total_usd: float
    input_usd: float
    output_usd: float
    reasoning_usd: float = 0.0
    estimated: bool = True
    pricing_source: str = ""


class TaskRef(BaseModel):
    id: str
    slug: str
    category: str
    title: str
    prompt_version: str


class ModelRef(BaseModel):
    id: str
    display_name: str
    provider: str
    version: str


class PromptRef(BaseModel):
    id: str
    version: str
    sha256: str
    title: str = ""


class Artifact(BaseModel):
    type: str
    path: str
    sha256: str
    language: str | None = None


class Screenshot(BaseModel):
    path: str
    viewport: str
    sha256: str = ""


class RunRecord(BaseModel):
    id: str
    task: TaskRef
    model: ModelRef
    prompt: PromptRef
    executed_at: str
    duration_ms: int
    tokens: TokenUsage
    cost_usd: float | None = None
    cost: CostBreakdown | None = None
    status: Literal["success", "error", "timeout"]
    error: str | None = None
    artifacts: list[Artifact] = Field(default_factory=list)
    screenshots: list[Screenshot] = Field(default_factory=list)
    logs: str = "run.log"