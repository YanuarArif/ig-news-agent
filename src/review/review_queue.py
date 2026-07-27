"""Review queue for human-in-the-loop approval.

Manages pending posts waiting for manual review via Telegram.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List
import json
from pathlib import Path

from config.settings import get_settings

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    PUBLISHED = "published"


@dataclass
class ReviewItem:
    """Item in review queue."""
    id: str
    image_path: str
    caption: str
    summary: dict
    score_result: dict
    metadata: dict
    status: ReviewStatus = ReviewStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "image_path": self.image_path,
            "caption": self.caption,
            "summary": self.summary,
            "score_result": self.score_result,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewed_by": self.reviewed_by,
            "review_note": self.review_note,
        }


class ReviewQueue:
    """Queue for managing review items."""

    def __init__(self, storage_path: Path = Path("logs/review_queue.json")):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.items: List[ReviewItem] = []
        self._load()

    def _load(self):
        """Load queue from storage."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self.items = [ReviewItem(**item) for item in data]
            except Exception as e:
                logger.warning("Failed to load review queue: %s", e)
                self.items = []

    def _save(self):
        """Save queue to storage."""
        try:
            data = [item.to_dict() for item in self.items]
            self.storage_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            logger.warning("Failed to save review queue: %s", e)

    def add(self, item: ReviewItem) -> ReviewItem:
        """Add item to queue."""
        self.items.append(item)
        self._save()
        logger.info("Added to review queue: %s", item.id)
        return item

    def get_pending(self) -> List[ReviewItem]:
        """Get all pending items."""
        return [item for item in self.items if item.status == ReviewStatus.PENDING]

    def get_by_id(self, item_id: str) -> Optional[ReviewItem]:
        """Get item by ID."""
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def approve(self, item_id: str, reviewer: str, note: str = "") -> bool:
        """Approve item for publishing."""
        item = self.get_by_id(item_id)
        if item and item.status == ReviewStatus.PENDING:
            item.status = ReviewStatus.APPROVED
            item.reviewed_at = datetime.now(timezone.utc)
            item.reviewed_by = reviewer
            item.review_note = note
            self._save()
            logger.info("Approved: %s by %s", item_id, reviewer)
            return True
        return False

    def reject(self, item_id: str, reviewer: str, note: str = "") -> bool:
        """Reject item."""
        item = self.get_by_id(item_id)
        if item and item.status == ReviewStatus.PENDING:
            item.status = ReviewStatus.REJECTED
            item.reviewed_at = datetime.now(timezone.utc)
            item.reviewed_by = reviewer
            item.review_note = note
            self._save()
            logger.info("Rejected: %s by %s", item_id, reviewer)
            return True
        return False

    def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """Mark expired pending items."""
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        count = 0
        for item in self.items:
            if item.status == ReviewStatus.PENDING:
                age = now - item.created_at
                if age > timedelta(hours=max_age_hours):
                    item.status = ReviewStatus.EXPIRED
                    count += 1
        if count:
            self._save()
        return count


def get_review_queue() -> ReviewQueue:
    """Get global review queue instance."""
    raise NotImplementedError