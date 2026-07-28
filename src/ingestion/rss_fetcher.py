"""Fetch entries from RSS feeds using feedparser.

Provides functionality to parse RSS/Atom feeds and extract structured
news items with title, link, summary, published date, and source metadata.
"""

import feedparser
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from pathlib import Path
import yaml

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


def _parse_published_date(entry) -> Optional[datetime]:
    """Parse published date from feedparser entry."""
    for attr in ('published_parsed', 'updated_parsed', 'created_parsed'):
        if hasattr(entry, attr) and getattr(entry, attr):
            parsed = getattr(entry, attr)
            try:
                return datetime(*parsed[:6])
            except Exception:
                continue
    return None


def _clean_html(text: str) -> str:
    """Basic HTML tag removal."""
    import re
    return re.sub(r'<[^>]+>', '', text).strip()


def parse_rss_entry(entry: feedparser.FeedParserDict, source_name: str, source_url: str) -> RawNewsItem:
    """Parse a single feedparser entry into RawNewsItem."""
    published_at = _parse_published_date(entry)
    
    summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
    summary = _clean_html(summary)
    
    guid = getattr(entry, 'guid', None) or getattr(entry, 'id', None) or getattr(entry, 'link', None)
    
    author = getattr(entry, 'author', None)
    
    category = None
    if hasattr(entry, 'tags') and entry.tags:
        category = entry.tags[0].get('term', None)
    
    return RawNewsItem(
        title=getattr(entry, 'title', 'No Title').strip(),
        link=getattr(entry, 'link', ''),
        summary=summary,
        published_at=published_at or datetime.now(),
        source_name=source_name,
        source_url=source_url,
        category=category,
        author=author,
        guid=guid,
    )


def fetch_rss_feed(url: str, source_name: str, category: Optional[str] = None) -> list[RawNewsItem]:
    """Fetch and parse a single RSS feed URL.

    Args:
        url: RSS feed URL
        source_name: Human-readable source name
        category: Optional category override

    Returns:
        List of RawNewsItem objects
    """
    feed = feedparser.parse(url)
    
    if feed.bozo:
        print(f"Warning: Feed parsing issue for {url}: {feed.bozo_exception}")
    
    items = []
    for entry in feed.entries:
        try:
            item = parse_rss_entry(entry, source_name, url)
            if category:
                item.category = category
            items.append(item)
        except Exception as e:
            print(f"Error parsing entry from {url}: {e}")
            continue
    
    return items


def fetch_all_sources() -> list[RawNewsItem]:
    """Fetch news from all enabled RSS sources in config/sources.yaml.

    Returns:
        Combined list of RawNewsItem from all sources
    """
    all_items = []
    
    sources_file = Path(__file__).parent.parent.parent / "config" / "sources.yaml"
    
    if not sources_file.exists():
        print(f"Sources config not found: {sources_file}")
        return []
    
    with open(sources_file) as f:
        data = yaml.safe_load(f)
        sources = data.get('rss_feeds', [])
    
    for source in sources:
        if not source.get('enabled', True):
            continue
        url = source.get('url')
        name = source.get('name', url)
        category = source.get('category')
        if url:
            items = fetch_rss_feed(url, name, category)
            all_items.extend(items)
            print(f"Fetched {len(items)} items from {name}")
    
    return all_items


def fetch_rss_feeds(sources: list = None) -> list[dict]:
    """Fetch RSS feeds and return as list of dicts (pipeline compatible)."""
    if sources:
        all_items = []
        for src in sources:
            items = fetch_rss_feed(src.get('url', ''), src.get('name', ''), src.get('category'))
            all_items.extend(items)
        return [item.to_dict() for item in all_items]
    else:
        items = fetch_all_sources()
        return [item.to_dict() for item in items]