"""Deduplicate news items using fuzzy matching against database history.

Uses rapidfuzz for efficient fuzzy string matching to detect duplicate
or near-duplicate news stories across sources and time.
"""

from dataclasses import dataclass
from typing import Optional

from rapidfuzz import fuzz, process


@dataclass
class DedupResult:
    """Result of deduplication check."""
    is_duplicate: bool
    matched_item: Optional[dict]
    similarity_score: float
    matched_title: Optional[str] = None


class NewsDeduplicator:
    """Deduplicate incoming news against existing database records."""

    def __init__(self, similarity_threshold: float = 0.85):
        """Initialize with similarity threshold (0.0-1.0)."""
        self.similarity_threshold = similarity_threshold

    def check_duplicate(
        self,
        title: str,
        existing_items: list[dict]
    ) -> DedupResult:
        """Check if a news title is duplicate of any existing item.

        Args:
            title: New item title to check
            existing_items: List of existing items (dict with title)

        Returns:
            DedupResult with match info
        """
        if not existing_items:
            return DedupResult(False, None, 0.0, None)
        
        best_match, score = self.find_best_match(title, existing_items)
        is_dup = score >= self.similarity_threshold
        
        return DedupResult(
            is_duplicate=is_dup,
            matched_item=best_match,
            similarity_score=score / 100.0,  # rapidfuzz returns 0-100
            matched_title=best_match.get('title') if best_match else None
        )

    def find_best_match(
        self,
        title: str,
        existing_items: list[dict]
    ) -> tuple[Optional[dict], float]:
        """Find best matching existing item using fuzzy matching.

        Returns:
            Tuple of (matched_item, similarity_score) or (None, 0.0)
        """
        if not existing_items:
            return None, 0.0
        
        titles = [item.get('title', '') for item in existing_items]
        result = process.extractOne(title, titles, scorer=fuzz.token_sort_ratio)
        
        if result:
            match_title, score, idx = result
            return existing_items[idx], score
        return None, 0.0

    def filter_batch(
        self,
        new_items: list[dict],
        existing_items: list[dict]
    ) -> list[dict]:
        """Filter a batch of new items, removing duplicates.

        Args:
            new_items: List of new items (with title attribute)
            existing_items: Existing items from database

        Returns:
            List of non-duplicate new items
        """
        filtered = []
        for item in new_items:
            result = self.check_duplicate(item.get('title', ''), existing_items)
            if not result.is_duplicate:
                filtered.append(item)
            else:
                print(f"  [DEDUP] Skipped duplicate: {item.get('title', '')[:60]} (score: {result.similarity_score:.2f})")
        return filtered


def get_deduplicator(similarity_threshold: float = 0.85) -> NewsDeduplicator:
    """Get deduplicator instance with configured threshold."""
    return NewsDeduplicator(similarity_threshold)