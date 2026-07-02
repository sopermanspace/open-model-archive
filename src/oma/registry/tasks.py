from pathlib import Path

import yaml

from oma.models.task import TaskDefinition
from oma.paths import TASKS_DIR


def _load_task_file(path: Path) -> TaskDefinition:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return TaskDefinition.model_validate(data)


def load_task(task_id: str) -> TaskDefinition:
    for path in TASKS_DIR.rglob("*.yaml"):
        task = _load_task_file(path)
        if task.id == task_id or task.slug == task_id:
            return task
    raise FileNotFoundError(f"Task not found: {task_id}")


def list_tasks() -> list[TaskDefinition]:
    tasks: list[TaskDefinition] = []
    for path in sorted(TASKS_DIR.rglob("*.yaml")):
        tasks.append(_load_task_file(path))
    return tasks