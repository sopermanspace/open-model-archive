from datetime import UTC, datetime

from oma.adapters.base import AdapterResult
from oma.models.prompt import Prompt
from oma.models.run import ModelRef, PromptRef, RunRecord, TaskRef, TokenUsage
from oma.models.task import TaskDefinition
from oma.models.model_config import ModelConfig


def build_run_record(
    *,
    task: TaskDefinition,
    model_config: ModelConfig,
    prompt: Prompt,
    result: AdapterResult,
    status: str,
    error: str | None = None,
) -> RunRecord:
    safe_model = model_config.id.replace("/", "-")
    run_id = f"{task.slug}/{safe_model}/{datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}"

    return RunRecord(
        id=run_id,
        task=TaskRef(
            id=task.id,
            slug=task.slug,
            category=task.category,
            title=task.title,
            prompt_version=prompt.meta.version,
        ),
        model=ModelRef(
            id=model_config.id,
            display_name=model_config.display_name,
            provider=model_config.provider,
            version=result.model_version or model_config.model_ref or model_config.cli_model,
        ),
        prompt=PromptRef(
            id=prompt.meta.id,
            version=prompt.meta.version,
            sha256=prompt.sha256,
            title=prompt.meta.title,
        ),
        executed_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        duration_ms=result.duration_ms,
        tokens=TokenUsage(
            input=result.input_tokens,
            output=result.output_tokens,
            reasoning=result.reasoning_tokens,
        ),
        cost_usd=result.cost_usd,
        status=status,  # type: ignore[arg-type]
        error=error,
    )