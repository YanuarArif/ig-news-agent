"""News scoring using LLM evaluation.

Evaluates news items for viral potential, credibility, sensitivity,
and cross-source verification. Returns structured score results.
"""

from dataclasses import dataclass
from typing import Optional

from config.settings import get_settings
from src.content_generation.prompts import load_prompt
from src.scoring.llm_client import get_llm_client, LLMClient


@dataclass
class ScoreResult:
    """Structured scoring result for a news item."""
    viral_potential: int          # 1-10: How likely to go viral on IG
    credibility_score: int        # 1-10: Source credibility & factual accuracy
    sensitivity_score: int        # 1-10: Sensitivity risk (higher = more sensitive)
    is_sensitive: bool            # True if contains sensitive topics
    is_verified_multi_source: bool  # True if verified by multiple sources
    cross_verification_score: int # 1-10: Multi-source confirmation strength
    reasoning: str                # LLM reasoning for scores
    overall_score: float          # Weighted composite score

    def passes_threshold(self) -> bool:
        """Check if item passes minimum thresholds for publishing."""
        raise NotImplementedError

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "viral_potential": self.viral_potential,
            "credibility_score": self.credibility_score,
            "sensitivity_score": self.sensitivity_score,
            "is_sensitive": self.is_sensitive,
            "is_verified_multi_source": self.is_verified_multi_source,
            "cross_verification_score": self.cross_verification_score,
            "reasoning": self.reasoning,
            "overall_score": self.overall_score,
        }


class NewsScorer:
    """Score news items using LLM evaluation."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize with optional custom LLM client."""
        self.llm_client = llm_client or get_llm_client()

    def score_news(self, item: dict) -> ScoreResult:
        """Score a single news item.

        Args:
            item: News item dict with title, summary, source, url, etc.

        Returns:
            ScoreResult with all scores and reasoning
        """
        raise NotImplementedError

    def score_batch(self, items: list[dict]) -> list[ScoreResult]:
        """Score multiple news items."""
        raise NotImplementedError

    def _build_prompt(self, item: dict) -> str:
        """Build scoring prompt from template and item data."""
        raise NotImplementedError

    def _parse_response(self, response: str) -> ScoreResult:
        """Parse LLM response into ScoreResult."""
        raise NotImplementedError


def score_news(item: dict) -> ScoreResult:
    """Convenience function to score a single news item."""
    raise NotImplementedError