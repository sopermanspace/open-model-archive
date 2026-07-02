# Contributing

Thank you for helping build a transparent model archive.

## Ways to contribute

- **Add a task** — new YAML in `tasks/` plus a versioned prompt in `prompts/`
- **Add a model** — copy `models/_template.yaml`, configure the adapter
- **Improve the site** — templates in `src/oma/site/templates/`, styles in `site/static/css/`
- **Fix bugs** — open an issue first for larger changes

## Adding a task

1. Create `prompts/<category>/<name>/v1.0.0.md` with YAML frontmatter
2. Create `tasks/<category>/<name>.yaml` referencing the prompt
3. Run `uv run oma run --task <id> --all`
4. Commit `runs/` and regenerated `docs/`

Prompt versions are immutable. To change a prompt, create `v1.1.0.md`.

## Adding a model

| Provider type | Adapter | Config |
|---------------|---------|--------|
| Ollama local/cloud | `ollama` | `model_ref` |
| agy CLI | `agy` | `cli_model` |

Never commit secrets, API keys, or `.env` files.

## Code style

- Python 3.12+, formatted with ruff
- Keep modules independent — adapters should not import site code
- Prefer declarative YAML over hard-coded task lists

## Pull requests

1. `uv run oma validate`
2. `uv run oma build --skip-run` (or full build if you have model access)
3. Describe which tasks/models you ran