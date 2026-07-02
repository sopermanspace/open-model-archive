# Contributing

Thank you for helping build the world's most transparent repository of AI model outputs on real-world tasks.

**You do not need our models.** Publish runs from whatever you have access to — any Ollama tag, any API key, any CLI-backed frontier model.

## Ways to contribute

- **Publish model runs** — enable a model you can access, execute tasks, commit `runs/`
- **Add a model** — copy `models/_template.yaml`, configure an adapter, set pricing
- **Add a task** — new YAML in `tasks/` plus a versioned prompt in `prompts/`
- **Add a provider adapter** — implement in `src/oma/adapters/`, register in `factory.py`
- **Add topics** — extend `registry/topics.yaml`
- **Improve the site** — templates in `src/oma/site/templates/`, styles in `site/static/css/`

## Supported adapters

Every adapter below is implemented and ready to use. Copy a template, set `enabled: true` locally, authenticate, run, commit.

| Adapter | Provider / scope | Auth | Example templates in `models/` |
| :--- | :--- | :--- | :--- |
| `ollama` | Any Ollama model (local or cloud) | Ollama daemon | `ollama-gemma4.yaml`, `ollama-kimi-k2.7-code.yaml` |
| `cli` | Any model behind a provider CLI | Local CLI session | `google-gemini-3.1-pro.yaml` |
| `openai` | OpenAI APIs | `OPENAI_API_KEY` | `openai-gpt-5.5.yaml`, `openai-gpt-5.4.yaml`, `openai-gpt-5.5-instant.yaml` |
| `anthropic` | Anthropic Messages API | `ANTHROPIC_API_KEY` | `anthropic-claude-sonnet-5.yaml`, `anthropic-claude-fable-5.yaml`, `anthropic-claude-mythos-5.yaml` |
| `openrouter` | Any model on OpenRouter | `OPENROUTER_API_KEY` | `openrouter-llama.yaml` |
| `together` | Together AI | `TOGETHER_API_KEY` | `together-llama.yaml` |
| `fireworks` | Fireworks AI | `FIREWORKS_API_KEY` | `fireworks-llama.yaml` |
| `sarvam` | Sarvam AI | `SARVAM_API_KEY` | `sarvam-m.yaml` |
| `codex` | OpenAI Codex-compatible endpoints | `OPENAI_API_KEY` | Add your own YAML |

See `.env.example` for environment variable names. **Never commit secrets, API keys, or `.env` files.**

## Adding a model (3 steps)

1. Copy `models/_template.yaml` → `models/your-model.yaml`
2. Fill in `adapter`, model reference (`model_ref`, `api_model`, or `cli_model`), and pricing
3. Set `enabled: true` locally, export your key, run tasks, commit `runs/`

```yaml
id: provider/model-name
display_name: Model Name
provider: Provider Name
adapter: openai          # see table above
api_model: gpt-5.5       # provider's model ID
api_key_env: OPENAI_API_KEY
api_base: https://api.openai.com/v1
cost_per_1k_input: 0.001
cost_per_1k_output: 0.002
pricing_source: "Link or citation for rates"
enabled: false           # true locally only
```

For Ollama, use `adapter: ollama` and `model_ref: your-tag:latest` instead of `api_model`.

## Adding a task

1. Pick topics from `registry/topics.yaml` (or propose new ones)
2. Create `prompts/<category>/<name>/v1.0.0.md` with YAML frontmatter
3. Create `tasks/<category>/<name>.yaml` with `topics`, `prompt`, and optional `inputs`
4. Run `uv run oma run --task <id> --model <your-model-id>`
5. Run `uv run oma generate` and commit `runs/` + `docs/`

Prompt versions are immutable. To change a prompt, create `v1.1.0.md`.

## Adding an API adapter

1. Implement `ModelAdapter` in `src/oma/adapters/`
2. Register the adapter name in `src/oma/adapters/factory.py`
3. Add a disabled template in `models/`
4. Document env vars in `.env.example`
5. Submit a PR with at least one published run (or a `--skip-run` site build if CI-safe)

## Pull requests

1. `uv run oma validate`
2. `uv run oma build --skip-run` (or full build if you have model access)
3. Describe which tasks and models you ran
4. Include `pricing_source` for new models