import json
import subprocess
import time

from oma.adapters.base import AdapterResult, ModelAdapter
from oma.metrics.cost import estimate_from_model


class AgyAdapter(ModelAdapter):
    """Execute frontier models via the agy CLI (non-interactive print mode)."""

    def execute(self, prompt: str) -> AdapterResult:
        if not self.config.cli_model:
            raise ValueError(f"Model {self.config.id} requires cli_model for agy adapter")

        started = time.perf_counter()
        cmd = [
            "agy",
            "--print",
            "--model",
            self.config.cli_model,
            "--prompt",
            prompt,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.config.timeout_seconds,
            check=False,
        )

        duration_ms = int((time.perf_counter() - started) * 1000)
        if result.returncode != 0:
            stderr = result.stderr.strip() or "agy command failed"
            raise RuntimeError(stderr)

        response = result.stdout.strip()
        metadata: dict = {}
        input_tokens = 0
        output_tokens = 0

        # agy may emit JSON metadata on stderr in some versions
        for line in reversed(result.stderr.splitlines()):
            line = line.strip()
            if line.startswith("{"):
                try:
                    metadata = json.loads(line)
                    usage = metadata.get("usage", {})
                    input_tokens = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
                    output_tokens = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
                    break
                except json.JSONDecodeError:
                    continue

        breakdown = estimate_from_model(
            self.config,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        return AdapterResult(
            response=response,
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_version=self.config.cli_model,
            cost_usd=breakdown.total_usd if breakdown else None,
            cost_breakdown=breakdown.as_dict() if breakdown else None,
            raw_metadata=metadata,
        )