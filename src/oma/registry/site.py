from pathlib import Path

import yaml
from pydantic import BaseModel

from oma.paths import ROOT


class SiteConfig(BaseModel):
    base_path: str = "/open-model-archive"
    canonical_url: str = "https://sopermanspace.github.io/open-model-archive"


def load_site_config() -> SiteConfig:
    path = ROOT / "registry" / "site.yaml"
    if not path.exists():
        return SiteConfig()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SiteConfig.model_validate(data)