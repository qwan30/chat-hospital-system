"""Base LLM interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, List, Optional


@dataclass
class LLMMessage:
    """A single message in a chat conversation."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM completion."""
    text: str
    model: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a chat completion.

        Args:
            messages: List of conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            LLMResponse with the generated text.
        """

    @abstractmethod
    async def stream(
        self,
        messages: List[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream a chat completion token by token.

        Args:
            messages: List of conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Yields:
            Individual tokens as strings.
        """

    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider (e.g. 'openai', 'ollama')."""

    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier."""
