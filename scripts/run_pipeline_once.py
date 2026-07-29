#!/usr/bin/env python
"""
CLI script untuk menjalankan satu siklus pipeline penuh secara manual.

Pipeline: Ingest RSS → Dedup → Score → Summarize → Caption → Image Gen → Compositor → Publish

Usage:
    python -m scripts.run_pipeline_once
    python scripts/run_pipeline_once.py  # (may need PYTHONPATH=.)
"""

import sys
from pathlib import Path

# Add src to path - MUST be first before any other imports
src_path = Path(__file__).parent.parent.resolve() / "src"
sys.path.insert(0, str(src_path))
print(f"[DEBUG] Added to sys.path: {src_path.resolve()}")
print(f"[DEBUG] sys.path[0]: {sys.path[0]}")

import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def load_env():
    """Load environment variables from .env file."""
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded .env from {env_path}")
    else:
        logger.warning(".env file not found, using system env vars only")


def run_pipeline():
    """Execute one full pipeline cycle."""
    load_env()
    
    # Import all components (lazy import to avoid circular deps)
    from src.ingestion.rss_fetcher import fetch_rss_feeds
    from src.ingestion.deduplicator import get_deduplicator
    from src.ingestion.freshness_filter import get_freshness_filter
    from src.scoring.news_scorer import score_news
    from src.content_generation.summarizer import NewsSummarizer
    from src.content_generation.caption_writer import CaptionWriter
    from src.design.compositor import build_infographic
    from src.publishing.publisher_factory import get_publisher
    from src.review.review_queue import ReviewQueue
    
    # Settings
    from config.settings import get_settings
    settings = get_settings()
    
    logger.info("=" * 60)
    logger.info("STARTING PIPELINE CYCLE")
    logger.info("=" * 60)
    
    # 1. INGESTION - Fetch from RSS feeds
    logger.info("[1/8] Fetching RSS feeds...")
    try:
        raw_items = fetch_rss_feeds(settings.scoring.rss_feeds if hasattr(settings.scoring, 'rss_feeds') else [])
        logger.info(f"  Fetched {len(raw_items)} raw items")
    except Exception as e:
        logger.error(f"  RSS fetch failed: {e}")
        # Use sample data for testing
        raw_items = [
            {
                "title": "Gempa M5.8 Guncang Jawa Tengah",
                "body": "Gempa berkekuatan M 5.8 melanda Jawa Tengah pukul 14:30 WIB. Epusentrum di laut 45 km barat daya Kebumen. Terjadi 3 korban meninggal dan 15 luka-luka. Ratusan rumah rusak, evakuasi darurat berlangsung.",
                "source_name": "BMKG",
                "source_url": "https://bmkg.go.id/gempa",
                "published_at": "2024-01-15T14:30:00Z",
                "category": "breaking_news"
            },
            {
                "title": "Film Indonesia Baru Raih Penghargaan Internasional",
                "body": "Film terbaru sutradara muda Indonesia berhasil meraih penghargaan di Festival Film Cannes. Film ini bercerita tentang kehidupan pedesaan dengan pendekatan visual yang memukau.",
                "source_name": "Detik",
                "source_url": "https://detik.com/hiburan",
                "published_at": "2024-01-15T10:00:00Z",
                "category": "entertainment"
            }
        ]
        logger.info(f"  Using {len(raw_items)} sample items for testing")
    
    # Convert RawNewsItem dataclass to dict if needed
    raw_items = [item.to_dict() if hasattr(item, 'to_dict') else item for item in raw_items]
    
    # 2. DEDUPLICATION
    logger.info("[2/8] Deduplicating...")
    deduplicator = get_deduplicator()
    unique_items = deduplicator.filter_batch(raw_items, [])
    # Ensure dicts
    unique_items = [item.to_dict() if hasattr(item, 'to_dict') else item for item in unique_items]
    logger.info(f"  {len(unique_items)} unique items after dedup")
    
    # 3. FRESHNESS FILTER
    logger.info("[3/8] Filtering freshness...")
    freshness_filter = get_freshness_filter()
    fresh_items = freshness_filter.filter_batch(unique_items)
    # Ensure dicts
    fresh_items = [item.to_dict() if hasattr(item, 'to_dict') else item for item in fresh_items]
    logger.info(f"  {len(fresh_items)} fresh items")
    
    if not fresh_items:
        logger.warning("No fresh items to process, exiting")
        return
    
    # 4. SCORING
    logger.info("[4/8] Scoring news items...")
    scored_items = []
    # Force convert ALL items to dicts before scoring
    fresh_items = [item.to_dict() if hasattr(item, 'to_dict') else item for item in fresh_items]
    logger.info(f"Converted {len(fresh_items)} items to dicts for scoring")
    for item in fresh_items:
        try:
            score = score_news(item)
            score_dict = score.to_dict()
            item["score"] = score_dict
            if score_dict.get("viral_potential", 0) >= settings.scoring.viral_threshold:
                scored_items.append(item)
                logger.info(f"  ✓ '{item['title'][:50]}' - viral:{score_dict.get('viral_potential')} cred:{score_dict.get('credibility_score')}")
            else:
                logger.info(f"  ✗ '{item['title'][:50]}' - below threshold")
        except Exception as e:
            logger.error(f"  Scoring failed for '{item['title'][:50]}': {e}")
    
    logger.info(f"  {len(scored_items)} items passed scoring threshold")
    
    # Sort by combined viral + credibility score (descending) and take top 2
    scored_items.sort(
        key=lambda x: (
            x["score"].get("viral_potential", 0) + 
            x["score"].get("credibility_score", 0)
        ),
        reverse=True
    )
    MAX_POSTS_PER_RUN = 2
    scored_items = scored_items[:MAX_POSTS_PER_RUN]
    logger.info(f"  📌 Taking top {MAX_POSTS_PER_RUN} items by viral+credibility score")
    
    if not scored_items:
        logger.warning("No items passed scoring, exiting")
        return
    
    # 5. CONTENT GENERATION - Summarize
    logger.info("[5/8] Generating summaries...")
    summarizer = NewsSummarizer()
    for item in scored_items:
        try:
            summary = summarizer.summarize(
                news_title=item["title"],
                news_body=item.get("summary", item.get("body", "")),
                source_name=item.get("source_name", "Unknown"),
                category=item.get("category", "general"),
                viral_potential=item["score"].get("viral_potential", 5),
                credibility_score=item["score"].get("credibility_score", 5)
            )
            item["summary"] = summary
            logger.info(f"  ✓ '{item['title'][:40]}' → {summary['headline'][:50]}")
        except Exception as e:
            logger.error(f"  Summarize failed: {e}")
            item["summary"] = None
    
    # 6. CONTENT GENERATION - Caption
    logger.info("[6/8] Writing captions...")
    caption_writer = CaptionWriter()
    for item in scored_items:
        if not item.get("summary"):
            continue
        try:
            caption_data = caption_writer.write_caption(
                summary=item["summary"],
                source_name=item.get("source_name", "Unknown"),
                viral_potential=item["score"].get("viral_potential", 5),
                credibility_score=item["score"].get("credibility_score", 5)
            )
            item["caption_data"] = caption_data
            logger.info(f"  ✓ Caption: {caption_data['caption'][:60]}...")
        except Exception as e:
            logger.error(f"  Caption failed: {e}")
            item["caption_data"] = None
    
    # 7. DESIGN - Build infographic
    logger.info("[7/8] Building infographics...")
    for item in scored_items:
        if not item.get("summary") or not item.get("caption_data"):
            continue
        try:
            image_path = build_infographic(
                summary=item["summary"],
                source_attribution=item["caption_data"]["source_attribution"]
            )
            item["image_path"] = image_path
            logger.info(f"  ✓ Generated: {Path(image_path).name}")
        except Exception as e:
            logger.error(f"  Infographic failed: {e}")
            item["image_path"] = None
    
    # 8. PUBLISH / REVIEW
    logger.info("[8/8] Publishing / Queue for review...")
    
    publisher = get_publisher()
    review_queue = ReviewQueue()
    
    review_mode = os.getenv("REVIEW_MODE", "manual")
    
    for item in scored_items:
        if not item.get("image_path") or not item.get("caption_data"):
            continue
        
        caption_text = item["caption_data"]["full_text"]
        
        if review_mode == "manual":
            # Queue for human review
            review_id = review_queue.add(
                title=item["summary"]["headline"],
                image_path=item["image_path"],
                caption=caption_text,
                score=item["score"],
                source=item.get("source_name", "Unknown")
            )
            logger.info(f"  📋 Queued for review: {review_id}")
        else:
            # Auto publish
            try:
                result = publisher.publish(item["image_path"], caption_text)
                if result["status"] == "success":
                    logger.info(f"  ✅ Published: {result['post_id']} ({result['mode']})")
                else:
                    logger.error(f"  ❌ Publish failed: {result.get('error')}")
            except Exception as e:
                logger.error(f"  ❌ Publish exception: {e}")
    
    logger.info("=" * 60)
    logger.info("PIPELINE CYCLE COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()