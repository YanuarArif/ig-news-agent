"""Keyword-based heuristic scoring - zero API calls, fast fallback."""

import re
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

from src.scoring.models import ScoreResult

logger = logging.getLogger(__name__)

# Source credibility tiers (1-10)
SOURCE_CREDIBILITY = {
    # Tier 1: Major national (9-10)
    "cnn indonesia": 9, "tempo": 9, "kompas": 9, "detik": 8, "liputan6": 8,
    "antara": 9, "republika": 7, "suara": 7, "okezone": 6,
    # Tier 2: Regional/tech (6-8)
    "teknologi": 7, "tekno": 7, "gadget": 6,
    # Default
    "default": 5
}

# Viral trigger keywords (weight 0.5-2.0)
VIRAL_KEYWORDS = {
    "breaking": 2.0, "viral": 1.8, "shocking": 1.5, "exclusive": 1.5,
    "bocor": 1.8, "terungkap": 1.5, "rahasia": 1.3, "heboh": 1.5,
    "trending": 1.3, "wow": 1.0, "gempar": 1.5, "kaget": 1.0,
    "gratis": 1.2, "gratis!": 1.5, "cuma": 0.8, "gratisnya": 1.0,
    "dapat": 0.5, "menang": 0.8, "hadiah": 0.8, "bonus": 0.8,
    "anjur": 0.5, "waspada": 1.0, "bahaya": 1.2, "awas": 1.0,
}

# Clickbait / sensationalism patterns
CLICKBAIT_PATTERNS = [
    r"kamu tidak akan percaya", r"nggak akan nyangka", r"bikin ngakak",
    r"bikin terharu", r"bikin ketar-ketir", r"hanya \d+ orang",
    r"rahasia .*? diungkap", r"fakta mengejutkan", r"!!!+",
]

SENSITIVE_KEYWORDS = {
    "sara": 10, "teror": 9, "bom": 9, "pembunuhan": 8, "bunuh diri": 9,
    "pelecehan": 8, "ksdr": 8, "radikal": 7, "ekstremis": 7,
    "bumil": 3, "bayi": 3, "anak": 2, "kematian": 5,
}


@dataclass
class HeuristicScorer:
    def score_batch(self, items: List[Dict]) -> List[ScoreResult]:
        """Score multiple items without LLM."""
        return [self.score_item(item) for item in items]

    def score_item(self, item: Dict) -> ScoreResult:
        title = item.get("title", "").lower()
        summary = item.get("summary", "").lower()
        source = item.get("source_name", "").lower()
        text = f"{title} {summary}"

        # 1. VIRAL POTENTIAL (1-10)
        viral = self._score_viral(title, text)

        # 2. CREDIBILITY (1-10)
        cred = self._score_credibility(source, text)

        # 3. SENSITIVITY (1-10)
        sens, is_sensitive = self._score_sensitivity(text)

        # 4. CROSS VERIFICATION - use existing (skip heuristic)
        cross_score = 0
        is_verified = False

        # 5. OVERALL
        overall = (
            viral * 0.35 +
            cred * 0.25 +
            (10 - sens) * 0.20 +
            0 * 0.20  # cross_score * 0.20
        )

        return ScoreResult(
            viral_potential=viral,
            credibility_score=cred,
            sensitivity_score=sens,
            is_sensitive=is_sensitive,
            is_verified_multi_source=is_verified,
            cross_verification_score=0,
            reasoning=f"Heuristic: viral={viral}, cred={cred}, sens={sens}",
            overall_score=round(overall, 2)
        )

    def _score_viral(self, title: str, text: str) -> int:
        score = 5  # base

        # Keyword boost
        for kw, weight in VIRAL_KEYWORDS.items():
            if kw in text:
                score += weight

        # Title length sweet spot (60-100 chars)
        if 60 <= len(title) <= 100:
            score += 1
        elif len(title) < 30:
            score -= 1

        # Numbers in title (listicles)
        if re.search(r"\b\d+\b", title):
            score += 0.5

        # Question mark = curiosity
        if "?" in title:
            score += 0.5

        return max(1, min(10, int(round(score))))

    def _score_credibility(self, source: str, text: str) -> int:
        # Source tier
        cred = SOURCE_CREDIBILITY.get(source, SOURCE_CREDIBILITY["default"])

        # Factual indicators
        factual_boost = 0
        if any(w in text for w in ["menurut", "data", "survei", "riset", "studi", "laporan", "resmi", "pemerintah", "kementerian", "polisi", "mabes"]):
            factual_boost += 1
        if re.search(r"\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\b", text):  # numbers with separators
            factual_boost += 0.5

        # Clickbait penalty
        clickbait_penalty = 0
        for pat in CLICKBAIT_PATTERNS:
            if re.search(pat, text):
                clickbait_penalty += 1.5

        final = cred + factual_boost - clickbait_penalty
        return max(1, min(10, int(round(final))))

    def _score_sensitivity(self, text: str) -> tuple[int, bool]:
        max_sens = 0
        for kw, weight in SENSITIVE_KEYWORDS.items():
            if kw in text:
                max_sens = max(max_sens, weight)

        is_sensitive = max_sens >= 7
        return max(1, min(10, max_sens)), is_sensitive


# Singleton
_heuristic_scorer: Optional["HeuristicScorer"] = None


def get_heuristic_scorer() -> "HeuristicScorer":
    global _heuristic_scorer
    if _heuristic_scorer is None:
        _heuristic_scorer = HeuristicScorer()
    return _heuristic_scorer