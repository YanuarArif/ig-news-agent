"""Application settings loaded from environment variables and config files.

This module provides a centralized Settings class that loads all configuration
from environment variables (via python-dotenv) and YAML config files.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_yaml_config(filename: str) -> dict:
    """Load YAML config file from config directory."""
    config_path = BASE_DIR / "config" / filename
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


@dataclass
class DatabaseSettings:
    """Database connection settings."""
    url: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/ig_news_agent")


@dataclass
class CloudinarySettings:
    """Cloudinary cloud storage settings."""
    cloud_name: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    api_key: str = os.getenv("CLOUDINARY_API_KEY", "")
    api_secret: str = os.getenv("CLOUDINARY_API_SECRET", "")


@dataclass
class InstagramSettings:
    """Instagram Graph API settings."""
    access_token: str = os.getenv("IG_ACCESS_TOKEN", "")
    business_account_id: str = os.getenv("IG_BUSINESS_ACCOUNT_ID", "")
    app_id: str = os.getenv("FB_APP_ID", "")
    app_secret: str = os.getenv("FB_APP_SECRET", "")
    api_version: str = "v19.0"


@dataclass
class TelegramSettings:
    """Telegram bot settings."""
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    preview_chat_id: str = os.getenv("TELEGRAM_PREVIEW_CHAT_ID", "")


@dataclass
class LLMSSettings:
    """LLM API settings."""
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.3


@dataclass
class ScoringSettings:
    """Scoring thresholds and weights."""
    viral_threshold: int = int(os.getenv("POST_SCORE_THRESHOLD_VIRAL", "7"))
    credibility_threshold: int = int(os.getenv("POST_SCORE_THRESHOLD_CREDIBILITY", "6"))
    sensitivity_categories: list = field(default_factory=lambda: [
        "SARA", "kematian", "bencana", "politik_hukum_belum_inkrah"
    ])


@dataclass
class PostingSettings:
    """Posting rules and limits."""
    max_posts_per_day: int = int(os.getenv("MAX_POSTS_PER_DAY", "10"))
    min_interval_minutes: int = 30
    max_posts_per_hour: int = 3
    skip_sensitive: bool = True


@dataclass
class PublishingSettings:
    """Publishing configuration loaded from YAML."""
    mode: str = os.getenv("PUBLISH_MODE", "mock")
    instagram: dict = field(default_factory=dict)
    telegram_preview: dict = field(default_factory=dict)
    mock: dict = field(default_factory=dict)

    def __post_init__(self):
        config = _load_yaml_config("publishing.yaml")
        self.instagram = config.get("publishing", {}).get("instagram", {})
        self.telegram_preview = config.get("publishing", {}).get("telegram_preview", {})
        self.mock = config.get("publishing", {}).get("mock", {})


@dataclass
class SchedulerSettings:
    """Scheduler configuration loaded from YAML."""
    config: dict = field(default_factory=dict)

    def __post_init__(self):
        self.config = _load_yaml_config("scheduler.yaml")


@dataclass
class Settings:
    """Main application settings container."""
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    cloudinary: CloudinarySettings = field(default_factory=CloudinarySettings)
    instagram: InstagramSettings = field(default_factory=InstagramSettings)
    telegram: TelegramSettings = field(default_factory=TelegramSettings)
    llm: LLMSSettings = field(default_factory=LLMSSettings)
    scoring: ScoringSettings = field(default_factory=ScoringSettings)
    posting: PostingSettings = field(default_factory=PostingSettings)
    publishing: PublishingSettings = field(default_factory=PublishingSettings)
    scheduler: SchedulerSettings = field(default_factory=SchedulerSettings)

    review_mode: str = os.getenv("REVIEW_MODE", "manual")

    def validate_required(self) -> list[str]:
        """Validate required settings are present. Returns list of missing keys."""
        missing = []
        if not self.llm.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")
        if not self.database.url or "postgresql://user:pass" in self.database.url:
            missing.append("DATABASE_URL")
        if self.publishing.mode == "telegram_preview":
            if not self.telegram.bot_token:
                missing.append("TELEGRAM_BOT_TOKEN")
            if not self.telegram.preview_chat_id:
                missing.append("TELEGRAM_PREVIEW_CHAT_ID")
        if self.publishing.mode == "instagram":
            if not self.instagram.access_token:
                missing.append("IG_ACCESS_TOKEN")
            if not self.instagram.business_account_id:
                missing.append("IG_BUSINESS_ACCOUNT_ID")
        if not self.cloudinary.cloud_name:
            missing.append("CLOUDINARY_CLOUD_NAME")
        return missing


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get global settings instance (for dependency injection)."""
    return settings