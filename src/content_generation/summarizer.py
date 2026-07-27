"""Summarize news content into concise bullet points for infographics.

Uses LLM to paraphrase news into key points suitable for visual
infographic templates, avoiding direct copy-paste of original text.
"""

from dataclasses import dataclass
from typing import Optional

from config.settings import get_settings
from src.content_generation.prompts import load_prompt
from src.scoring.llm_client import get_llm_client, LLMClient


@dataclass
class SummaryResult:
    """Structured summary for infographic."""
    headline: str           # Short catchy headline (max 60 chars)
    key_points: list[str]   # 3-5 bullet points
    category: str           # breaking_news, entertainment, general, etc.
    tone: str               # urgent, informative, light, etc.
    source_attribution: str # Source credit line

    def to_dict(self) -> dict:
        return {
            "headline": self.headline,
            "key_points": self.key_points,
            "category": self.category,
            "tone": self.tone,
            "source_attribution": self.source_attribution,
        }


class NewsSummarizer:
    """Generate infographic-ready summaries from news items."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or get_llm_client()

    def summarize(self, item: dict, score_result: dict) -> SummaryResult:
        """Summarize a scored news item for infographic.

        Args:
            item: Original news item dict
            score_result: ScoreResult dict from NewsScorer

        Returns:
            SummaryResult with headline, key points, category, tone
        """
        raise NotImplementedError

    def _build_prompt(self, item: dict, score_result: dict) -> str:
        """Build summarization prompt from template."""
        raise NotImplementedError

    def _parse_response(self, response: str) -> SummaryResult:
        """Parse LLM response into SummaryResult."""
        raise NotImplementedError


def summarize_news(item: dict, score_result: dict) -> SummaryResult:
    """Convenience function to summarize a news item."""
    raise NotImplementedError