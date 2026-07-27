"""Telegram bot for human-in-the-loop review.

Sends pending posts to Telegram for manual approve/reject before publishing.
Uses python-telegram-bot for handling callbacks.
"""

import logging
from typing import Optional

from config.settings import get_settings

logger = logging.getLogger(__name__)


class ReviewTelegramBot:
    """Telegram bot for review queue management."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None
    ):
        """Initialize bot with credentials."""
        self.bot_token = bot_token or get_settings().telegram.bot_token
        self.chat_id = chat_id or get_settings().telegram.chat_id
        self.application = None

        if not self.bot_token or not self.chat_id:
            logger.warning("ReviewTelegramBot initialized without credentials")

    async def start(self):
        """Start the bot."""
        raise NotImplementedError

    async def stop(self):
        """Stop the bot."""
        raise NotImplementedError

    async def send_for_review(self, post_data: dict) -> int:
        """Send post preview to review chat with approve/reject buttons.

        Returns:
            Message ID for tracking
        """
        raise NotImplementedError

    async def handle_callback(self, update, context):
        """Handle approve/reject callbacks."""
        raise NotImplementedError


def get_review_bot() -> ReviewTelegramBot:
    """Get configured review bot instance."""
    raise NotImplementedError