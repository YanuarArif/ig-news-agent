"""IG News Agent - Automated Instagram news content pipeline.

This package contains all core modules for the IG News Automation Agent:
- Ingestion: RSS/News API fetching, deduplication, freshness filtering
- Scoring: LLM-based viral potential, credibility, sensitivity scoring
- Content Generation: Summarization, caption writing, prompt templates
- Design: HTML template rendering to images via Playwright
- Storage: Cloudinary image upload
- Publishing: Multi-mode publisher (mock, telegram_preview, instagram)
- Review: Human-in-the-loop Telegram review queue
- Database: SQLAlchemy models and migrations
- Scheduler: APScheduler-based pipeline orchestration
"""

__version__ = "0.1.0"
__author__ = "IG News Agent Team"