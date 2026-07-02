# Setup Guide

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended)
- Node.js 20+ — **only** if you need Playwright screenshots for HTML tasks

You do **not** need a specific model installed. Use whatever you have access to.

## Install

```bash
git clone https://github.com/sopermanspace/open-model-archive.git
cd open-model-archive

uv sync
```

Optional (screenshots only):

```bash
npm install
npx playwright install chromium
```

## Configure your models

The archive is model-agnostic. Add or enable entries in `models/*.yaml` for whatever you can run.

### Ollama (any local or cloud model)

1. Copy `models/_template.yaml`
2. Set `adapter: ollama` and `model_ref` to your Ollama tag (e.g. `llama3.3:latest`, `qwen2.5-coder:32b`)
3. Set `enabled: true`

Ollama must be running locally. Cloud-backed models require an authenticated Ollama account — no API keys are stored in this repository.

### Provider CLI (any CLI-backed model)

1. Copy `models/_template.yaml`
2. Set `adapter: cli` and `cli_model` to the model name your CLI accepts
3. Install and authenticate the CLI on your machine separately

### API providers

Copy a disabled template from `models/` (e.g. `openai-gpt-5.5.yaml`, `anthropic-claude-sonnet-5.yaml`) or start from `_template.yaml`.

| Adapter | Environment variable |
| :--- | :--- |
| `openai` | `OPENAI_API_KEY` |
| `anthropic` | `ANTHROPIC_API_KEY` |
| `openrouter` | `OPENROUTER_API_KEY` |
| `together` | `TOGETHER_API_KEY` |
| `fireworks` | `FIREWORKS_API_KEY` |
| `sarvam` | `SARVAM_API_KEY` |
| `codex` | `OPENAI_API_KEY` |

```bash
cp .env.example .env
# fill in the keys you use — never commit .env
```

Set `enabled: true` on the models you want to run. Export keys before executing tasks.

## Run the pipeline

```bash
# Validate configuration
uv run oma validate

# Run against your enabled models
uv run oma run --task <slug> --model <model-id>
uv run oma run --all          # all tasks × all enabled models

# Generate static site from committed runs
uv run oma generate

# Full pipeline (validate + run + generate)
uv run oma build
```

To rebuild the site without executing models:

```bash
uv run oma build --skip-run
```

## Preview locally

After `oma generate`:

```bash
python -m http.server 8080 --directory docs
```

Open http://localhost:8080/open-model-archive/

## Browse without running anything

The live archive at [sopermanspace.github.io/open-model-archive](https://sopermanspace.github.io/open-model-archive/) is generated from committed `runs/`. You can explore comparisons there with zero local setup.