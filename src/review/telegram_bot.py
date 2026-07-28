"""Telegram bot for human-in-the-loop review.

Sends pending posts to Telegram for manual approve/reject before publishing.
Uses python-telegram-bot for handling callbacks.
"""

import asyncio
import logging
import os
from typing import Optional, Callable, Awaitable

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from src.review.review_queue import get_review_queue, ReviewStatus

logger = logging.getLogger(__name__)


class ReviewTelegramBot:
    """Telegram bot for review queue management."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None
    ):
        """Initialize bot with credentials."""
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.application: Optional[Application] = None
        self._review_callback: Optional[Callable[[str, bool, str], Awaitable[None]]] = None

        if not self.bot_token or not self.chat_id:
            logger.warning("ReviewTelegramBot initialized without credentials")

    async def start(self, review_callback: Optional[Callable[[str, bool, str], Awaitable[None]]] = None):
        """Start the bot."""
        if not self.bot_token:
            logger.error("Cannot start bot: TELEGRAM_BOT_TOKEN not set")
            return

        self._review_callback = review_callback
        
        self.application = Application.builder().token(self.bot_token).build()
        
        # Handlers
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("help", self._cmd_help))
        self.application.add_handler(CommandHandler("status", self._cmd_status))
        self.application.add_handler(CommandHandler("pending", self._cmd_pending))
        
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Review Telegram bot started")

    async def stop(self):
        """Stop the bot."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Review Telegram bot stopped")

    async def send_for_review(self, post_data: dict) -> Optional[int]:
        """Send post preview to review chat with approve/reject buttons.

        Args:
            post_data: Dict with image_path, caption, summary, score_result, id

        Returns:
            Message ID for tracking, or None if failed
        """
        if not self.application or not self.chat_id:
            logger.error("Bot not ready or chat_id not set")
            return None

        item_id = post_data.get("id", "unknown")
        image_path = post_data.get("image_path")
        caption = post_data.get("caption", "")
        summary = post_data.get("summary", {})
        score = post_data.get("score_result", {})

        # Build preview message
        headline = summary.get("headline", "No headline")
        key_points = summary.get("key_points", [])
        source = summary.get("source_attribution", "Unknown source")
        
        # Build inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{item_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{item_id}"),
            ],
            [
                InlineKeyboardButton("📝 Edit Caption", callback_data=f"edit:{item_id}"),
                InlineKeyboardButton("🔄 Regenerate", callback_data=f"regen:{item_id}"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Truncate caption for preview
        preview_caption = caption[:1000] + ("..." if len(caption) > 1000 else "")

        try:
            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as photo:
                    message = await self.application.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=photo,
                        caption=(
                            f"📰 <b>Review Required</b>\n\n"
                            f"<b>ID:</b> {item_id}\n"
                            f"<b>Headline:</b> {headline}\n\n"
                            f"<b>Preview:</b>\n{preview_caption}\n\n"
                            f"<b>Source:</b> {source}\n"
                            f"<b>Scores:</b> Viral: {score.get('viral_potential', 'N/A')}/10 | "
                            f"Cred: {score.get('credibility_score', 'N/A')}/10 | "
                            f"Overall: {score.get('overall_score', 'N/A')}/10"
                        ),
                        parse_mode="HTML",
                        reply_markup=reply_markup
                    )
            else:
                message = await self.application.bot.send_message(
                    chat_id=self.chat_id,
                    text=(
                        f"📰 <b>Review Required (No Image)</b>\n\n"
                        f"<b>ID:</b> {item_id}\n"
                        f"<b>Headline:</b> {headline}\n\n"
                        f"<b>Preview:</b>\n{preview_caption}\n\n"
                        f"<b>Source:</b> {source}\n"
                        f"<b>Scores:</b> Viral: {score.get('viral_potential', 'N/A')}/10 | "
                        f"Cred: {score.get('credibility_score', 'N/A')}/10 | "
                        f"Overall: {score.get('overall_score', 'N/A')}/10"
                    ),
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            
            logger.info("Sent for review: %s (msg_id: %s)", item_id, message.message_id)
            return message.message_id

        except Exception as e:
            logger.exception("Failed to send for review: %s", e)
            return None

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle approve/reject callbacks."""
        query = update.callback_query
        await query.answer()
        
        if not query.data:
            return
        
        action, item_id = query.data.split(":", 1)
        user = query.from_user
        reviewer = f"{user.first_name} {user.last_name or ''}".strip()
        if user.username:
            reviewer += f" (@{user.username})"

        queue = get_review_queue()
        
        if action == "approve":
            success = queue.approve(item_id, reviewer)
            if success:
                await query.edit_message_caption(
                    caption=query.message.caption + "\n\n✅ <b>APPROVED</b> by " + reviewer,
                    parse_mode="HTML"
                )
                if self._review_callback:
                    await self._review_callback(item_id, True, reviewer)
            else:
                await query.answer("❌ Already processed or not found", show_alert=True)

        elif action == "reject":
            success = queue.reject(item_id, reviewer, "Rejected via Telegram")
            if success:
                await query.edit_message_caption(
                    caption=query.message.caption + "\n\n❌ <b>REJECTED</b> by " + reviewer,
                    parse_mode="HTML"
                )
                if self._review_callback:
                    await self._review_callback(item_id, False, reviewer)
            else:
                await query.answer("❌ Already processed or not found", show_alert=True)

        elif action == "edit":
            await query.answer("Edit mode not yet implemented", show_alert=True)

        elif action == "regen":
            await query.answer("Regeneration not yet implemented", show_alert=True)

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        await update.message.reply_text(
            "🤖 <b>IG News Agent Review Bot</b>\n\n"
            "Commands:\n"
            "/pending - Show pending items\n"
            "/status - Show queue status\n"
            "/help - Show this help",
            parse_mode="HTML"
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await self._cmd_start(update, context)

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        queue = get_review_queue()
        pending = queue.get_pending()
        total = len(queue.items)
        approved = sum(1 for i in queue.items if i.status == ReviewStatus.APPROVED)
        rejected = sum(1 for i in queue.items if i.status == ReviewStatus.REJECTED)
        
        await update.message.reply_text(
            f"📊 <b>Queue Status</b>\n\n"
            f"Total: {total}\n"
            f"Pending: {len(pending)}\n"
            f"Approved: {approved}\n"
            f"Rejected: {rejected}",
            parse_mode="HTML"
        )

    async def _cmd_pending(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pending command."""
        queue = get_review_queue()
        pending = queue.get_pending()
        
        if not pending:
            await update.message.reply_text("No pending items")
            return
        
        for item in pending[:5]:
            headline = item.summary.get("headline", "No headline")
            await update.message.reply_text(
                f"📋 <b>{item.id}</b>\n"
                f"Headline: {headline[:80]}\n"
                f"Created: {item.created_at.strftime('%Y-%m-%d %H:%M')}",
                parse_mode="HTML"
            )


# Global instance
_review_bot_instance: Optional[ReviewTelegramBot] = None


def get_review_bot() -> ReviewTelegramBot:
    """Get configured review bot instance."""
    global _review_bot_instance
    if _review_bot_instance is None:
        _review_bot_instance = ReviewTelegramBot()
    return _review_bot_instance


async def run_review_bot(
    review_callback: Optional[Callable[[str, bool, str], Awaitable[None]]] = None
):
    """Run the review bot (blocking)."""
    bot = get_review_bot()
    await bot.start(review_callback)
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Shutting down review bot...")
    finally:
        await bot.stop()