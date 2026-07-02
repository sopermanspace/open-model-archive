"""Token counting utilities."""

from __future__ import annotations


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken when available, else a conservative estimate."""
    text = text or ""
    if not text:
        return 0

    try:
        import tiktoken

        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Conservative fallback: ~3.2 chars/token for English prose/code mix
        return max(1, int(len(text) / 3.2))


def count_prompt_and_output(*, prompt: str, output: str) -> tuple[int, int]:
    return count_tokens(prompt), count_tokens(output)