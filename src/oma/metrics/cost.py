from dataclasses import dataclass

from oma.models.model_config import ModelConfig


@dataclass
class CostBreakdown:
    total_usd: float
    input_usd: float
    output_usd: float
    reasoning_usd: float
    estimated: bool
    pricing_source: str

    def as_dict(self) -> dict:
        return {
            "total_usd": self.total_usd,
            "input_usd": self.input_usd,
            "output_usd": self.output_usd,
            "reasoning_usd": self.reasoning_usd,
            "estimated": self.estimated,
            "pricing_source": self.pricing_source,
        }


def estimate_cost(
    *,
    input_tokens: int,
    output_tokens: int,
    reasoning_tokens: int = 0,
    cost_per_1k_input: float | None,
    cost_per_1k_output: float | None,
    cost_per_1k_reasoning: float | None = None,
    pricing_source: str = "",
    estimated: bool = True,
) -> CostBreakdown | None:
    """Estimate USD cost from token counts and per-1k rates."""
    if cost_per_1k_input is None and cost_per_1k_output is None:
        return None

    rate_in = cost_per_1k_input or 0.0
    rate_out = cost_per_1k_output or 0.0
    rate_reasoning = cost_per_1k_reasoning if cost_per_1k_reasoning is not None else rate_out

    input_usd = (input_tokens / 1000) * rate_in
    output_usd = (output_tokens / 1000) * rate_out
    reasoning_usd = (reasoning_tokens / 1000) * rate_reasoning
    total = input_usd + output_usd + reasoning_usd

    return CostBreakdown(
        total_usd=round(total, 6),
        input_usd=round(input_usd, 6),
        output_usd=round(output_usd, 6),
        reasoning_usd=round(reasoning_usd, 6),
        estimated=estimated,
        pricing_source=pricing_source,
    )


def estimate_from_model(
    config: ModelConfig,
    *,
    input_tokens: int,
    output_tokens: int,
    reasoning_tokens: int = 0,
) -> CostBreakdown | None:
    if config.cost_per_1k_input is None and config.cost_per_1k_output is None:
        return None

    return estimate_cost(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
        cost_per_1k_input=config.cost_per_1k_input,
        cost_per_1k_output=config.cost_per_1k_output,
        cost_per_1k_reasoning=config.cost_per_1k_reasoning,
        pricing_source=config.pricing_source,
        estimated=config.cost_estimate,
    )