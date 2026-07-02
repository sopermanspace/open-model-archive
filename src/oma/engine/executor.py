import json
import subprocess
from pathlib import Path

from rich.console import Console

from oma.adapters.base import AdapterResult
from oma.adapters.factory import create_adapter
from oma.engine.post_processors import attach_screenshot, run_post_processors
from oma.metrics.collector import build_run_record
from oma.models.model_config import ModelConfig
from oma.models.run import RunRecord
from oma.models.task import TaskDefinition
from oma.registry.prompts import load_prompt
from oma.storage.artifacts import run_directory

console = Console()


def _write_log(run_dir: Path, lines: list[str]) -> None:
    (run_dir / "run.log").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _capture_screenshot(html_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["npm", "run", "screenshot", "--", str(html_path), str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Screenshot capture failed")


def execute_run(task: TaskDefinition, model_config: ModelConfig, *, screenshot: bool = True) -> RunRecord:
    prompt = load_prompt(task.prompt)
    run_dir = run_directory(task.slug, model_config.id)
    run_dir.mkdir(parents=True, exist_ok=True)

    logs: list[str] = [
        f"task={task.id}",
        f"model={model_config.id}",
        f"prompt={prompt.ref}",
        f"adapter={model_config.adapter}",
    ]

    adapter = create_adapter(model_config)
    status = "success"
    error: str | None = None
    result = AdapterResult(response="", duration_ms=0)

    try:
        console.print(f"[bold]Running[/bold] {task.slug} × {model_config.display_name}")
        result = adapter.execute(prompt.full_text)
        (run_dir / "output.txt").write_text(result.response, encoding="utf-8")
        logs.append(f"duration_ms={result.duration_ms}")
        logs.append(f"tokens={result.input_tokens}->{result.output_tokens}")

        record = build_run_record(
            task=task,
            model_config=model_config,
            prompt=prompt,
            result=result,
            status="success",
        )

        if task.post_process:
            artifacts = run_post_processors(task.post_process, result.response, run_dir)
            record.artifacts = artifacts

            if screenshot and any(a.type == "html" for a in artifacts):
                html_artifact = next(a for a in artifacts if a.type == "html")
                html_path = run_dir / html_artifact.path
                shot_path = run_dir / "screenshots" / "desktop.png"
                try:
                    _capture_screenshot(html_path, shot_path)
                    record.screenshots.append(
                        attach_screenshot(run_dir, shot_path, "1280x800")
                    )
                    logs.append(f"screenshot={shot_path}")
                except Exception as exc:  # noqa: BLE001 - keep run successful, note screenshot failure
                    logs.append(f"screenshot_error={exc}")

    except Exception as exc:  # noqa: BLE001 - convert to structured run record
        status = "error"
        error = str(exc)
        logs.append(f"error={error}")
        record = build_run_record(
            task=task,
            model_config=model_config,
            prompt=prompt,
            result=AdapterResult(
                response="",
                duration_ms=0,
                model_version=model_config.model_ref or model_config.cli_model,
            ),
            status="error",
            error=error,
        )

    _write_log(run_dir, logs)
    (run_dir / "run.json").write_text(
        json.dumps(record.model_dump(), indent=2) + "\n",
        encoding="utf-8",
    )
    return record