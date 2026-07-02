import base64
import os
import time
from pathlib import Path

import httpx

from oma.adapters.base import AdapterResult, ModelAdapter
from oma.metrics.cost import estimate_from_model
from oma.models.model_config import ModelConfig


class OpenAICompatibleAdapter(ModelAdapter):
    """OpenAI-compatible chat API (OpenAI, OpenRouter, Together, Fireworks, Sarvam, etc.)."""

    def execute(self, prompt: str, *, images: list[Path] | None = None) -> AdapterResult:
        if not self.config.api_key_env:
            raise ValueError(f"Model {self.config.id} requires api_key_env")
        if not self.config.api_model:
            raise ValueError(f"Model {self.config.id} requires api_model")

        api_key = os.environ.get(self.config.api_key_env, "").strip()
        if not api_key:
            raise RuntimeError(
                f"Missing API key. Set {self.config.api_key_env} in your environment."
            )

        base_url = (self.config.api_base or "https://api.openai.com/v1").rstrip("/")
        content = _build_content(prompt, images)

        started = time.perf_counter()
        payload = {
            "model": self.config.api_model,
            "messages": [{"role": "user", "content": content}],
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if "openrouter.ai" in base_url:
            headers["HTTP-Referer"] = "https://github.com/sopermanspace/open-model-archive"
            headers["X-Title"] = "Open Model Archive"

        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            response = client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        duration_ms = int((time.perf_counter() - started) * 1000)
        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        input_tokens = int(usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or 0)

        breakdown = estimate_from_model(
            self.config,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return AdapterResult(
            response=choice,
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_version=data.get("model") or self.config.api_model,
            cost_usd=breakdown.total_usd if breakdown else None,
            cost_breakdown=breakdown.as_dict() if breakdown else None,
            raw_metadata={"provider_response_id": data.get("id")},
        )


def _build_content(prompt: str, images: list[Path] | None) -> str | list[dict]:
    if not images:
        return prompt

    parts: list[dict] = [{"type": "text", "text": prompt}]
    for image in images:
        encoded = base64.b64encode(image.read_bytes()).decode("ascii")
        mime = _mime_type(image)
        parts.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{encoded}"},
            }
        )
    return parts


def _mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(suffix, "image/png")