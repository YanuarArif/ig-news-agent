"""Sensitivity guard for detecting sensitive/restricted content categories.

Checks news content against prohibited categories (SARA, terrorism, adult,
gambling, scams, hoaxes, radicalism) before allowing publication.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SensitivityResult:
    """Result of sensitivity check."""
    is_sensitive: bool
    categories: list[str]
    confidence: float
    reasoning: str
    flagged_terms: list[str]
    sensitivity_score: int = 0  # 1-10: Sensitivity risk (higher = more sensitive)

    def __post_init__(self):
        """Calculate sensitivity_score based on categories and confidence."""
        if self.is_sensitive:
            # Base score from number of categories
            base_score = min(len(self.categories) * 2, 8)
            # Add confidence factor
            confidence_bonus = int(self.confidence * 2)
            self.sensitivity_score = min(base_score + confidence_bonus, 10)
        else:
            self.sensitivity_score = 0

    def to_dict(self) -> dict:
        return {
            "is_sensitive": self.is_sensitive,
            "categories": self.categories,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "flagged_terms": self.flagged_terms,
            "sensitivity_score": self.sensitivity_score,
        }


class SensitivityGuard:
    """Detect sensitive content categories in news."""

    SENSITIVE_CATEGORIES = {
        "SARA": [
            r"\b(suku|ras|agama|antara|berbeda|sara|sukai)\b",
            r"\b(kafir|musyrik|bidah|sesat|kafirin)\b",
            r"\b(musuh.*agama|ancam.*agama|melanggar.*agama)\b",
        ],
        "terorisme": [
            r"\b(bom|ledakan|teror|terorisme|bom.*bunuh|jihad|isis|isis)\b",
            r"\b(penembakan|penusukan|amok|radikal|ekstremis)\b",
        ],
        "pornografi": [
            r"\b(porno|pornografi|bokep|seks|mesum|telanjang|konten.*dewasa)\b",
        ],
        "judi_online": [
            r"\b(judi|slot|casino|poker|togel|bandar|taruhan|gambling)\b",
        ],
        "penipuan_investasi": [
            r"\b(investasi.*bodong|skema.*ponzi|penipuan.*invest|bodong.*invest)\b",
            r"\b(biaya.*admin|transfer.*dulu|jaminan.*profit|return.*tinggi.*jaminan)\b",
        ],
        "hoaks_kesehatan": [
            r"\b(vaksin.*mati|vaksin.*bahaya|obat.*mujarab|herbal.*sembuhkan.*semua|covid.*hoaks|virus.*palsu)\b",
        ],
        "radikalisme": [
            r"\b(khalifah|syariat|khilafah|daulah|hijrah.*perang|perang.*sabil)\b",
        ],
        "kekerasan_seksual": [
            r"\b(pelecehan|pemerkosaan|kekerasan.*seksual|pedofilia|eksploitasi.*seksual)\b",
        ],
        "eksploitasi_anak": [
            r"\b(anak.*dielektasikan|pekerja.*anak|trafficking.*anak|penyelundupan.*anak)\b",
        ],
        "narkoba": [
            r"\b(narkoba|sabu|ganja|putau|ekstasi|shabu|drugs|penyalahgunaan.*narkoba)\b",
        ],
        "pencucian_uang": [
            r"\b(pencucian.*uang|money.*laundering|korupsi|suap|gratifikasi|pungli)\b",
        ],
    }

    def __init__(self):
        """Initialize with configured sensitive categories."""
        self.compiled_patterns = {}
        for cat, patterns in self.SENSITIVE_CATEGORIES.items():
            self.compiled_patterns[cat] = [re.compile(p, re.IGNORECASE) for p in patterns]

    def check(self, title: str, content: str) -> SensitivityResult:
        """Check content for sensitive categories.

        Args:
            title: News title
            content: News content/summary

        Returns:
            SensitivityResult with findings
        """
        full_text = f"{title} {content}".lower()
        flagged_categories = []
        flagged_terms = []

        for cat, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(full_text)
                if matches:
                    flagged_categories.append(cat)
                    flagged_terms.extend(matches)
                    break  # One match per category is enough

        is_sensitive = len(flagged_categories) > 0
        confidence = min(1.0, len(flagged_categories) * 0.3 + len(flagged_terms) * 0.1) if is_sensitive else 0.0
        
        if is_sensitive:
            reasoning = f"Detected sensitive categories: {', '.join(flagged_categories)}. Flagged terms: {', '.join(set(flagged_terms))}"
        else:
            reasoning = "No sensitive content detected"

        return SensitivityResult(
            is_sensitive=is_sensitive,
            categories=flagged_categories,
            confidence=round(confidence, 2),
            reasoning=reasoning,
            flagged_terms=list(set(flagged_terms)),
        )

    def check_batch(self, items: list[dict]) -> list[SensitivityResult]:
        """Check multiple items."""
        return [self.check(item.get("title", ""), item.get("summary", "")) for item in items]


def get_sensitivity_guard() -> SensitivityGuard:
    """Get configured sensitivity guard instance."""
    return SensitivityGuard()


# Convenience function
_guard_instance = None

def check_sensitivity(text: str) -> SensitivityResult:
    """Convenience function to check sensitivity."""
    global _guard_instance
    if _guard_instance is None:
        _guard_instance = SensitivityGuard()
    # Split into title/content roughly
    parts = text.split(". ", 1)
    title = parts[0] if parts else ""
    content = parts[1] if len(parts) > 1 else text
    return _guard_instance.check(title, content)