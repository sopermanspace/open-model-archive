import hashlib
import re
from pathlib import Path

from oma.models.run import Artifact, Screenshot


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _extract_fenced_block(text: str, language: str | None = None) -> str | None:
    pattern = r"```(?:html|HTML)?\s*\n(.*?)```"
    if language:
        pattern = rf"```{re.escape(language)}\s*\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fallback: any fenced block
    match = re.search(r"```[^\n]*\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_html(raw_output: str, artifacts_dir: Path) -> list[Artifact]:
    html = _extract_fenced_block(raw_output, "html")
    if not html:
        # If the model returned bare HTML, accept it when it looks like HTML.
        stripped = raw_output.strip()
        if stripped.lower().startswith("<!doctype") or stripped.lower().startswith("<html"):
            html = stripped
        else:
            raise ValueError("No HTML found in model output")

    out_path = artifacts_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    return [
        Artifact(
            type="html",
            path=str(out_path.relative_to(artifacts_dir.parent)),
            sha256=_sha256_file(out_path),
            language="html",
        )
    ]


def extract_svg(raw_output: str, artifacts_dir: Path) -> list[Artifact]:
    svg = _extract_fenced_block(raw_output, "svg")
    if not svg:
        match = re.search(r"(<svg[\s\S]*?</svg>)", raw_output, re.IGNORECASE)
        svg = match.group(1).strip() if match else None
    if not svg:
        raise ValueError("No SVG found in model output")

    out_path = artifacts_dir / "output.svg"
    out_path.write_text(svg, encoding="utf-8")
    return [
        Artifact(
            type="svg",
            path=str(out_path.relative_to(artifacts_dir.parent)),
            sha256=_sha256_file(out_path),
            language="svg",
        )
    ]


def extract_code(raw_output: str, artifacts_dir: Path, language: str = "python") -> list[Artifact]:
    code = _extract_fenced_block(raw_output, language)
    if not code:
        raise ValueError(f"No {language} code block found in model output")

    ext = {"python": "py", "javascript": "js", "typescript": "ts"}.get(language, "txt")
    out_path = artifacts_dir / f"main.{ext}"
    out_path.write_text(code, encoding="utf-8")
    return [
        Artifact(
            type="source",
            path=str(out_path.relative_to(artifacts_dir.parent)),
            sha256=_sha256_file(out_path),
            language=language,
        )
    ]


PROCESSORS = {
    "extract_html": lambda raw, d: extract_html(raw, d),
    "extract_svg": lambda raw, d: extract_svg(raw, d),
    "extract_python": lambda raw, d: extract_code(raw, d, "python"),
}


def run_post_processors(names: list[str], raw_output: str, run_dir: Path) -> list[Artifact]:
    artifacts_dir = run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[Artifact] = []
    for name in names:
        processor = PROCESSORS.get(name)
        if not processor:
            raise ValueError(f"Unknown post-processor: {name}")
        artifacts.extend(processor(raw_output, artifacts_dir))
    return artifacts


def attach_screenshot(run_dir: Path, screenshot_path: Path, viewport: str) -> Screenshot:
    rel = screenshot_path.relative_to(run_dir)
    return Screenshot(
        path=str(rel),
        viewport=viewport,
        sha256=_sha256_file(screenshot_path),
    )