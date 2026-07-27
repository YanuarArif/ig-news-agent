"""Wrapper generic untuk memanggil Claude API. Dipakai bersama oleh
news_scorer.py, summarizer.py, dan caption_writer.py supaya retry &
error handling konsisten di satu tempat."""

import os
import logging

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-3-5-sonnet-20241022"  # cek docs.claude.com untuk model terbaru


class LLMClient:
    """Wrapper Anthropic Claude API dengan retry & rate limit handling."""

    def __init__(self, model: str = DEFAULT_MODEL):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY belum diisi di .env")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        """Panggil Claude API dengan system + user prompt, return teks."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


# Backwards compatibility alias
AnthropicClient = LLMClient