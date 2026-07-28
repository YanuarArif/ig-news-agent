"""Shared data structures for scoring."""

from dataclasses import dataclass
from typing import Optional


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