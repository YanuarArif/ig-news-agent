"""Cross-verification of news across multiple sources.

Verifies if a news story appears in multiple credible sources before
considering it verified. Uses keyword matching against known sources.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from src.ingestion.rss_fetcher import fetch_all_sources

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of cross-verification check."""
    is_verified: bool
    source_count: int
    sources: list[dict]
    confidence: float
    reasoning: str
    cross_verification_score: int = 0  # 1-10: Multi-source confirmation strength

    def __post_init__(self):
        """Calculate cross_verification_score based on source count and confidence."""
        if self.is_verified:
            # Base score from source count (max 6 for 3+ sources)
            base_score = min(self.source_count * 2, 6)
            # Add confidence factor (max 4)
            confidence_bonus = int(self.confidence * 4)
            self.cross_verification_score = min(base_score + confidence_bonus, 10)
        else:
            self.cross_verification_score = 0

    def to_dict(self) -> dict:
        return {
            "is_verified": self.is_verified,
            "source_count": self.source_count,
            "sources": self.sources,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "cross_verification_score": self.cross_verification_score,
        }


class CrossVerifier:
    """Verify news across multiple sources."""

    def __init__(self, min_sources: int = 2):
        """Initialize with minimum source requirement."""
        self.min_sources = min_sources
        self._source_cache = None

    def _get_source_pool(self) -> list[dict]:
        """Get pool of news items from all RSS sources for verification."""
        if self._source_cache is None:
            try:
                self._source_cache = fetch_all_sources()
                # Convert RawNewsItem to dict
                self._source_cache = [item.to_dict() if hasattr(item, 'to_dict') else item for item in self._source_cache]
                logger.info(f"Loaded {len(self._source_cache)} items for cross-verification")
            except Exception as e:
                logger.warning(f"Failed to fetch source pool: {e}")
                self._source_cache = []
        return self._source_cache

    def verify(self, title: str, content: str, source_url: str = "") -> VerificationResult:
        """Verify a news item by searching for corroborating sources.

        Args:
            title: News title
            content: News content/summary
            source_url: Original source URL (excluded from verification)

        Returns:
            VerificationResult with verification status
        """
        # Extract key terms from title for matching
        key_terms = self._extract_key_terms(title)
        
        if not key_terms:
            return VerificationResult(
                is_verified=False,
                source_count=0,
                sources=[],
                confidence=0.0,
                reasoning="No key terms extracted for verification"
            )

        # Search in source pool
        sources = self._get_source_pool()
        matches = []
        
        for item in sources:
            if item.get("source_url") == source_url:
                continue  # Skip original source
            
            similarity = self._calculate_similarity(title, content, item)
            if similarity > 0.4:  # Threshold for considering it a match
                matches.append({
                    "title": item.get("title", ""),
                    "source": item.get("source_name", ""),
                    "similarity": similarity,
                    "url": item.get("link", ""),
                })

        # Sort by similarity
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        matches = matches[:5]  # Top 5
        
        is_verified = len(matches) >= self.min_sources
        confidence = min(1.0, len(matches) / self.min_sources * 0.8 + (matches[0]["similarity"] if matches else 0) * 0.2)
        
        if is_verified:
            reasoning = f"Found {len(matches)} corroborating sources with key terms: {key_terms[:3]}"
        else:
            reasoning = f"Only {len(matches)} sources found (need {self.min_sources}). Key terms: {key_terms[:3]}"

        return VerificationResult(
            is_verified=is_verified,
            source_count=len(matches),
            sources=matches,
            confidence=round(confidence, 2),
            reasoning=reasoning
        )

    def verify_batch(self, items: list[dict]) -> list[VerificationResult]:
        """Verify multiple items."""
        return [self.verify(item.get("title", ""), item.get("summary", ""), item.get("link", "")) for item in items]

    def _extract_key_terms(self, title: str) -> list[str]:
        """Extract key terms from title for matching."""
        import re
        # Remove common stop words
        stop_words = {'dan', 'di', 'ke', 'dari', 'untuk', 'dengan', 'pada', 'yang', 'atau', 'adalah', 'akan', 'sudah', 'telah', 'ini', 'itu', 'the', 'a', 'an', 'is', 'of', 'to', 'in', 'for', 'on', 'with', 'as', 'by'}
        words = re.findall(r'\b\w+\b', title.lower())
        return [w for w in words if len(w) > 3 and w not in stop_words]

    def _calculate_similarity(self, title1: str, content1: str, item2: dict) -> float:
        """Calculate similarity between two news items."""
        from rapidfuzz import fuzz
        
        title2 = item2.get("title", "")
        content2 = item2.get("summary", "")
        
        # Title similarity (weight: 70%)
        title_sim = fuzz.token_sort_ratio(title1, title2) / 100.0
        
        # Content similarity (weight: 30%)
        content_sim = fuzz.token_sort_ratio(content1[:200], content2[:200]) / 100.0 if content1 and content2 else 0
        
        return title_sim * 0.7 + content_sim * 0.3


def get_cross_verifier(min_sources: int = 2) -> CrossVerifier:
    """Get configured cross verifier instance."""
    return CrossVerifier(min_sources)


# Convenience function
_verifier_instance = None

def check_cross_verification(title: str, source_name: str = "") -> VerificationResult:
    """Convenience function to check cross-verification."""
    global _verifier_instance
    if _verifier_instance is None:
        _verifier_instance = CrossVerifier()
    return _verifier_instance.verify(title, "", source_name)