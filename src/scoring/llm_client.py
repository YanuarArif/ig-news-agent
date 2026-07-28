"""Wrapper generic untuk memanggil NVIDIA Nemotron LLM API (OpenAI-compatible).
Dipakai bersama oleh news_scorer.py, summarizer.py, dan caption_writer.py
supaya retry & error handling konsisten di satu tempat."""

import os
import logging
from typing import Optional, Dict, Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# NVIDIA Nemotron 3 Ultra model di build.nvidia.com
DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


class LLMClient:
    """Wrapper NVIDIA Nemotron API (OpenAI-compatible) dengan retry & rate limit handling."""

    def __init__(self, model: str = DEFAULT_MODEL):
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("NVIDIA_API_KEY belum diisi di .env (dapatkan dari https://build.nvidia.com)")
        self.client = OpenAI(
            base_url=NVIDIA_BASE_URL,
            api_key=api_key,
        )
        self.model = model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        response_format: Optional[Dict[str, str]] = None,
        temperature: float = 0.3,
    ) -> str:
        """Panggil Nemotron API dengan system + user prompt, return teks."""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=response_format or {"type": "text"},
        )
        return response.choices[0].message.content or ""

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> str:
        """Panggil LLM dengan response_format json_object (enforced JSON)."""
        return self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            temperature=temperature,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def complete_batch(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        temperature: float = 0.2,
    ) -> str:
        """Batch version with higher token limit, returns JSON array."""
        return self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            temperature=temperature,
        )


# Backwards compatibility alias
NemotronClient = LLMClient