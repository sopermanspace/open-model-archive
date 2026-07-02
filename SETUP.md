# Setup Guide

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended)
- [Ollama](https://ollama.com/) for open-source and cloud-backed models
- Node.js 20+ (screenshots only)

## Install

```bash
git clone https://github.com/sopermanspace/open-model-archive.git
cd open-model-archive

uv sync
npm install
npx playwright install chromium
```

## Configure providers

### Ollama (local + cloud)

Pull the models you need:

```bash
ollama pull gemma4:latest
ollama pull kimi-k2.7-code:cloud
```

Cloud models require an authenticated Ollama account synced locally. No API keys are stored in this repository.

### agy CLI (frontier models)

Install and authenticate `agy` separately. Add models via `models/*.yaml` with `adapter: agy`.

## Run the pipeline

```bash
# Validate configuration
uv run oma validate

# Execute all tasks against all enabled models
uv run oma run --all

# Generate static site
uv run oma generate

# Or do everything
uv run oma build
```

## Preview locally

```bash
python -m http.server 8080 --directory docs
```

Open http://localhost:8080