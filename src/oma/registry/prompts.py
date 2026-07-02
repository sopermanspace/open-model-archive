import hashlib
import re
from pathlib import Path

import yaml

from oma.models.prompt import Prompt, PromptFrontmatter
from oma.paths import PROMPTS_DIR


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def _parse_prompt_file(path: Path) -> Prompt:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"Prompt file missing YAML frontmatter: {path}")

    meta = PromptFrontmatter.model_validate(yaml.safe_load(match.group(1)))
    body = match.group(2).strip()
    sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return Prompt(meta=meta, body=body, path=str(path.relative_to(PROMPTS_DIR.parent)), sha256=sha256)


def load_prompt(ref: str) -> Prompt:
    """Load a versioned prompt by reference like 'website-generation/landing-page@v1.0.0'."""
    if "@" not in ref:
        raise ValueError(f"Invalid prompt reference: {ref}")

    path_part, version = ref.rsplit("@", 1)
    version_tag = version if version.startswith("v") else f"v{version}"
    prompt_path = PROMPTS_DIR / path_part / f"{version_tag}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")

    prompt = _parse_prompt_file(prompt_path)
    normalized = version.removeprefix("v")
    if prompt.meta.version != normalized and prompt.meta.version != version:
        raise ValueError(f"Prompt version mismatch in {prompt_path}")
    return prompt


def list_prompts() -> list[Prompt]:
    prompts: list[Prompt] = []
    for path in sorted(PROMPTS_DIR.rglob("v*.md")):
        prompts.append(_parse_prompt_file(path))
    return prompts