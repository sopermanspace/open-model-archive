import shutil
from pathlib import Path

from oma.paths import DOCS_DIR, RUNS_DIR


def run_directory(task_slug: str, model_id: str) -> Path:
    safe_model = model_id.replace("/", "-")
    return RUNS_DIR / task_slug / safe_model


def copy_runs_to_docs() -> None:
    """Copy run artifacts into docs/runs for GitHub Pages serving."""
    target_root = DOCS_DIR / "runs"
    if target_root.exists():
        shutil.rmtree(target_root)
    if RUNS_DIR.exists():
        shutil.copytree(RUNS_DIR, target_root)