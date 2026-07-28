#!/usr/bin/env python
"""
Standalone test script for Cloudflare Workers AI image generation + Telegram send.

Theme: "cat in the park"
Does NOT interfere with main pipeline code.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

# Load .env first
load_dotenv(Path(__file__).parent / ".env")

from src.design.image_gen.cloudflare_workers_gen import CloudflareWorkersImageGen
from src.publishing.telegram_preview_publisher import TelegramPreviewPublisher


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def main():
    # Output path for generated image
    output_dir = Path(__file__).parent / "tmp_design"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "test_cat_in_park.jpg"

    # 1. Generate image via Cloudflare Workers AI
    logger.info("=" * 60)
    logger.info("Generating image: 'cat in the park'")
    logger.info("=" * 60)

    try:
        gen = CloudflareWorkersImageGen()
        logger.info(f"Using endpoint: {gen.endpoint}")

        prompt = (
            "A cute fluffy cat sitting on a park bench, "
            "green trees and grass background, "
            "sunlight filtering through leaves, "
            "peaceful afternoon atmosphere, "
            "high quality photo realistic, 8k"
        )

        saved_path = gen.generate(prompt, str(output_path))
        logger.info(f"✅ Image saved to: {saved_path}")
        logger.info(f"   File size: {Path(saved_path).stat().st_size / 1024:.1f} KB")

    except Exception as e:
        logger.error(f"❌ Image generation failed: {e}")
        return 1

    # 2. Send to Telegram
    logger.info("=" * 60)
    logger.info("Sending to Telegram...")
    logger.info("=" * 60)

    try:
        publisher = TelegramPreviewPublisher()
        caption = (
            "🐱 <b>Test: Cloudflare Workers AI + Telegram</b>\n\n"
            "Theme: Cat in the park\n"
            "Model: Flux Schnell (via Cloudflare Workers AI)\n"
            "Generated: Test script\n\n"
            "#test #cloudflare #ai #flux #cat"
        )

        result = publisher.publish(saved_path, caption)

        if result["status"] == "success":
            logger.info(f"✅ Telegram sent successfully!")
            logger.info(f"   Message ID: {result['post_id']}")
            logger.info(f"   Preview URL: {result['url']}")
        else:
            logger.error(f"❌ Telegram send failed: {result['error']}")
            return 1

    except Exception as e:
        logger.error(f"❌ Telegram publisher error: {e}")
        return 1

    logger.info("=" * 60)
    logger.info("🎉 ALL DONE - Check your Telegram chat!")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())