import json
import subprocess
import time
from pathlib import Path

from oma.adapters.base import AdapterResult, ModelAdapter
from oma.metrics.cost import estimate_from_model
from oma.metrics.tokens import count_prompt_and_output


class CliAdapter(ModelAdapter):
    """Execute frontier models via provider CLIs in non-interactive print mode."""

    def _resolve_binary(self) -> str:
        if self.config.cli_binary:
            return self.config.cli_binary.lower()
        adapter = self.config.adapter.lower()
        if adapter in {"claude", "grok"}:
            return adapter
        return "agy"

    def _build_command(self, full_prompt: str, add_dirs: set[Path]) -> list[str]:
        binary = self._resolve_binary()

        if binary == "claude":
            cmd = ["claude", "-p", full_prompt, "--model", self.config.cli_model]
            for directory in sorted(add_dirs):
                cmd.extend(["--add-dir", str(directory)])
            return cmd

        if binary == "grok":
            return [
                "grok",
                "-p",
                full_prompt,
                "-m",
                self.config.cli_model,
                "--output-format",
                "plain",
                "--permission-mode",
                "bypassPermissions",
            ]

        cmd = ["agy", "-p", full_prompt, "--model", self.config.cli_model]
        for directory in sorted(add_dirs):
            cmd.extend(["--add-dir", str(directory)])
        return cmd

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

        cmd = self._build_command(full_prompt, add_dirs)

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

        tokens_source = "provider"
        if input_tokens == 0 and output_tokens == 0 and response:
            input_tokens, output_tokens = count_prompt_and_output(
                prompt=full_prompt,
                output=response,
            )
            tokens_source = "estimated"

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
            tokens_source=tokens_source,
            model_version=self.config.cli_model,
            cost_usd=breakdown.total_usd if breakdown else None,
            cost_breakdown=breakdown.as_dict() if breakdown else None,
            raw_metadata=metadata,
        )


# Backwards-compatible alias
AgyAdapter = CliAdapter