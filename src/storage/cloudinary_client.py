"""Cloudinary client for image upload and management.

Handles uploading rendered infographic images to Cloudinary
and returning public URLs for publishing.
"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
from pathlib import Path
from typing import Optional, Dict, Any

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
        transformation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload image to Cloudinary.

        Args:
            file_path: Local path to image file
            public_id: Optional custom public ID
            folder: Cloudinary folder
            transformation: Optional transformation dict

        Returns:
            Dict with url, public_id, width, height, format, bytes
        """
        options: Dict[str, Any] = {
            "folder": folder,
            "resource_type": "image",
        }
        if public_id:
            options["public_id"] = public_id
        if transformation:
            options["transformation"] = transformation
        
        result = cloudinary.uploader.upload(str(file_path), **options)
        
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "width": result.get("width"),
            "height": result.get("height"),
            "format": result.get("format"),
            "bytes": result.get("bytes"),
        }

    def upload_bytes(
        self,
        image_bytes: bytes,
        public_id: Optional[str] = None,
        folder: str = "ig_news_agent"
    ) -> Dict[str, Any]:
        """Upload image from bytes."""
        options = {
            "folder": folder,
            "resource_type": "image",
        }
        if public_id:
            options["public_id"] = public_id
        
        result = cloudinary.uploader.upload(image_bytes, **options)
        
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "width": result.get("width"),
            "height": result.get("height"),
            "format": result.get("format"),
            "bytes": result.get("bytes"),
        }

    def delete_image(self, public_id: str) -> Dict[str, Any]:
        """Delete image from Cloudinary."""
        result = cloudinary.uploader.destroy(public_id)
        return {"result": result.get("result"), "public_id": public_id}

    def get_image_info(self, public_id: str) -> Dict[str, Any]:
        """Get image metadata."""
        result = cloudinary.api.resource(public_id)
        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "width": result.get("width"),
            "height": result.get("height"),
            "format": result.get("format"),
            "bytes": result.get("bytes"),
            "created_at": result.get("created_at"),
        }


def get_cloudinary_client() -> CloudinaryClient:
    """Get configured Cloudinary client."""
    return CloudinaryClient()