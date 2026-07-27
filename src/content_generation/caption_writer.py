"""Generate Instagram captions with hashtags from summarized news.

Creates engaging captions optimized for Instagram with relevant
hashtags, call-to-action, and source attribution.
"""

from dataclasses import dataclass
from typing import Optional

from config.settings import get_settings
from src.content_generation.prompts import load_prompt
from src.scoring.llm_client import get_llm_client, LLMClient


@dataclass
class CaptionResult:
    """Generated caption with metadata."""
    caption: str            # Main caption text
    hashtags: list[str]     # Relevant hashtags (max 30)
    cta: str                # Call to action
    full_text: str          # Caption + hashtags + CTA combined
    character_count: int    # Total character count

    def to_dict(self) -> dict:
        return {
            "caption": self.caption,
            "hashtags": self.hashtags,
            "cta": self.cta,
            "full_text": self.full_text,
            "character_count": self.character_count,
        }


class CaptionWriter:
    """Generate Instagram captions from summarized news."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or get_llm_client()

    def write_caption(self, summary: dict, score_result: dict) -> CaptionResult:
        """Write caption from summary and scores.

        Args:
            summary: SummaryResult dict from NewsSummarizer
            score_result: ScoreResult dict from NewsScorer

        Returns:
            CaptionResult with caption, hashtags, CTA
        """
        raise NotImplementedError

    def _build_prompt(self, summary: dict, score_result: dict) -> str:
        """Build caption writing prompt from template."""
        raise NotImplementedError

    def _parse_response(self, response: str, base_caption: str) -> CaptionResult:
        """Parse LLM response into CaptionResult."""
        raise NotImplementedError

    def _extract_hashtags(self, text: str) -> list[str]:
        """Extract hashtags from generated text."""
        raise NotImplementedError


def write_caption(summary: dict, score_result: dict) -> CaptionResult:
    """Convenience function to generate caption."""
    raise NotImplementedError