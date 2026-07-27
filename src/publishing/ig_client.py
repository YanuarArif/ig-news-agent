"""Instagram Graph API publisher (stub until API access approved).

This class extends BasePublisher but raises NotImplementedError for
the actual Graph API calls until Instagram approves the app review.
The factory will instantiate this when PUBLISH_MODE=instagram.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from src.publishing.base_publisher import BasePublisher

logger = logging.getLogger(__name__)


class InstagramPublisher(BasePublisher):
    """Instagram Graph API publisher (implementation pending API approval)."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        business_account_id: Optional[str] = None,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
    ):
        """Initialize with Instagram credentials."""
        self.access_token = access_token or os.getenv("IG_ACCESS_TOKEN")
        self.business_account_id = business_account_id or os.getenv("IG_BUSINESS_ACCOUNT_ID")
        self.app_id = app_id or os.getenv("FB_APP_ID")
        self.app_secret = app_secret or os.getenv("FB_APP_SECRET")
        self.api_version = "v19.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

        if not self.access_token or not self.business_account_id:
            logger.warning(
                "InstagramPublisher initialized without credentials. "
                "IG_ACCESS_TOKEN and IG_BUSINESS_ACCOUNT_ID required for actual publishing."
            )

    @property
    def mode(self) -> str:
        return "instagram"

    def publish(
        self,
        image_path_or_url: str,
        caption: str,
        metadata: Optional[dict] = None
    ) -> dict:
        """Publish to Instagram via Graph API.

        Flow:
        1. Upload image to get media container ID (POST /{ig_user_id}/media)
        2. Publish container (POST /{ig_user_id}/media_publish)

        Currently raises NotImplementedError until API access is granted.
        """
        logger.warning("InstagramPublisher.publish() called but not implemented yet")
        raise NotImplementedError(
            "Instagram Graph API publishing not yet implemented. "
            "Requires: IG_ACCESS_TOKEN, IG_BUSINESS_ACCOUNT_ID, and approved app review. "
            "Set PUBLISH_MODE=mock or PUBLISH_MODE=telegram_preview for testing."
        )

    def _create_media_container(self, image_url: str, caption: str) -> str:
        """Step 1: Create media container. Returns container ID."""
        raise NotImplementedError("Instagram Graph API not yet implemented")

    def _publish_media_container(self, container_id: str) -> str:
        """Step 2: Publish media container. Returns post ID."""
        raise NotImplementedError("Instagram Graph API not yet implemented")

    def _get_ig_user_id(self) -> str:
        """Get Instagram Business Account ID."""
        return self.business_account_id


# Backwards compatibility
InstagramPublisher = InstagramPublisher