import typer
from rich.console import Console

from oma.engine.executor import execute_run
from oma.registry.models import resolve_task_models
from oma.registry.tasks import list_tasks, load_task
from oma.site.generator import generate_site
from oma.metrics.recost import recost_all
from oma.validate import validate_project

app = typer.Typer(
    name="oma",
    help="Open Model Archive — build pipeline for transparent model comparison.",
    no_args_is_help=True,
)
console = Console()


def _execute_runs(
    *,
    task: str | None = None,
    model: str | None = None,
    all_tasks: bool = False,
    no_screenshot: bool = False,
) -> None:
    if all_tasks and not task:
        tasks = list_tasks()
    elif task:
        tasks = [load_task(task)]
    elif all_tasks:
        tasks = list_tasks()
    else:
        raise typer.BadParameter("Specify --task <id> or --all")
    for task_def in tasks:
        models = resolve_task_models(task_def.models)
        if model:
            models = [m for m in models if m.id == model]
            if not models:
                raise typer.BadParameter(f"Model not in task: {model}")

        for model_config in models:
            record = execute_run(
                task_def,
                model_config,
                screenshot=not no_screenshot,
            )
            if record.status == "success":
                console.print(f"[green]✓[/green] {task_def.slug} × {model_config.display_name}")
            else:
                console.print(
                    f"[red]✗[/red] {task_def.slug} × {model_config.display_name}: {record.error}"
                )


@app.command()
def validate() -> None:
    """Validate tasks, prompts, and model configurations."""
    validate_project()
    console.print("[green]Validation passed.[/green]")


@app.command()
def run(
    task: str = typer.Option(None, "--task", "-t", help="Task ID or slug"),
    model: str = typer.Option(None, "--model", "-m", help="Model ID"),
    all_tasks: bool = typer.Option(False, "--all", help="Run all tasks (or all models when combined with --task)"),
    no_screenshot: bool = typer.Option(False, "--no-screenshot", help="Skip screenshots"),
) -> None:
    """Execute tasks against models and store run artifacts."""
    validate_project()
    _execute_runs(
        task=task,
        model=model,
        all_tasks=all_tasks,
        no_screenshot=no_screenshot,
    )


@app.command()
def recost() -> None:
    """Recalculate cost estimates for existing runs from token usage."""
    records = recost_all()
    for record in records:
        cost = f"${record.cost_usd:.4f}" if record.cost_usd is not None else "—"
        console.print(f"[green]✓[/green] {record.task.slug} × {record.model.display_name}: {cost}")
    console.print(f"[green]Updated {len(records)} run(s).[/green]")


@app.command("generate")
def generate() -> None:
    """Generate static site into docs/."""
    generate_site()
    console.print("[green]Site generated in docs/[/green]")


@app.command()
def build(
    skip_run: bool = typer.Option(False, "--skip-run", help="Only regenerate the site"),
    no_screenshot: bool = typer.Option(False, "--no-screenshot", help="Skip screenshots"),
) -> None:
    """Validate, run all tasks, and generate the static site."""
    validate_project()
    if not skip_run:
        _execute_runs(all_tasks=True, no_screenshot=no_screenshot)
    generate()


if __name__ == "__main__":
    app()