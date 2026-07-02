import json
import shutil
import subprocess
from pathlib import Path

from rich.console import Console

from oma.adapters.base import AdapterResult
from oma.adapters.factory import create_adapter
from oma.engine.post_processors import attach_screenshot, run_post_processors
from oma.metrics.collector import build_run_record
from oma.models.model_config import ModelConfig
from oma.models.run import Artifact, RunRecord
from oma.models.task import TaskDefinition
from oma.paths import ROOT
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


def _resolve_inputs(task: TaskDefinition, run_dir: Path) -> list[Path]:
    if not task.inputs:
        return []

    inputs_dir = run_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    resolved: list[Path] = []

    for rel_path in task.inputs:
        source = ROOT / rel_path
        if not source.exists():
            raise FileNotFoundError(f"Task input not found: {source}")
        dest = inputs_dir / source.name
        if not dest.exists():
            shutil.copy2(source, dest)
        resolved.append(dest)

    return resolved


def _input_artifacts(inputs: list[Path], run_dir: Path) -> list[Artifact]:
    import hashlib

    artifacts: list[Artifact] = []
    for path in inputs:
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        rel = path.relative_to(run_dir)
        suffix = path.suffix.lower()
        file_type = "image" if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif"} else "input"
        artifacts.append(Artifact(type=file_type, path=str(rel), sha256=sha, language=None))
    return artifacts


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
    error: str | None = None
    result = AdapterResult(response="", duration_ms=0)

    try:
        console.print(f"[bold]Running[/bold] {task.slug} × {model_config.display_name}")
        images = _resolve_inputs(task, run_dir)
        if images:
            logs.append(f"inputs={[str(p.name) for p in images]}")

        result = adapter.execute(prompt.full_text, images=images or None)
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

        if images:
            record.artifacts.extend(_input_artifacts(images, run_dir))

        if task.post_process:
            generated = run_post_processors(task.post_process, result.response, run_dir)
            record.artifacts.extend(generated)

            should_screenshot = screenshot and task.screenshot
            if should_screenshot and any(a.type == "html" for a in generated):
                html_artifact = next(a for a in generated if a.type == "html")
                html_path = run_dir / html_artifact.path
                shot_path = run_dir / "screenshots" / "desktop.png"
                try:
                    _capture_screenshot(html_path, shot_path)
                    record.screenshots.append(
                        attach_screenshot(run_dir, shot_path, "1280x800")
                    )
                    logs.append(f"screenshot={shot_path}")
                except Exception as exc:  # noqa: BLE001
                    logs.append(f"screenshot_error={exc}")

    except Exception as exc:  # noqa: BLE001
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