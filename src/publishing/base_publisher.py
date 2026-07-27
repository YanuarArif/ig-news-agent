"""Abstract base class for all publishers (mock, telegram preview, instagram).

All publishers must implement the publish() method with the same signature
so they can be swapped via environment variable without changing pipeline code.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BasePublisher(ABC):
    """Abstract base publisher interface."""

    @abstractmethod
    def publish(
        self,
        image_path_or_url: str,
        caption: str,
        metadata: Optional[dict] = None
    ) -> dict:
        """Publish content (image + caption) to target platform.

        Args:
            image_path_or_url: Local file path (mock, telegram) or
                public URL (instagram, which requires hosted image).
            caption: Caption text to accompany the image.
            metadata: Optional extra data (source_url, score, etc.)

        Returns:
            Dict with keys:
                - status: "success" | "failed"
                - post_id: Platform-specific post identifier
                - mode: Publisher mode identifier ("mock", "telegram_preview", "instagram")
                - error: Error message if failed, None if success
                - url: Optional public URL to published post
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def mode(self) -> str:
        """Return publisher mode identifier."""
        raise NotImplementedError