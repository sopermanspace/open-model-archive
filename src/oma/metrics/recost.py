import json
from pathlib import Path

from oma.metrics.cost import estimate_from_model
from oma.models.run import CostBreakdown, RunRecord
from oma.paths import RUNS_DIR
from oma.registry.models import load_model


def recost_run(run_json_path: Path) -> RunRecord:
    record = RunRecord.model_validate(json.loads(run_json_path.read_text(encoding="utf-8")))
    model_config = load_model(record.model.id)

    breakdown = estimate_from_model(
        model_config,
        input_tokens=record.tokens.input,
        output_tokens=record.tokens.output,
        reasoning_tokens=record.tokens.reasoning,
    )

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