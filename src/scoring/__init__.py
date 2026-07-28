"""Scoring package: LLM-based news scoring for viral potential, credibility, and sensitivity."""

from src.scoring.llm_client import LLMClient
from src.scoring.news_scorer import NewsScorer, ScoreResult, score_news, score_batch
from src.scoring.sensitivity_guard import check_sensitivity, SensitivityResult
from src.scoring.cross_verification import check_cross_verification, VerificationResult
from src.scoring.heuristic_scorer import HeuristicScorer, get_heuristic_scorer

__all__ = [
    "LLMClient",
    "NewsScorer",
    "ScoreResult",
    "score_news",
    "score_batch",
    "check_sensitivity",
    "SensitivityResult",
    "check_cross_verification",
    "VerificationResult",
    "HeuristicScorer",
    "get_heuristic_scorer",
]