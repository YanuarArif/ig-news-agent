"""Menulis caption Instagram + hashtag berdasarkan ringkasan berita,
menggunakan Claude API."""

import json
import logging
from pathlib import Path

from src.scoring.llm_client import LLMClient

logger = logging.getLogger(__name__)
PROMPT_PATH = Path(__file__).parent / "prompts" / "caption_prompt.txt"


class CaptionWriter:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def write_caption(self, summary: dict, source_name: str = "Media Indonesia",
                      viral_potential: int = 5, credibility_score: int = 5) -> dict:
        key_points = "; ".join(summary.get("key_points", []))
        user_prompt = (
            f"Headline: {summary.get('headline', '')}\n"
            f"Key Points: {key_points}\n"
            f"Category: {summary.get('category', 'general')}\n"
            f"Tone: {summary.get('tone', 'informative')}\n"
            f"Source: {summary.get('source_attribution', f'Sumber: {source_name}')}\n"
            f"Viral Score: {viral_potential}/10\n"
            f"Credibility: {credibility_score}/10"
        )
        raw = self.llm.complete(self.system_prompt, user_prompt, max_tokens=400)
        try:
            result = json.loads(raw)
            # Ensure required fields
            required = ["caption", "hashtags", "cta", "full_text", "character_count"]
            for field in required:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            return result
        except json.JSONDecodeError:
            logger.error("Gagal parse JSON dari LLM: %s", raw)
            raise
        except ValueError as e:
            logger.error("Validasi gagal: %s", e)
            raise


# Backwards compatibility
write_instagram_caption = CaptionWriter().write_caption