import json
import re
import shutil
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from oma.models.run import RunRecord
from oma.models.task import TaskDefinition
from oma.paths import DOCS_DIR, ROOT, RUNS_DIR, SITE_STATIC
from oma.registry.prompts import load_prompt
from oma.registry.tasks import list_tasks
from oma.registry.site import load_site_config
from oma.registry.topics import list_topics, topics_by_id
from oma.storage.artifacts import copy_runs_to_docs


def _load_run(path: Path) -> RunRecord:
    return RunRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _extract_fenced_code(text: str, language: str = "python") -> str:
    pattern = rf"```{re.escape(language)}\s*\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"```[^\n]*\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _render_markdown(text: str) -> str:
    if not text.strip():
        return ""
    return markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "sane_lists"],
    )


def _load_source_content(
    run_dir: Path,
    artifact_path: str,
    raw_output: str,
    language: str | None,
) -> str:
    source_path = run_dir / artifact_path
    if source_path.exists():
        return source_path.read_text(encoding="utf-8")

    lang = language or "python"
    extracted = _extract_fenced_code(raw_output, lang)
    if extracted:
        return extracted

    # Last resort: show raw output stripped of fences
    return raw_output.strip()


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


def _format_tokens(count: int, estimated: bool = False) -> str:
    prefix = "~" if estimated else ""
    if count >= 1000:
        return f"{prefix}{count / 1000:.1f}k"
    return f"{prefix}{count}"


def _format_cost(cost: float | None, estimated: bool = False) -> str:
    if cost is None:
        return "—"
    prefix = "~" if estimated else ""
    if cost == 0:
        return f"{prefix}$0.00"
    if cost < 0.01:
        return f"{prefix}${cost:.4f}"
    return f"{prefix}${cost:.2f}"


def generate_site() -> None:
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir(parents=True)

    assets_dir = DOCS_DIR / "assets"
    assets_dir.mkdir()
    shutil.copytree(SITE_STATIC, assets_dir, dirs_exist_ok=True)
    favicon = SITE_STATIC / "favicon.svg"
    if favicon.exists():
        shutil.copy2(favicon, assets_dir / "favicon.svg")

    copy_runs_to_docs()

    env = _env()
    env.filters["duration"] = _format_duration
    env.filters["tokens"] = _format_tokens
    env.filters["cost"] = _format_cost

    site = load_site_config()
    site_root = site.base_path.rstrip("/")

    tasks = list_tasks()
    runs_by_task = collect_runs()
    topic_catalog = topics_by_id()
    topic_labels = {tid: topic_catalog[tid].title for tid in topic_catalog}

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

    categories: list[str] = []
    topic_counts: dict[str, int] = {}
    for entry in index_runs:
        cat = entry["task"].category
        if cat not in categories:
            categories.append(cat)
        for topic_id in entry["task"].topics:
            topic_counts[topic_id] = topic_counts.get(topic_id, 0) + 1

    index_html = env.get_template("index.html").render(
        site_name="Open Model Archive",
        site=site,
        site_root=site_root,
        canonical_url=site.canonical_url,
        tasks=index_runs,
        categories=categories,
        topic_list=list_topics(),
        topic_counts=topic_counts,
        topic_labels=topic_labels,
    )
    (DOCS_DIR / "index.html").write_text(index_html, encoding="utf-8")

    about_html = env.get_template("about.html").render(
        site_name="Open Model Archive",
        site=site,
        site_root=site_root,
        canonical_url=site.canonical_url,
    )
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

        render_as_markdown = task.category == "blog-writing"
        run_outputs: dict[str, str] = {}
        run_rendered: dict[str, str] = {}
        run_sources: dict[str, dict[str, str]] = {}
        for run in task_runs:
            safe_model = run.model.id.replace("/", "-")
            run_dir = RUNS_DIR / task.slug / safe_model
            output_path = run_dir / "output.txt"
            run_outputs[run.id] = (
                output_path.read_text(encoding="utf-8") if output_path.exists() else ""
            )
            raw_output = run_outputs[run.id]
            if render_as_markdown:
                run_rendered[run.id] = _render_markdown(raw_output)
            sources: dict[str, str] = {}
            for artifact in run.artifacts:
                if artifact.type == "source":
                    content = _load_source_content(
                        run_dir,
                        artifact.path,
                        raw_output,
                        artifact.language,
                    )
                    if content:
                        sources[artifact.path] = content
            run_sources[run.id] = sources

        page = env.get_template("comparison.html").render(
            site_name="Open Model Archive",
            site=site,
            site_root=site_root,
            canonical_url=site.canonical_url,
            task=task,
            runs=task_runs,
            prompt_body=prompt_body,
            run_outputs=run_outputs,
            run_rendered=run_rendered,
            render_as_markdown=render_as_markdown,
            run_sources=run_sources,
            topic_labels=topic_labels,
        )
        out_dir = DOCS_DIR / "tasks" / task.slug
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(page, encoding="utf-8")