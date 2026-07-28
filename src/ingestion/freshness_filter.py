"""Filter news items by freshness (age since publication).

Removes stale news items based on publication timestamp compared to
current time, with configurable maximum age thresholds.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class FreshnessResult:
    """Result of freshness check."""
    is_fresh: bool
    age_hours: float
    published_at: datetime
    reason: Optional[str] = None


class FreshnessFilter:
    """Filter news items by age/freshness."""

    def __init__(
        self,
        max_age_hours: int = 24,
        preferred_max_age_hours: int = 6
    ):
        """Initialize with age thresholds."""
        self.max_age_hours = max_age_hours
        self.preferred_max_age_hours = preferred_max_age_hours

    def check_freshness(self, published_at: datetime) -> FreshnessResult:
        """Check if a news item is fresh enough.

        Args:
            published_at: Publication timestamp (timezone-aware or naive)

        Returns:
            FreshnessResult with details
        """
        # Handle naive datetime - assume UTC
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        age = now - published_at
        age_hours = age.total_seconds() / 3600
        
        if age_hours <= self.preferred_max_age_hours:
            return FreshnessResult(True, age_hours, published_at, "fresh")
        elif age_hours <= self.max_age_hours:
            return FreshnessResult(True, age_hours, published_at, "acceptable")
        else:
            return FreshnessResult(False, age_hours, published_at, f"stale ({age_hours:.1f}h > {self.max_age_hours}h)")

    def filter_batch(self, items: list) -> list:
        """Filter a batch of items, keeping only fresh ones.

        Args:
            items: List of items with published_at attribute (datetime or ISO string)

        Returns:
            Filtered list of fresh items (converted to dict if needed)
        """
        filtered = []
        for item in items:
            # Convert to dict if it's a RawNewsItem
            if hasattr(item, 'to_dict'):
                item = item.to_dict()
            
            published_at = item.get('published_at')
            if isinstance(published_at, str):
                try:
                    published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                except Exception:
                    continue
            
            if not isinstance(published_at, datetime):
                continue
                
            result = self.check_freshness(published_at)
            if result.is_fresh:
                filtered.append(item)
            else:
                print(f"  [FRESHNESS] Skipped stale: {item.get('title', '')[:60]} ({result.age_hours:.1f}h old)")
        return filtered

    def get_age_hours(self, published_at: datetime) -> float:
        """Calculate age in hours from published_at to now."""
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - published_at).total_seconds() / 3600


def get_freshness_filter(max_age_hours: int = 24, preferred_max_age_hours: int = 6) -> FreshnessFilter:
    """Get freshness filter with configured thresholds."""
    return FreshnessFilter(max_age_hours, preferred_max_age_hours)