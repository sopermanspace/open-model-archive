import base64
import os
import time
from pathlib import Path

import httpx

from oma.adapters.base import AdapterResult, ModelAdapter
from oma.metrics.cost import estimate_from_model


class AnthropicAdapter(ModelAdapter):
    """Anthropic Messages API (Claude)."""

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

        content = _build_content(prompt, images)
        started = time.perf_counter()

        payload = {
            "model": self.config.api_model,
            "max_tokens": 8192,
            "messages": [{"role": "user", "content": content}],
        }

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        base_url = (self.config.api_base or "https://api.anthropic.com").rstrip("/")
        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            response = client.post(f"{base_url}/v1/messages", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        duration_ms = int((time.perf_counter() - started) * 1000)
        text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        text = "\n".join(text_blocks)
        usage = data.get("usage", {})
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)

        breakdown = estimate_from_model(
            self.config,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return AdapterResult(
            response=text,
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

    parts: list[dict] = []
    for image in images:
        encoded = base64.b64encode(image.read_bytes()).decode("ascii")
        mime = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }.get(image.suffix.lower(), "image/png")
        parts.append(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": mime, "data": encoded},
            }
        )
    parts.append({"type": "text", "text": prompt})
    return parts