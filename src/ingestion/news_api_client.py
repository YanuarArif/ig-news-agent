"""Wrapper client for third-party News API (generic interface).

Provides an abstract interface for fetching news from REST APIs like NewsAPI.org,
with support for different API providers through a common interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from config.settings import get_settings


@dataclass
class NewsAPIItem:
    """Normalized news item from News API."""
    title: str
    url: str
    description: str
    published_at: datetime
    source_name: str
    source_url: str
    category: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None


class NewsAPIClient(ABC):
    """Abstract base class for News API clients."""

    @abstractmethod
    def fetch_top_headlines(
        self,
        country: str = "id",
        category: str = "general",
        page_size: int = 20
    ) -> list[NewsAPIItem]:
        """Fetch top headlines from the API."""
        raise NotImplementedError

    @abstractmethod
    def fetch_everything(
        self,
        query: str,
        language: str = "id",
        page_size: int = 20
    ) -> list[NewsAPIItem]:
        """Search for articles matching query."""
        raise NotImplementedError


class NewsAPIOrgClient(NewsAPIClient):
    """Client for NewsAPI.org (requires API key)."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from settings or parameter."""
        raise NotImplementedError

    def fetch_top_headlines(
        self,
        country: str = "id",
        category: str = "general",
        page_size: int = 20
    ) -> list[NewsAPIItem]:
        raise NotImplementedError

    def fetch_everything(
        self,
        query: str,
        language: str = "id",
        page_size: int = 20
    ) -> list[NewsAPIItem]:
        raise NotImplementedError


def get_news_api_client() -> Optional[NewsAPIClient]:
    """Factory function to get configured News API client.

    Returns None if no API key is configured.
    """
    raise NotImplementedError