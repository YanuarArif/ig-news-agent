"""Mock publisher for local testing.

Simulates publishing without calling any external API.
Saves publish metadata as JSON to mock_output/ for auditing.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.publishing.base_publisher import BasePublisher

logger = logging.getLogger(__name__)

MOCK_OUTPUT_DIR = Path("mock_output")


class MockPublisher(BasePublisher):
    """Mock publisher that logs and saves to local JSON files."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize mock publisher."""
        self.output_dir = output_dir or MOCK_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"MockPublisher initialized, output dir: {self.output_dir}")

    @property
    def mode(self) -> str:
        return "mock"

    def publish(
        self,
        image_path_or_url: str,
        caption: str,
        metadata: Optional[dict] = None
    ) -> dict:
        """Simulate publishing by saving metadata to JSON file."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        post_id = f"mock_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        record = {
            "post_id": post_id,
            "image": image_path_or_url,
            "caption": caption,
            "timestamp": timestamp,
            "mode": "mock",
            "metadata": metadata or {},
        }

        out_path = self.output_dir / f"{post_id}.json"
        out_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        logger.info("[MOCK POST] %s -> %s", post_id, out_path)
        logger.info("[MOCK POST] caption preview: %s...", caption[:80])

        return {
            "status": "success",
            "post_id": post_id,
            "mode": "mock",
            "error": None,
            "url": f"file://{out_path.absolute()}",
        }


# Backwards compatibility
MockPublisher = MockPublisher