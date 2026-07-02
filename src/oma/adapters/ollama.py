import time

import httpx

from oma.adapters.base import AdapterResult, ModelAdapter
from oma.metrics.cost import estimate_from_model
from oma.models.model_config import ModelConfig


class OllamaAdapter(ModelAdapter):
    """Execute models via the local Ollama HTTP API (local and cloud-backed models)."""

    def __init__(self, config: ModelConfig, base_url: str = "http://127.0.0.1:11434"):
        super().__init__(config)
        self.base_url = config.api_base or base_url

    def execute(self, prompt: str) -> AdapterResult:
        started = time.perf_counter()
        payload = {
            "model": self.config.model_ref,
            "prompt": prompt,
            "stream": False,
        }

        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()

        if data.get("error"):
            raise RuntimeError(data["error"])

        duration_ms = int((time.perf_counter() - started) * 1000)
        input_tokens = int(data.get("prompt_eval_count") or 0)
        output_tokens = int(data.get("eval_count") or 0)

        breakdown = estimate_from_model(
            self.config,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return AdapterResult(
            response=data.get("response", ""),
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_version=data.get("model") or self.config.model_ref,
            cost_usd=breakdown.total_usd if breakdown else None,
            cost_breakdown=breakdown.as_dict() if breakdown else None,
            raw_metadata={
                "total_duration_ns": data.get("total_duration"),
                "eval_duration_ns": data.get("eval_duration"),
                "done_reason": data.get("done_reason"),
            },
        )