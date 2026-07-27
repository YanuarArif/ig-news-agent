"""Fetch entries from RSS feeds using feedparser.

Provides functionality to parse RSS/Atom feeds and extract structured
news items with title, link, summary, published date, and source metadata.
"""

import feedparser
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from config.settings import get_settings


@dataclass
class RawNewsItem:
    """Raw news item extracted from RSS feed."""
    title: str
    link: str
    summary: str
    published_at: datetime
    source_name: str
    source_url: str
    category: Optional[str] = None
    author: Optional[str] = None
    guid: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "link": self.link,
            "summary": self.summary,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "category": self.category,
            "author": self.author,
            "guid": self.guid,
        }


def parse_rss_entry(entry: feedparser.FeedParserDict, source_name: str, source_url: str) -> RawNewsItem:
    """Parse a single feedparser entry into RawNewsItem."""
    raise NotImplementedError


def fetch_rss_feed(url: str, source_name: str, category: Optional[str] = None) -> list[RawNewsItem]:
    """Fetch and parse a single RSS feed URL.

    Args:
        url: RSS feed URL
        source_name: Human-readable source name
        category: Optional category override

    Returns:
        List of RawNewsItem objects
    """
    raise NotImplementedError


def fetch_all_sources() -> list[RawNewsItem]:
    """Fetch news from all enabled RSS sources in config.

    Returns:
        Combined list of RawNewsItem from all sources
    """
    raise NotImplementedError