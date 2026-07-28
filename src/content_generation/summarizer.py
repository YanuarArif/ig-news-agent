"""Meringkas & memparafrase berita jadi poin-poin untuk infografis,
menggunakan Nemotron API. TIDAK boleh copy-paste teks asli (hak cipta)."""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional

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
        
        # Try LLM with JSON mode
        try:
            raw = self.llm.complete(
                self.system_prompt, 
                user_prompt, 
                max_tokens=512,
                response_format={"type": "json_object"}
            )
            result = self._parse_json_response(raw)
            
            # Ensure required fields exist
            required = ["headline", "key_points", "category", "tone", "source_attribution"]
            for field in required:
                if field not in result or not result[field]:
                    raise ValueError(f"Missing or empty required field: {field}")
            
            # Ensure source_attribution is present
            if "source_attribution" not in result:
                result["source_attribution"] = f"Sumber: {summary.get('source_name', 'Media Indonesia')}"
            
            return result
            
        except Exception as e:
            logger.warning(f"LLM summarization failed, using fallback: {e}")
            return self._fallback_summary(news_title, news_body, source_name, category)

    def _parse_json_response(self, raw: str) -> Dict[str, Any]:
        """Parse JSON from LLM response with multiple fallback strategies."""
        # Strategy 1: Direct parse
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON object with regex
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Strategy 3: Find first { to last }
        first_brace = raw.find('{')
        last_brace = raw.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(raw[first_brace:last_brace + 1])
            except json.JSONDecodeError:
                pass
        
        # Strategy 4: Try to clean and fix common JSON issues
        cleaned = self._clean_json(raw)
        if cleaned:
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Failed to parse JSON from LLM response: {raw[:200]}...")

    def _clean_json(self, text: str) -> Optional[str]:
        """Try to fix common JSON issues."""
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Fix trailing commas
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        
# Fix unescaped newlines in strings
        text = re.sub(r'(?<!\\)\n', '\\n', text)

        return text.strip()

    def _fallback_summary(self, news_title: str, news_body: str, source_name: str, category: str) -> dict:
        """Generate a simple summary when LLM completely fails."""
        # Simple extraction of key points from body
        sentences = re.split(r'[.!?]+', news_body)
        key_points = [s.strip() for s in sentences[:3] if len(s.strip()) > 20]

        # Generate headline from title
        headline = news_title[:60] if len(news_title) <= 60 else news_title[:57] + "..."

        return {
            "headline": headline,
            "key_points": [p for p in key_points[:3] if p],
            "category": "general",
            "tone": "informative",
            "source_attribution": f"Sumber: {source_name}"
        }


# Backwards compatibility
summarize_news = NewsSummarizer().summarize