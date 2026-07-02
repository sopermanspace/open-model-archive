# Architecture

Open Model Archive is a data-first static archive. Git stores prompts, runs, and artifacts. The website is generated read-only content.

## Modules

| Module | Path | Role |
|--------|------|------|
| Task Registry | `src/oma/registry/tasks.py` | Loads YAML task definitions |
| Prompt Registry | `src/oma/registry/prompts.py` | Versioned Markdown prompts with frontmatter |
| Model Registry | `src/oma/registry/models.py` | Provider adapter configuration |
| Model Adapters | `src/oma/adapters/` | Execute prompts (Ollama, agy CLI) |
| Execution Engine | `src/oma/engine/executor.py` | Orchestrates runs and post-processing |
| Artifact Storage | `src/oma/storage/` | Persists outputs under `runs/` |
| Metrics Collector | `src/oma/metrics/` | Builds structured `run.json` records |
| Site Generator | `src/oma/site/` | Jinja2 templates → `docs/` |

## Data flow

```
prompts/*.md + tasks/*.yaml + models/*.yaml
        ↓
   oma run / oma build
        ↓
runs/<task>/<model>/run.json + artifacts/
        ↓
   oma generate
        ↓
docs/ (GitHub Pages)
```

## Adding a model

### Ollama (open-source or cloud-backed)

1. Copy `models/_template.yaml`
2. Set `adapter: ollama` and `model_ref` to your Ollama tag
3. Enable the model and add it to a task's `models` list (or use `all`)

### Frontier models via agy CLI

1. Copy `models/_template.yaml`
2. Set `adapter: agy` and `cli_model` to an `agy models` name
3. The adapter captures stdout and archives it

### Direct APIs (future)

Add a new adapter implementing `ModelAdapter.execute()` in `src/oma/adapters/`.

## Run record

Each execution writes `runs/<task-slug>/<model-id>/run.json` with timing, tokens, cost, artifacts, and screenshots. This file is the canonical metadata source for the static site.