from pathlib import Path

import yaml
from pydantic import BaseModel

from oma.paths import ROOT


class SiteConfig(BaseModel):
    base_path: str = "/open-model-archive"
    canonical_url: str = "https://sopermanspace.github.io/open-model-archive"
    title: str = "Open Model Archive — Compare AI Model Outputs"
    description: str = (
        "Side-by-side AI model outputs on real-world tasks. Inspect artifacts, "
        "screenshots, timing, tokens, and cost — with versioned prompts and "
        "full reproducibility."
    )
    keywords: str = (
        "AI model comparison, LLM outputs, model evaluation, prompt versioning, "
        "AI artifacts, side-by-side comparison, open source AI"
    )
    robots: str = "index, follow"
    author: str = "sopermanspace"
    publisher: str = "Open Model Archive"
    api_base_url: str | None = None


def load_site_config() -> SiteConfig:
    path = ROOT / "registry" / "site.yaml"
    if not path.exists():
        return SiteConfig()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SiteConfig.model_validate(data)