from __future__ import annotations

from typing import Optional

"""Tests for the ValidatedSentenceStreamer service."""

from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest


@dataclass
class SseEvent:
    type: str
    content: Optional[str] = None
    sequence: Optional[int] = None
    validation_mode: Optional[str] = None


async def async_tokens(text: str) -> AsyncIterator[str]:
    """Simulate an LLM provider yielding space-separated tokens."""
    for word in text.split(" "):
        yield word + " "


async def streamer(provider, evidence, context=None) -> AsyncIterator[SseEvent]:
    from hospital_ai.services.validated_stream import ValidatedSentenceStreamer

    s = ValidatedSentenceStreamer()
    async for event in s.events(provider, evidence, context):
        yield event


@pytest.mark.asyncio
async def test_sse_never_emits_unvalidated_provider_tokens() -> None:
    """Validated streamer must not leak unvalidated content (e.g. wrong dose)."""
    provider = async_tokens("Unsupported 5000 mg. Supported 500 mg [E1].")
    events = [event async for event in streamer(provider, evidence={"E1": "Dose 500 mg"})]
    tokens = [event for event in events if event.type == "token"]
    # The '5000' sentence should fail validation and be refused/repaired
    assert "5000" not in "".join(event.content for event in tokens)
    # Sequence numbers must be monotonically increasing from 1
    assert [event.sequence for event in tokens] == list(range(1, len(tokens) + 1))
    # Terminal event order
    assert [event.type for event in events if event.type != "token"] == [
        "status",
        "metadata",
        "citations",
        "graph_explanation",
        "done",
    ]


@pytest.mark.asyncio
async def test_validated_chunks_emit_validation_mode() -> None:
    """Each token event should carry validation_mode='sentence_buffered'."""
    provider = async_tokens("Patient is stable [E1].")
    events = [event async for event in streamer(provider, evidence={"E1": "Patient is stable"})]
    tokens = [event for event in events if event.type == "token"]
    assert len(tokens) >= 1
    for token in tokens:
        assert token.validation_mode == "sentence_buffered"


@pytest.mark.asyncio
async def test_streamer_emits_empty_citations_and_graph_explanation() -> None:
    """Even with no explicit citations data, citations and graph_explanation must be emitted."""
    provider = async_tokens("Patient is stable [E1].")
    events = [event async for event in streamer(provider, evidence={"E1": "Patient is stable"})]
    event_types = [event.type for event in events]
    assert "citations" in event_types
    assert "graph_explanation" in event_types


@pytest.mark.asyncio
async def test_streamer_handles_trailing_fragment() -> None:
    """Text without a trailing period should still be emitted after validation."""
    provider = async_tokens("Patient is stable [E1]")
    events = [event async for event in streamer(provider, evidence={"E1": "Patient is stable"})]
    tokens = [event for event in events if event.type == "token"]
    full_text = "".join(event.content for event in tokens)
    assert "stable" in full_text


@pytest.mark.asyncio
async def test_sequence_starts_at_one() -> None:
    """Sequence numbering must start at 1, not 0."""
    provider = async_tokens("Dose is 500 mg [E1].")
    events = [event async for event in streamer(provider, evidence={"E1": "Dose 500 mg"})]
    tokens = [event for event in events if event.type == "token"]
    assert tokens[0].sequence == 1
