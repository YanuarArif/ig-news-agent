"""Sensitivity guard for detecting sensitive/restricted content categories.

Checks news content against prohibited categories (SARA, terrorism, adult,
gambling, scams, hoaxes, radicalism) before allowing publication.
"""

from dataclasses import dataclass
from typing import Optional

from config.settings import get_settings


@dataclass
class SensitivityResult:
    """Result of sensitivity check."""
    is_sensitive: bool
    categories: list[str]
    confidence: float
    reasoning: str
    flagged_terms: list[str]

    def to_dict(self) -> dict:
        return {
            "is_sensitive": self.is_sensitive,
            "categories": self.categories,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "flagged_terms": self.flagged_terms,
        }


class SensitivityGuard:
    """Detect sensitive content categories in news."""

    SENSITIVE_CATEGORIES = [
        "SARA",
        "terorisme",
        "pornografi",
        "judi online",
        "penipuan investasi",
        "hoaks COVID",
        "radikalisme",
        "kekerasan seksual",
        "eksploitasi anak",
        "narkoba",
        "pencucian uang",
    ]

    def __init__(self):
        """Initialize with configured sensitive categories."""
        raise NotImplementedError

    def check(self, title: str, content: str) -> SensitivityResult:
        """Check content for sensitive categories.

        Args:
            title: News title
            content: News content/summary

        Returns:
            SensitivityResult with findings
        """
        raise NotImplementedError

    def check_batch(self, items: list[dict]) -> list[SensitivityResult]:
        """Check multiple items."""
        raise NotImplementedError


def get_sensitivity_guard() -> SensitivityGuard:
    """Get configured sensitivity guard instance."""
    raise NotImplementedError