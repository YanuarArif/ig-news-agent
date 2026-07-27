"""Telegram preview publisher for visual QA.

Sends rendered infographic + caption to a Telegram chat/channel
for real visual preview before Instagram publishing.
This uses real Telegram Bot API calls (not mock).
"""

import logging
import os
from pathlib import Path
from typing import Optional

import requests

from src.publishing.base_publisher import BasePublisher

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendPhoto"


class TelegramPreviewPublisher(BasePublisher):
    """Publisher that sends to Telegram for visual preview."""

    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None
    ):
        """Initialize with bot token and chat ID from env or params."""
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_PREVIEW_CHAT_ID")

        if not self.token or not self.chat_id:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN and TELEGRAM_PREVIEW_CHAT_ID must be set "
                "in .env or passed to constructor for telegram_preview mode"
            )

        logger.info(f"TelegramPreviewPublisher initialized for chat_id: {self.chat_id}")

    @property
    def mode(self) -> str:
        return "telegram_preview"

    def publish(
        self,
        image_path_or_url: str,
        caption: str,
        metadata: Optional[dict] = None
    ) -> dict:
        """Send image + caption to Telegram chat.

        Args:
            image_path_or_url: Local file path (preferred) or HTTP URL.
            caption: Caption text (max 1024 chars for Telegram).
            metadata: Optional extra data.

        Returns:
            Dict with status, post_id (message_id), mode, error, url.
        """
        url = TELEGRAM_API_BASE.format(token=self.token)

        # Telegram caption limit is 1024 chars
        telegram_caption = caption[:1020] + ("..." if len(caption) > 1024 else "")

        try:
            # Determine if local file or URL
            path = Path(image_path_or_url)
            if path.exists() and path.is_file():
                # Local file - upload as multipart
                with open(path, "rb") as img_file:
                    files = {"photo": img_file}
                    data = {
                        "chat_id": self.chat_id,
                        "caption": telegram_caption,
                        "parse_mode": "HTML",
                    }
                    response = requests.post(url, data=data, files=files, timeout=30)
            else:
                # Assume it's a URL - send as photo with URL
                data = {
                    "chat_id": self.chat_id,
                    "photo": image_path_or_url,
                    "caption": telegram_caption,
                    "parse_mode": "HTML",
                }
                response = requests.post(url, data=data, timeout=30)

            response.raise_for_status()
            result = response.json()

            if not result.get("ok"):
                raise RuntimeError(f"Telegram API error: {result.get('description')}")

            message_id = result["result"]["message_id"]
            logger.info("[TELEGRAM PREVIEW] sent, message_id=%s", message_id)

            return {
                "status": "success",
                "post_id": str(message_id),
                "mode": "telegram_preview",
                "error": None,
                "url": f"https://t.me/c/{str(self.chat_id).replace('-100', '')}/{message_id}",
            }

        except Exception as exc:
            logger.exception("[TELEGRAM PREVIEW] failed to send")
            return {
                "status": "failed",
                "post_id": None,
                "mode": "telegram_preview",
                "error": str(exc),
                "url": None,
            }


# Backwards compatibility
TelegramPreviewPublisher = TelegramPreviewPublisher