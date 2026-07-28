"""Menulis caption Instagram + hashtag berdasarkan ringkasan berita,
menggunakan Nemotron API."""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional

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
        
        # Try LLM with JSON mode first
        try:
            raw = self.llm.complete(
                self.system_prompt, 
                user_prompt, 
                max_tokens=400, 
                response_format={"type": "json_object"}
            )
            result = self._parse_json_response(raw)
            
            # Validate required fields
            required = ["caption", "hashtags", "cta", "full_text", "character_count"]
            for field in ["caption", "hashtags", "cta", "full_text"]:
                if field not in result or not result[field]:
                    raise ValueError(f"Missing or empty required field: {field}")
            
            # Ensure character_count is present
            if "character_count" not in result:
                result["character_count"] = len(result.get("full_text", ""))
            
            return result
            
        except Exception as e:
            logger.warning(f"LLM caption generation failed, using fallback: {e}")
            return self._fallback_caption(summary, source_name)

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

    def _fallback_caption(self, summary: dict, source_name: str) -> dict:
        """Generate a simple caption template when LLM completely fails."""
        headline = summary.get('headline', 'Berita Teknologi')
        key_points = summary.get('key_points', [])
        source_attr = summary.get('source_attribution', f'Sumber: {source_name}')
        category = summary.get('category', 'tech')
        
        # Build simple caption
        points_text = "\n".join([f"• {p}" for p in key_points[:3]])
        caption = f"{summary.get('headline', 'Berita Teknologi')}\n\n{points_text}"
        
        # Generate relevant hashtags
        hashtags = self._generate_hashtags(summary.get('category', 'tech'))
        
        cta = "Simpan & bagikan agar lebih banyak orang tahu! 📲"
        full_text = f"{caption}\n\n{' '.join(hashtags)}\n\nSimpan & bagikan agar lebih banyak orang tahu! 📲\n\nSumber: {source_name}"
        
        return {
            "caption": caption,
            "hashtags": hashtags,
            "cta": "Simpan & bagikan agar lebih banyak orang tahu! 📲",
            "full_text": full_text,
            "character_count": len(full_text),
            "source_attribution": f"Sumber: {source_name}"
        }

    def _generate_hashtags(self, category: str) -> list:
        """Generate relevant hashtags based on category."""
        base_tags = ["#teknologi", "#indonesia", "#berita", "#update", "#viral"]
        category_tags = {
            "tech": ["#teknologi", "#ai", "#gadget", "#startup", "#inovasi", "#digital"],
            "general": ["#berita", "#indonesia", "#update", "#viral", "#trending"],
            "entertainment": ["#hiburan", "#selebriti", "#film", "#music", "#kpop"],
            "sports": ["#olahraga", "#sepakbola", "#badminton", "#atlet"],
            "health": ["#kesehatan", "#tips", "#wellness", "#covid19"],
            "business": ["#bisnis", "#ekonomi", "#investasi", "#startup"],
        }
        tags = base_tags + category_tags.get(category, [])
        return tags[:15]  # Limit to 15 tags


# Backwards compatibility
write_instagram_caption = CaptionWriter().write_caption