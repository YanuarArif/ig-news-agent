"""Generic LLM client wrapper for Claude/OpenAI APIs.

Provides a unified interface for calling LLM APIs with retry logic,
rate limiting, and structured response parsing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from config.settings import get_settings


@dataclass
class LLMResponse:
    """Structured LLM response."""
    content: str
    model: str
    usage: Optional[dict] = None
    raw_response: Optional[Any] = None


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate completion from prompt."""
        raise NotImplementedError

    @abstractmethod
    def complete_structured(
        self,
        prompt: str,
        schema: dict,
        system_prompt: Optional[str] = None,
    ) -> dict:
        """Generate structured JSON response matching schema."""
        raise NotImplementedError


class AnthropicClient(LLMClient):
    """Anthropic Claude API client."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key."""
        raise NotImplementedError

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        raise NotImplementedError

    def complete_structured(
        self,
        prompt: str,
        schema: dict,
        system_prompt: Optional[str] = None,
    ) -> dict:
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """OpenAI GPT API client."""

    def __init__(self, api_key: Optional[str] = None):
        raise NotImplementedError

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        raise NotImplementedError

    def complete_structured(
        self,
        prompt: str,
        schema: dict,
        system_prompt: Optional[str] = None,
    ) -> dict:
        raise NotImplementedError


def get_llm_client(provider: str = "anthropic") -> LLMClient:
    """Factory function to get configured LLM client."""
    raise NotImplementedError