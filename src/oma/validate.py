from oma.registry.models import list_models
from oma.registry.prompts import list_prompts
from oma.registry.tasks import list_tasks


def validate_project() -> None:
    tasks = list_tasks()
    models = list_models()
    prompts = list_prompts()

    if not tasks:
        raise ValueError("No tasks defined")
    if not models:
        raise ValueError("No models enabled")

    for task in tasks:
        from oma.registry.prompts import load_prompt

        load_prompt(task.prompt)

    print(f"Validated {len(tasks)} task(s), {len(models)} model(s), {len(prompts)} prompt(s).")