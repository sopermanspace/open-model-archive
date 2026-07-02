from pathlib import Path

import yaml
from pydantic import BaseModel

from oma.paths import ROOT


class Topic(BaseModel):
    id: str
    title: str
    description: str


def list_topics() -> list[Topic]:
    path = ROOT / "registry" / "topics.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [Topic.model_validate(item) for item in data.get("topics", [])]


def topics_by_id() -> dict[str, Topic]:
    return {topic.id: topic for topic in list_topics()}