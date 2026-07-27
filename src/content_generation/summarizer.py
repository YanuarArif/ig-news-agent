"""Meringkas & memparafrase berita jadi poin-poin untuk infografis,
menggunakan Claude API. TIDAK boleh copy-paste teks asli (hak cipta)."""

import json
import logging
from pathlib import Path

from src.scoring.llm_client import LLMClient

logger = logging.getLogger(__name__)
PROMPT_PATH = Path(__file__).parent / "prompts" / "summarize_prompt.txt"


class NewsSummarizer:
    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def summarize(self, news_title: str, news_body: str, source_name: str = "Media Indonesia",
                  category: str = "general", viral_potential: int = 5, credibility_score: int = 5) -> dict:
        user_prompt = (
            f"Judul: {news_title}\n\n"
            f"Isi berita:\n{news_body}\n\n"
            f"Sumber: {source_name}\n"
            f"Kategori: {category}\n"
            f"Skor viral: {viral_potential}/10\n"
            f"Skor kredibilitas: {credibility_score}/10"
        )
        raw = self.llm.complete(self.system_prompt, user_prompt, max_tokens=512)
        try:
            result = json.loads(raw)
            # Ensure required fields exist
            required = ["headline", "key_points", "category", "tone", "source_attribution"]
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
summarize_news = NewsSummarizer().summarize