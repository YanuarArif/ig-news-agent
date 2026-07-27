"""SQLAlchemy database models.

Defines ORM models for NewsItem, Post, ScoreLog, ReviewLog.
"""

from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class ReviewStatus(PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    PUBLISHED = "published"


class PostStatus(PyEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class NewsItem(Base):
    """Raw news item from ingestion."""
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guid = Column(String(255), unique=True, index=True, nullable=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=False)
    summary = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    source_name = Column(String(200), nullable=False)
    source_url = Column(String(1000), nullable=True)
    category = Column(String(100), nullable=True)
    author = Column(String(200), nullable=True)
    raw_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    scores = relationship("ScoreLog", back_populates="news_item", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="news_item", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_news_items_source_published", "source_name", "published_at"),
    )


class ScoreLog(Base):
    """Scoring results for a news item."""
    __tablename__ = "score_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_item_id = Column(Integer, ForeignKey("news_items.id", ondelete="CASCADE"), nullable=False, index=True)

    viral_potential = Column(Integer, nullable=False)  # 1-10
    credibility_score = Column(Integer, nullable=False)  # 1-10
    sensitivity_score = Column(Integer, nullable=False)  # 1-10
    is_sensitive = Column(Boolean, nullable=False, default=False)
    is_verified_multi_source = Column(Boolean, nullable=False, default=False)
    cross_verification_score = Column(Integer, nullable=False)  # 1-10
    overall_score = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)
    llm_model = Column(String(100), nullable=True)
    raw_response = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    news_item = relationship("NewsItem", back_populates="scores")


class Post(Base):
    """Published or scheduled post."""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_item_id = Column(Integer, ForeignKey("news_items.id", ondelete="CASCADE"), nullable=False, index=True)

    image_path = Column(String(1000), nullable=True)
    image_url = Column(String(1000), nullable=True)
    caption = Column(Text, nullable=False)
    hashtags = Column(JSONB, nullable=True)  # list of strings
    summary_data = Column(JSONB, nullable=True)  # SummaryResult dict

    status = Column(SQLEnum(PostStatus), default=PostStatus.DRAFT, nullable=False, index=True)
    publisher_mode = Column(String(50), nullable=False)  # mock, telegram_preview, instagram
    platform_post_id = Column(String(200), nullable=True, index=True)  # IG media ID, Telegram message_id, mock ID
    platform_url = Column(String(1000), nullable=True)

    scheduled_at = Column(DateTime(timezone=True), nullable=True, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    news_item = relationship("NewsItem", back_populates="posts")
    reviews = relationship("ReviewLog", back_populates="post", cascade="all, delete-orphan")


class ReviewLog(Base):
    """Human review log for posts."""
    __tablename__ = "review_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    reviewer = Column(String(200), nullable=True)  # Telegram user ID
    note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    post = relationship("Post", back_populates="reviews")


# Indexes
Index("ix_posts_status_scheduled", Post.status, Post.scheduled_at)
Index("ix_posts_publisher_mode", Post.publisher_mode)