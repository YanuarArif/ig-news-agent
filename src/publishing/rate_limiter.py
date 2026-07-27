"""Rate limiter for Instagram posting (max 25 posts per 24 hours).

Implements a sliding window rate limiter to enforce Instagram's
API limits. Uses local file storage for persistence across runs.
"""

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

RATE_LIMIT_FILE = Path("logs/rate_limit.json")
MAX_POSTS_PER_24H = 25
WINDOW_SECONDS = 24 * 60 * 60


class RateLimiter:
    """Enforce maximum posts per 24-hour sliding window."""

    def __init__(
        self,
        max_posts: int = MAX_POSTS_PER_24H,
        window_seconds: int = WINDOW_SECONDS,
        storage_path: Optional[Path] = None
    ):
        """Initialize rate limiter."""
        self.max_posts = max_posts
        self.window_seconds = window_seconds
        self.storage_path = storage_path or RATE_LIMIT_FILE
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        """Load timestamps from storage."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self.timestamps = [float(ts) for ts in data.get("timestamps", [])]
            except Exception as e:
                logger.warning("Failed to load rate limit data: %s", e)
                self.timestamps = []
        else:
            self.timestamps = []

    def _save(self):
        """Save timestamps to storage."""
        try:
            data = {"timestamps": self.timestamps}
            self.storage_path.write_text(json.dumps(data), encoding="utf-8")
        except Exception as e:
            logger.warning("Failed to save rate limit data: %s", e)

    def _clean_old(self, now: float):
        """Remove timestamps outside the window."""
        cutoff = now - self.window_seconds
        self.timestamps = [ts for ts in self.timestamps if ts > cutoff]

    def can_post(self) -> bool:
        """Check if a new post is allowed within rate limit."""
        now = time.time()
        self._clean_old(now)
        return len(self.timestamps) < self.max_posts

    def get_remaining(self) -> int:
        """Get remaining posts allowed in current window."""
        now = time.time()
        self._clean_old(now)
        return max(0, self.max_posts - len(self.timestamps))

    def get_reset_time(self) -> Optional[datetime]:
        """Get datetime when oldest post expires (window resets)."""
        if not self.timestamps:
            return None
        now = time.time()
        self._clean_old(now)
        if not self.timestamps:
            return None
        oldest = min(self.timestamps)
        return datetime.fromtimestamp(oldest + self.window_seconds, tz=timezone.utc)

    def record_post(self) -> bool:
        """Record a new post. Returns True if allowed, False if rate limited."""
        now = time.time()
        self._clean_old(now)

        if len(self.timestamps) >= self.max_posts:
            logger.warning("Rate limit exceeded: %d posts in 24h", len(self.timestamps))
            return False

        self.timestamps.append(now)
        self._save()
        logger.info("Post recorded. Total in 24h: %d", len(self.timestamps))
        return True

    def wait_if_needed(self) -> float:
        """Wait until a post slot is available. Returns wait time in seconds."""
        if self.can_post():
            return 0.0

        now = time.time()
        self._clean_old(now)
        if not self.timestamps:
            return 0.0

        oldest = min(self.timestamps)
        wait_time = (oldest + self.window_seconds) - now
        wait_time = max(0, wait_time)

        logger.info("Rate limited. Waiting %.0f seconds...", wait_time)
        time.sleep(wait_time)
        return wait_time


# Global instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def check_rate_limit() -> bool:
    """Convenience function to check if posting is allowed."""
    return get_rate_limiter().can_post()


def record_post() -> bool:
    """Convenience function to record a post."""
    return get_rate_limiter().record_post()