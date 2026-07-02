import json
from pathlib import Path

from oma.metrics.cost import estimate_from_model
from oma.models.run import CostBreakdown, RunRecord
from oma.paths import RUNS_DIR
from oma.registry.models import load_model


def recost_run(run_json_path: Path) -> RunRecord:
    record = RunRecord.model_validate(json.loads(run_json_path.read_text(encoding="utf-8")))
    model_config = load_model(record.model.id)

    input_tokens = record.tokens.input
    output_tokens = record.tokens.output
    if input_tokens == 0 and output_tokens == 0:
        output_path = run_json_path.parent / "output.txt"
        if output_path.exists():
            output_text = output_path.read_text(encoding="utf-8")
            output_tokens = max(1, len(output_text) // 4)
            input_tokens = max(1, 256)

    breakdown = estimate_from_model(
        model_config,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=record.tokens.reasoning,
    )

    if input_tokens != record.tokens.input or output_tokens != record.tokens.output:
        record.tokens.input = input_tokens
        record.tokens.output = output_tokens

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