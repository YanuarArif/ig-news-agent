"""Publisher factory: selects active publisher based on PUBLISH_MODE env var.

This is the ONLY place that needs to change when switching between
mock, telegram_preview, and instagram modes.
"""

import os
import logging

from src.publishing.base_publisher import BasePublisher
from src.publishing.mock_publisher import MockPublisher
from src.publishing.telegram_preview_publisher import TelegramPreviewPublisher

logger = logging.getLogger(__name__)


def get_publisher() -> BasePublisher:
    """Get publisher instance based on PUBLISH_MODE environment variable.

    Returns:
        BasePublisher instance appropriate for current mode.

    Raises:
        ValueError: If PUBLISH_MODE is unknown.
    """
    mode = os.getenv("PUBLISH_MODE", "mock").lower()

    if mode == "mock":
        logger.info("Publisher factory: returning MockPublisher")
        return MockPublisher()

    elif mode == "telegram_preview":
        logger.info("Publisher factory: returning TelegramPreviewPublisher")
        return TelegramPreviewPublisher()

    elif mode == "instagram":
        logger.info("Publisher factory: returning InstagramPublisher")
        # Lazy import to avoid circular dependency
        from src.publishing.ig_client import InstagramPublisher
        return InstagramPublisher()

    else:
        raise ValueError(
            f"Unknown PUBLISH_MODE: '{mode}'. "
            "Valid values: mock | telegram_preview | instagram"
        )


# For testing
__all__ = ["get_publisher"]