import json
from pathlib import Path

from oma.metrics.cost import estimate_from_model
from oma.metrics.tokens import count_prompt_and_output
from oma.models.run import CostBreakdown, RunRecord
from oma.paths import RUNS_DIR
from oma.registry.models import load_model
from oma.registry.prompts import load_prompt
from oma.registry.tasks import load_task


def _resolve_prompt_text(record: RunRecord) -> str:
    try:
        task = load_task(record.task.id)
        return load_prompt(task.prompt).full_text
    except Exception:
        return ""


def recost_run(run_json_path: Path) -> RunRecord:
    record = RunRecord.model_validate(json.loads(run_json_path.read_text(encoding="utf-8")))
    model_config = load_model(record.model.id)

    input_tokens = record.tokens.input
    output_tokens = record.tokens.output
    tokens_source = record.tokens.source

    # CLI models never return provider token counts — always re-estimate from archived text
    cli_adapters = {"cli", "agy", "claude", "grok"}
    needs_estimate = (
        model_config.adapter.lower() in cli_adapters
        or tokens_source == "estimated"
        or (input_tokens == 0 and output_tokens == 0)
    )

    if needs_estimate:
        output_path = run_json_path.parent / "output.txt"
        prompt_text = _resolve_prompt_text(record)
        output_text = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        if prompt_text or output_text:
            input_tokens, output_tokens = count_prompt_and_output(
                prompt=prompt_text,
                output=output_text,
            )
            tokens_source = "estimated"

    breakdown = estimate_from_model(
        model_config,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=record.tokens.reasoning,
    )

    record.tokens.input = input_tokens
    record.tokens.output = output_tokens
    record.tokens.source = tokens_source

    if breakdown:
        record.cost_usd = breakdown.total_usd
        record.cost = CostBreakdown.model_validate(breakdown.as_dict())
    else:
        record.cost_usd = None
        record.cost = None

    run_json_path.write_text(json.dumps(record.model_dump(), indent=2) + "\n", encoding="utf-8")
    return record


def recost_all() -> list[RunRecord]:
    updated: list[RunRecord] = []
    for run_json in sorted(RUNS_DIR.rglob("run.json")):
        updated.append(recost_run(run_json))
    return updated