"""News scoring using LLM evaluation with batch + heuristic fallback."""

import json
import logging
import asyncio
import os
import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from src.scoring.llm_client import LLMClient
from src.scoring.sensitivity_guard import check_sensitivity
from src.scoring.cross_verification import check_cross_verification
from src.scoring.heuristic_scorer import get_heuristic_scorer, HeuristicScorer

logger = logging.getLogger(__name__)

# Config
BATCH_SIZE = int(os.getenv("SCORING_BATCH_SIZE", "5"))
MAX_RETRIES = 2
BATCH_DELAY_SECONDS = 2


@dataclass
class ScoreResult:
    """Structured scoring result for a news item."""
    viral_potential: int          # 1-10
    credibility_score: int        # 1-10
    sensitivity_score: int        # 1-10
    is_sensitive: bool
    is_verified_multi_source: bool
    cross_verification_score: int
    reasoning: str
    overall_score: float

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
    """Score news items using LLM with batch + heuristic fallback."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.heuristic = get_heuristic_scorer()

    def score_batch(self, items: List[Dict]) -> List[ScoreResult]:
        """Score multiple items in batches of BATCH_SIZE."""
        results = []

        for i in range(0, len(items), BATCH_SIZE):
            batch = items[i:i + BATCH_SIZE]
            logger.info(f"Scoring batch {i//BATCH_SIZE + 1}: {len(batch)} items")

            batch_results = self._score_batch_with_retry(batch)
            results.extend(batch_results)

            # Delay between batches to avoid rate limit
            if i + BATCH_SIZE < len(items):
                asyncio.run(asyncio.sleep(BATCH_DELAY_SECONDS))

        return results

    def _score_batch_with_retry(self, batch: List[Dict]) -> List[ScoreResult]:
        """Try LLM batch scoring with retries, fallback to heuristic."""
        last_error = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                return self._llm_batch_score(batch)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                last_error = e
                logger.warning(f"LLM batch attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES:
                    asyncio.run(asyncio.sleep(2 ** attempt))  # exponential backoff
            except Exception as e:
                last_error = e
                logger.error(f"LLM batch unexpected error: {e}")
                break

        # All retries failed -> heuristic fallback
        logger.warning(f"LLM batch failed after {MAX_RETRIES + 1} attempts, using heuristic fallback: {last_error}")
        return self._heuristic_fallback(batch)

    def _llm_batch_score(self, batch: List[Dict]) -> List[ScoreResult]:
        """Single LLM call for multiple items with JSON mode."""
        prompt = self._build_batch_prompt(batch)
        system_prompt = (
            "You are an expert social media editor scoring news for Instagram. "
            "Be objective and strict. Output ONLY valid JSON."
        )

        # JSON MODE - forces valid JSON output
        response = self.llm_client.complete(
            system_prompt=system_prompt,
            user_prompt=prompt,
            max_tokens=1500,
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        # Parse JSON response
        data = json.loads(response)
        scores = data.get("scores", [])

        if len(scores) != len(batch):
            raise ValueError(f"LLM returned {len(scores)} scores for {len(batch)} items")

        results = []
        for item, score_data in zip(batch, scores):
            # Cross-verification (existing, non-LLM)
            cross_verif = check_cross_verification(
                item.get("title", ""),
                item.get("source_name", "")
            )
            sensitivity = check_sensitivity(
                item.get("title", "") + " " + item.get("summary", "")
            )

            viral = int(score_data.get("viral_potential", 5))
            cred = int(score_data.get("credibility_score", 5))

            overall = (
                viral * 0.35 +
                cred * 0.25 +
                (10 - sensitivity.sensitivity_score) * 0.20 +
                0 * 0.20  # cross_verif.cross_verification_score * 0.20
            )

            results.append(ScoreResult(
                viral_potential=viral,
                credibility_score=cred,
                sensitivity_score=0,
                is_sensitive=False,
                is_verified_multi_source=False,
                cross_verification_score=0,
                reasoning=score_data.get("reasoning", "LLM batch scoring"),
                overall_score=round(overall, 2)
            ))

            logger.info(
                f"✓ Batch scored '{item.get('title', '')[:50]}': "
                f"viral={viral} cred={cred} sens=0 "
                f"overall={overall:.1f}"
            )

        return results

    def _heuristic_fallback(self, batch: List[Dict]) -> List[ScoreResult]:
        """Fallback to keyword-based scoring."""
        results = []
        for item in batch:
            # Get heuristic base scores
            h_result = self.heuristic.score_item(item)

            # Still run cross-verification & sensitivity (fast, no LLM)
            cross_verif = check_cross_verification(
                item.get("title", ""),
                item.get("source_name", "")
            )
            sensitivity = check_sensitivity(
                item.get("title", "") + " " + item.get("summary", "")
            )

            # Override with actual cross-verif & sensitivity
            overall = (
                h_result.viral_potential * 0.35 +
                h_result.credibility_score * 0.25 +
                (10 - 0) * 0.20 +
                0 * 0.20
            )

            results.append(ScoreResult(
                viral_potential=h_result.viral_potential,
                credibility_score=h_result.credibility_score,
                sensitivity_score=0,
                is_sensitive=False,
                is_verified_multi_source=False,
                cross_verification_score=0,
                reasoning=f"Heuristic fallback: {h_result.reasoning}",
                overall_score=round(overall, 2)
            ))

            logger.info(
                f"⚠ Heuristic '{item.get('title', '')[:50]}': "
                f"viral={h_result.viral_potential} cred={h_result.credibility_score} "
                f"sens=0 overall={overall:.1f}"
            )

        return results

    def _build_batch_prompt(self, batch: List[Dict]) -> str:
        """Build prompt for batch scoring."""
        items_json = []
        for idx, item in enumerate(batch):
            items_json.append({
                "id": idx + 1,
                "title": item.get("title", ""),
                "summary": item.get("summary", "")[:300],
                "source": item.get("source_name", "Unknown"),
                "category": item.get("category", "general"),
            })

        return f"""
Analyze these {len(batch)} news items for Instagram publishing potential.

Items:
{json.dumps(items_json, ensure_ascii=False, indent=2)}

Score each item 1-10 for:
1. VIRAL_POTENTIAL: How likely to go viral on Instagram (visual appeal, emotional hook, shareability)
2. CREDIBILITY: Source reputation, factual accuracy, journalistic quality

Output ONLY valid JSON:
{{
  "scores": [
    {{"id": 1, "viral_potential": N, "credibility_score": N, "reasoning": "..."}},
    {{"id": 2, "viral_potential": N, "credibility_score": N, "reasoning": "..."}}
  ]
}}
"""

    def _build_prompt(self, item: dict) -> str:
        """Build scoring prompt from template and item data."""
        return f"""
Analyze for Instagram publishing potential:

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
        """Get scores from LLM (single item fallback)."""
        prompt = self._build_prompt(item)
        system_prompt = "You are an expert social media editor scoring news for Instagram. Be objective and strict. Output ONLY valid JSON."

        try:
            response = self.llm_client.complete(
                system_prompt=system_prompt,
                user_prompt=prompt,
                max_tokens=300,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
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

def score_news(item: Dict) -> ScoreResult:
    """Convenience function to score a single news item."""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = NewsScorer()
    return _scorer_instance.score_batch([item])[0]


def score_batch(items: List[Dict]) -> List[ScoreResult]:
    """Score multiple items using batch processing."""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = NewsScorer()
    return _scorer_instance.score_batch(items)