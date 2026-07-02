# Contributing

Thank you for helping build the world's most transparent repository of AI model outputs on identical real-world tasks.

## Ways to contribute

- **Add a task** — new YAML in `tasks/` plus a versioned prompt in `prompts/`
- **Add a model** — copy `models/_template.yaml`, configure an adapter
- **Add a provider adapter** — implement in `src/oma/adapters/`, register in `factory.py`
- **Add topics** — extend `registry/topics.yaml`
- **Improve the site** — templates in `src/oma/site/templates/`, styles in `site/static/css/`
- **Publish runs** — execute tasks locally and commit `runs/` artifacts

## We especially welcome

Contributions from developers using these providers:

| Provider | Adapter | Env variable |
|----------|---------|--------------|
| **Ollama** | `ollama` | (local, no key) |
| **OpenAI** | `openai` | `OPENAI_API_KEY` |
| **Anthropic** | `anthropic` | `ANTHROPIC_API_KEY` |
| **OpenRouter** | `openrouter` | `OPENROUTER_API_KEY` |
| **Together AI** | `together` | `TOGETHER_API_KEY` |
| **Fireworks** | `fireworks` | `FIREWORKS_API_KEY` |
| **Sarvam AI** | `sarvam` | `SARVAM_API_KEY` |
| **Provider CLI** | `cli` | (local CLI auth) |
| **OpenAI (GPT-5.x)** | `openai` | `OPENAI_API_KEY` |

Disabled model templates live in `models/` — enable locally, run tasks, commit results.

## Adding a task

1. Pick topics from `registry/topics.yaml` (or propose new ones)
2. Create `prompts/<category>/<name>/v1.0.0.md` with YAML frontmatter
3. Create `tasks/<category>/<name>.yaml` with `topics`, `prompt`, and optional `inputs`
4. Run `uv run oma run --task <id> --all`
5. Run `uv run oma generate` and commit `runs/` + `docs/`

Prompt versions are immutable. To change a prompt, create `v1.1.0.md`.

## Adding a model

```yaml
id: provider/model-name
display_name: Model Name
provider: Provider Name
adapter: openai  # see table above
api_model: model-id-on-provider
api_key_env: PROVIDER_API_KEY
api_base: https://api.provider.com/v1
cost_per_1k_input: 0.001
cost_per_1k_output: 0.002
pricing_source: "Link or citation for rates"
enabled: false  # enable locally only
```

Never commit secrets, API keys, or `.env` files.

## Adding an API adapter

1. Implement `ModelAdapter` in `src/oma/adapters/`
2. Register the adapter name in `src/oma/adapters/factory.py`
3. Add a disabled template in `models/`
4. Document env vars in `.env.example`
5. Submit a PR with at least one published run (or CI-safe `--skip-run` site build)

## Pull requests

1. `uv run oma validate`
2. `uv run oma build --skip-run` (or full build if you have model access)
3. Describe which tasks/models you ran
4. Include pricing source for new models