"""LLM provider abstraction layer.

Inspired by kotaemon's llms/ architecture — provider-agnostic interface
for chat completion with swappable backends.
"""

from __future__ import annotations

from hospital_ai.services.llm.base import BaseLLM, LLMResponse
from hospital_ai.services.llm.manager import LLMManager, get_llm_manager

__all__ = ["BaseLLM", "LLMResponse", "LLMManager", "get_llm_manager"]
