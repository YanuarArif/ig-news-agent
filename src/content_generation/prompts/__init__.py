"""Load prompt templates from text files.

Provides utilities to load LLM prompt templates from the prompts/
directory, keeping prompts separate from Python code.
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt(name: str) -> str:
    """Load prompt template by name (without .txt extension).

    Args:
        name: Prompt filename without extension (e.g., 'scoring_prompt')

    Returns:
        Prompt template string
    """
    path = PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def load_scoring_prompt() -> str:
    return load_prompt("scoring_prompt")


def load_summarize_prompt() -> str:
    return load_prompt("summarize_prompt")


def load_caption_prompt() -> str:
    return load_prompt("caption_prompt")