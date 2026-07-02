from pathlib import Path

import yaml

from oma.models.model_config import ModelConfig
from oma.paths import MODELS_DIR


def _load_model_file(path: Path) -> ModelConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ModelConfig.model_validate(data)


def list_models(*, include_disabled: bool = False) -> list[ModelConfig]:
    models: list[ModelConfig] = []
    for path in sorted(MODELS_DIR.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        model = _load_model_file(path)
        if model.enabled or include_disabled:
            models.append(model)
    return models


def load_model(model_id: str) -> ModelConfig:
    for model in list_models(include_disabled=True):
        if model.id == model_id:
            return model
    raise FileNotFoundError(f"Model not found: {model_id}")


def resolve_task_models(task_models: list[str] | str) -> list[ModelConfig]:
    all_models = list_models()
    if task_models == "all":
        return all_models
    resolved: list[ModelConfig] = []
    for model_id in task_models:
        resolved.append(load_model(model_id))
    return resolved