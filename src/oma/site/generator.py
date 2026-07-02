import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from oma.models.run import RunRecord
from oma.models.task import TaskDefinition
from oma.paths import DOCS_DIR, ROOT, RUNS_DIR, SITE_STATIC
from oma.registry.prompts import load_prompt
from oma.registry.tasks import list_tasks
from oma.storage.artifacts import copy_runs_to_docs


def _load_run(path: Path) -> RunRecord:
    return RunRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))


def collect_runs() -> dict[str, list[RunRecord]]:
    grouped: dict[str, list[RunRecord]] = {}
    if not RUNS_DIR.exists():
        return grouped

    for run_json in RUNS_DIR.rglob("run.json"):
        record = _load_run(run_json)
        grouped.setdefault(record.task.slug, []).append(record)
    return grouped


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(ROOT / "src" / "oma" / "site" / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )


def _format_duration(ms: int) -> str:
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms / 1000:.1f}s"


def _format_tokens(count: int) -> str:
    if count >= 1000:
        return f"{count / 1000:.1f}k"
    return str(count)


def _format_cost(cost: float | None) -> str:
    if cost is None:
        return "—"
    if cost == 0:
        return "$0.00"
    return f"${cost:.4f}"


def generate_site() -> None:
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir(parents=True)

    assets_dir = DOCS_DIR / "assets"
    assets_dir.mkdir()
    shutil.copytree(SITE_STATIC, assets_dir, dirs_exist_ok=True)

    copy_runs_to_docs()

    env = _env()
    env.filters["duration"] = _format_duration
    env.filters["tokens"] = _format_tokens
    env.filters["cost"] = _format_cost

    tasks = list_tasks()
    runs_by_task = collect_runs()

    # Index page
    index_runs: list[dict] = []
    for task in tasks:
        task_runs = runs_by_task.get(task.slug, [])
        success = [r for r in task_runs if r.status == "success"]
        index_runs.append(
            {
                "task": task,
                "model_count": len(success),
                "models": [r.model.display_name for r in success],
            }
        )

    index_html = env.get_template("index.html").render(
        site_name="Open Model Archive",
        tagline="Transparent AI model outputs for identical real-world tasks.",
        tasks=index_runs,
    )
    (DOCS_DIR / "index.html").write_text(index_html, encoding="utf-8")

    about_html = env.get_template("about.html").render(site_name="Open Model Archive")
    about_dir = DOCS_DIR / "about"
    about_dir.mkdir()
    (about_dir / "index.html").write_text(about_html, encoding="utf-8")

    # Comparison pages
    for task in tasks:
        task_runs = sorted(
            runs_by_task.get(task.slug, []),
            key=lambda r: r.model.display_name,
        )
        prompt_body = ""
        if task_runs:
            try:
                prompt_body = load_prompt(task.prompt).full_text
            except Exception:
                prompt_body = ""

        page = env.get_template("comparison.html").render(
            site_name="Open Model Archive",
            task=task,
            runs=task_runs,
            prompt_body=prompt_body,
        )
        out_dir = DOCS_DIR / "tasks" / task.slug
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(page, encoding="utf-8")