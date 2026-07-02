import json
import subprocess
import time
from pathlib import Path

from oma.adapters.base import AdapterResult, ModelAdapter
from oma.metrics.cost import estimate_from_model


class CliAdapter(ModelAdapter):
    """Execute frontier models via a provider CLI in non-interactive print mode."""

    def execute(self, prompt: str, *, images: list[Path] | None = None) -> AdapterResult:
        if not self.config.cli_model:
            raise ValueError(f"Model {self.config.id} requires cli_model for CLI adapter")

        started = time.perf_counter()
        add_dirs: set[Path] = set()
        full_prompt = prompt
        if images:
            for image in images:
                add_dirs.add(image.parent.resolve())
            image_refs = ", ".join(str(p.resolve()) for p in images)
            full_prompt = (
                f"{prompt}\n\n"
                f"Reference image file(s) are available at absolute path(s): {image_refs}\n"
                f"Read and analyze the image(s) as part of your response."
            )

        cmd = ["agy", "-p", full_prompt, "--model", self.config.cli_model]

        for directory in sorted(add_dirs):
            cmd.extend(["--add-dir", str(directory)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.config.timeout_seconds,
            check=False,
        )

        duration_ms = int((time.perf_counter() - started) * 1000)
        if result.returncode != 0:
            stderr = result.stderr.strip() or "CLI execution failed"
            raise RuntimeError(stderr)

        response = result.stdout.strip()
        metadata: dict = {}
        input_tokens = 0
        output_tokens = 0

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

        if input_tokens == 0 and output_tokens == 0 and response:
            input_tokens = max(1, len(full_prompt) // 4)
            output_tokens = max(1, len(response) // 4)

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


# Backwards-compatible alias
AgyAdapter = CliAdapter