"""Cloudinary client for image upload and management.

Handles uploading rendered infographic images to Cloudinary
and returning public URLs for publishing.
"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
from pathlib import Path
from typing import Optional

from config.settings import get_settings


class CloudinaryClient:
    """Cloudinary storage client."""

    def __init__(self):
        """Initialize with credentials from settings."""
        settings = get_settings()
        cloudinary.config(
            cloud_name=settings.cloudinary.cloud_name,
            api_key=settings.cloudinary.api_key,
            api_secret=settings.cloudinary.api_secret,
            secure=True
        )

    def upload_image(
        self,
        file_path: Path,
        public_id: Optional[str] = None,
        folder: str = "ig_news_agent",
        transformation: Optional[dict] = None
    ) -> dict:
        """Upload image to Cloudinary.

        Args:
            file_path: Local path to image file
            public_id: Optional custom public ID
            folder: Cloudinary folder
            transformation: Optional transformation dict

        Returns:
            Dict with url, public_id, width, height, format, bytes
        """
        raise NotImplementedError

    def upload_bytes(
        self,
        image_bytes: bytes,
        public_id: Optional[str] = None,
        folder: str = "ig_news_agent"
    ) -> dict:
        """Upload image from bytes."""
        raise NotImplementedError

    def delete_image(self, public_id: str) -> dict:
        """Delete image from Cloudinary."""
        raise NotImplementedError

    def get_image_info(self, public_id: str) -> dict:
        """Get image metadata."""
        raise NotImplementedError


def get_cloudinary_client() -> CloudinaryClient:
    """Get configured Cloudinary client."""
    raise NotImplementedError