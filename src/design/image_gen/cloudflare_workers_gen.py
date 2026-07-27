"""Cloudflare Workers AI image generator (Flux Schnell).

Connects to deployed Cloudflare Worker untuk generate image.
Cek quota sebelum generate - gagal kalau quota habis.
"""

import logging
import os
import time
from pathlib import Path
from typing import Optional

import requests

from src.design.image_gen.base_image_gen import BaseImageGen

logger = logging.getLogger(__name__)

# Default endpoint - override via env
DEFAULT_ENDPOINT = "https://cf-image-gen.<your-subdomain>.workers.dev"


class CloudflareWorkersImageGen(BaseImageGen):
    """Image generator via Cloudflare Workers AI (Flux Schnell)."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 2
    ):
        self.endpoint = (endpoint or os.getenv("CF_WORKERS_AI_ENDPOINT") or DEFAULT_ENDPOINT).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._quota_checked = False
        self._quota_available = True

        if "your-subdomain" in self.endpoint:
            raise ValueError(
                "CF_WORKERS_AI_ENDPOINT belum di-set di .env. "
                "Deploy worker dulu, lalu isi endpoint di .env"
            )

        logger.info(f"CloudflareWorkersImageGen initialized: {self.endpoint}")

    def _check_quota(self) -> bool:
        """Cek quota via health endpoint. Return True kalau tersedia."""
        if self._quota_checked:
            return self._quota_available

        try:
            resp = requests.get(f"{self.endpoint}/health", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self._quota_available = data.get("status") == "ok"
                self._quota_checked = True
                logger.info(f"Quota check: {'available' if self._quota_available else 'exhausted'}")
                return self._quota_available
        except Exception as e:
            logger.warning(f"Quota check failed, assuming available: {e}")
            self._quota_available = True
            self._quota_checked = True
            return True

        self._quota_available = False
        self._quota_checked = True
        return False

    def generate(self, prompt: str, output_path: str) -> str:
        """Generate image via Cloudflare Workers AI.

        Args:
            prompt: Prompt untuk generate (kategori berita, dll)
            output_path: Path file output (akan disimpan sebagai JPEG)

        Returns:
            Path file yang di-generate

        Raises:
            RuntimeError: Kalau quota habis atau generate gagal
        """
        # Cek quota dulu
        if not self._check_quota():
            raise RuntimeError(
                "Cloudflare Workers AI quota exhausted (10,000 neurons/day free tier). "
                "Upgrade ke Workers Paid plan atau tunggu reset 00:00 UTC."
            )

        # Safety suffix untuk news content
        safety_suffix = (
            ", abstract symbolic illustration, no realistic human faces, "
            "no specific real people, editorial illustration style, news infographic background"
        )
        safe_prompt = f"{prompt}{safety_suffix}"

        payload = {
            "prompt": safe_prompt,
            "width": 1024,
            "height": 1024,
            "steps": 4,
            "guidance_scale": 3.5
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.post(
                    f"{self.endpoint}/generate",
                    json=payload,
                    timeout=self.timeout,
                    headers={"Accept": "image/jpeg"}
                )

                if resp.status_code == 429:
                    # Quota exceeded dari worker
                    error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    raise RuntimeError(
                        "Cloudflare Workers AI quota exhausted (429). "
                        f"Worker response: {error_data.get('message', 'Rate limited')}"
                    )

                if resp.status_code == 400:
                    error_data = resp.json()
                    raise RuntimeError(f"Bad request: {error_data.get('error', 'Unknown error')}")

                resp.raise_for_status()

                # Save binary image
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(resp.content)

                logger.info(f"[CLOUDFLARE WORKERS AI] generated -> {output_path} ({len(resp.content)} bytes)")
                return output_path

            except requests.Timeout:
                last_error = "Request timeout"
                logger.warning(f"Attempt {attempt + 1} timeout, retrying...")
            except requests.RequestException as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
            except RuntimeError:
                raise  # Re-raise quota errors immediately

            if attempt < self.max_retries:
                time.sleep(2 ** attempt)  # Exponential backoff

        raise RuntimeError(f"Cloudflare Workers AI generation failed after {self.max_retries + 1} attempts: {last_error}")


# Convenience function untuk testing
def test_cloudflare_workers():
    """Quick test function."""
    gen = CloudflareWorkersImageGen()
    test_path = "tmp_design/test_cf_workers.jpg"
    return gen.generate("breaking_news urgent red alert background", test_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(test_cloudflare_workers())