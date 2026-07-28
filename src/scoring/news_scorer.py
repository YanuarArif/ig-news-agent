"""News scoring using LLM evaluation.

Evaluates news items for viral potential, credibility, sensitivity,
and cross-source verification. Returns structured score results.
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional

from src.scoring.llm_client import LLMClient
from src.scoring.sensitivity_guard import check_sensitivity
from src.scoring.cross_verification import check_cross_verification
from src.scoring.llm_client import LLMClient

logger = logging.getLogger(__name__)


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

    def passes_threshold(self, viral_thresh: int = 7, cred_thresh: int = 6) -> bool:
        """Check if item passes minimum thresholds for publishing."""
        return (
            self.viral_potential >= viral_thresh and
            self.credibility_score >= cred_thresh and
            not self.is_sensitive
        )

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
        self.llm_client = llm_client or LLMClient()

    def score_news(self, item: dict) -> ScoreResult:
        """Score a single news item.

        Args:
            item: News item dict with title, summary, source, url, etc.

        Returns:
            ScoreResult with all scores and reasoning
        """
        # 1. Check sensitivity first (fast, rule-based)
        sensitivity = check_sensitivity(item.get("title", "") + " " + item.get("summary", ""))
        
        # 2. Cross-verification check
        cross_verif = check_cross_verification(
            item.get("title", ""),
            item.get("source_name", "")
        )
        
        # 3. LLM scoring for viral potential & credibility
        llm_scores = self._llm_score(item)
        
        # Combine scores
        viral = llm_scores.get("viral_potential", 5)
        cred = llm_scores.get("credibility_score", 5)
        
        # Weighted overall score
        overall = (
            viral * 0.35 +
            cred * 0.25 +
            (10 - sensitivity.sensitivity_score) * 0.20 +  # Lower sensitivity = higher score
            cross_verif.cross_verification_score * 0.20
        )
        
        result = ScoreResult(
            viral_potential=viral,
            credibility_score=cred,
            sensitivity_score=sensitivity.sensitivity_score,
            is_sensitive=sensitivity.is_sensitive,
            is_verified_multi_source=cross_verif.is_verified,
            cross_verification_score=cross_verif.cross_verification_score,
            reasoning=llm_scores.get("reasoning", ""),
            overall_score=round(overall, 2)
        )
        
        logger.info(f"Scored '{item.get('title', '')[:50]}': viral={viral}, cred={cred}, sens={sensitivity.sensitivity_score}, overall={overall:.1f}")
        return result

    def score_batch(self, items: list[dict]) -> list[ScoreResult]:
        """Score multiple news items."""
        return [self.score_news(item) for item in items]

    def _build_prompt(self, item: dict) -> str:
        """Build scoring prompt from template and item data."""
        return f"""
Analyze this news item for Instagram publishing potential:

Title: {item.get('title', '')}
Summary: {item.get('summary', '')}
Source: {item.get('source_name', 'Unknown')}
Category: {item.get('category', 'general')}

Score each dimension 1-10:

1. VIRAL_POTENTIAL: How likely to go viral on Instagram (visual appeal, emotional hook, shareability)
2. CREDIBILITY: Source reputation, factual accuracy, journalistic quality
3. REASONING: Brief explanation for scores

Output ONLY JSON:
{{"viral_potential": N, "credibility_score": N, "reasoning": "..."}}
"""

    def _llm_score(self, item: dict) -> dict:
        """Get scores from LLM."""
        prompt = self._build_prompt(item)
        system_prompt = "You are an expert social media editor scoring news for Instagram. Be objective and strict. Output ONLY valid JSON."
        
        try:
            response = self.llm_client.complete(system_prompt, prompt, max_tokens=300)
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # Try direct parse
                return json.loads(response)
        except Exception as e:
            logger.error(f"LLM scoring failed: {e}")
            # Fallback scores
            return {"viral_potential": 5, "credibility_score": 5, "reasoning": "LLM failed, using defaults"}

    def _parse_response(self, response: str) -> ScoreResult:
        """Parse LLM response into ScoreResult."""
        data = json.loads(response)
        return ScoreResult(
            viral_potential=data.get("viral_potential", 5),
            credibility_score=data.get("credibility_score", 5),
            sensitivity_score=0,
            is_sensitive=False,
            is_verified_multi_source=False,
            cross_verification_score=0,
            reasoning=data.get("reasoning", ""),
            overall_score=0.0,
        )


# Convenience function
_scorer_instance = None

def score_news(item: dict) -> ScoreResult:
    """Convenience function to score a single news item."""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = NewsScorer()
    return _scorer_instance.score_news(item)