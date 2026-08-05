"""Validated sentence streaming service.

Buffers raw LLM provider tokens privately until each complete sentence
passes claim validation.  Only validated content is yielded to the SSE
transport, ensuring no unverified clinical claims reach the wire.
"""

from __future__ import annotations

import logging
import re
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any, Optional

from hospital_ai.services.claim_validation import ClaimValidator, ValidationContext

logger = logging.getLogger(__name__)

# ── Sentence boundary utilities ──────────────────────────────────────────

_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")


def split_complete_sentences(buffer: str) -> tuple[list[str], str]:
    """Split *buffer* into (complete_sentences, remaining_fragment).

    A sentence is considered complete when it ends with '.', '!', or '?'
    followed by whitespace (or end-of-buffer for trailing periods).
    """
    parts = _SENTENCE_END_RE.split(buffer)
    if len(parts) <= 1:
        # Check if the buffer itself ends with sentence-ending punctuation
        stripped = buffer.rstrip()
        if stripped and stripped[-1] in ".!?":
            return [buffer], ""
        return [], buffer

    # All parts except the last are complete sentences
    complete = parts[:-1]
    remainder = parts[-1]
    # If remainder ends with sentence-ending punctuation, it's also complete
    if remainder.rstrip() and remainder.rstrip()[-1] in ".!?":
        complete.append(remainder)
        remainder = ""
    return complete, remainder


def visual_chunks(sentence: str) -> list[str]:
    """Break a validated sentence into small visual chunks for the SSE stream.

    Yields word-level chunks to maintain a streaming feel in the UI,
    even though validation happened at the sentence level.
    """
    parts = sentence.split(" ")
    result = []
    for i, part in enumerate(parts):
        if i < len(parts) - 1:
            result.append(part + " ")
        else:
            result.append(part)
    return [p for p in result if p]


# ── Data types ───────────────────────────────────────────────────────────


@dataclass
class ValidatedChunk:
    """A single validated text fragment ready for SSE emission."""

    sequence: int
    content: str
    validation_mode: str
    validation_passed: bool = True


@dataclass
class SseEvent:
    """An SSE event emitted by the ValidatedSentenceStreamer."""

    type: str
    content: Optional[str] = None
    sequence: Optional[int] = None
    validation_mode: Optional[str] = None
    data: Any = None
    validation_passed: Optional[bool] = None


# ── Streamer ─────────────────────────────────────────────────────────────

_SAFE_REFUSAL = "This information could not be verified against the available evidence."


class ValidatedSentenceStreamer:
    """Buffer provider tokens, validate complete sentences, yield only safe output."""

    def __init__(self) -> None:
        self.validator = ClaimValidator()

    async def validated_chunks(
        self,
        provider_tokens: AsyncIterator[str],
        evidence: Mapping[str, str],
        context: Optional[ValidationContext],
        sentence_guardrail: Optional[Callable[[str], Awaitable[Optional[str]]]] = None,
    ) -> AsyncIterator[ValidatedChunk]:
        """Core generator: validate sentences, yield visual chunks."""
        buffer = ""
        sequence = 0
        ctx = context or ValidationContext()

        async for raw_token in provider_tokens:
            buffer += raw_token
            complete, buffer = split_complete_sentences(buffer)
            for sentence in complete:
                async for chunk in self._validate_and_chunk(
                    sentence,
                    evidence,
                    ctx,
                    sequence,
                    sentence_guardrail,
                ):
                    sequence = chunk.sequence
                    yield chunk

        # Handle any trailing fragment
        if buffer.strip():
            async for chunk in self._validate_and_chunk(buffer, evidence, ctx, sequence, sentence_guardrail):
                sequence = chunk.sequence
                yield chunk

    async def _validate_and_chunk(
        self,
        sentence: str,
        evidence: Mapping[str, str],
        context: ValidationContext,
        current_sequence: int,
        sentence_guardrail: Optional[Callable[[str], Awaitable[Optional[str]]]] = None,
    ) -> AsyncIterator[ValidatedChunk]:
        """Validate a sentence and yield visual chunks if it passes."""
        replacement = await sentence_guardrail(sentence) if sentence_guardrail is not None else None
        if replacement is not None:
            safe_sentence = replacement
            validation_passed = False
        else:
            validation = self.validator.validate_sentence(sentence, evidence, context)
            validation_passed = validation.passed
            safe_sentence = sentence if validation.passed else await self._repair_or_refuse(validation)

        chunks = [safe_sentence] if not validation_passed else visual_chunks(safe_sentence)
        for text in chunks:
            current_sequence += 1
            yield ValidatedChunk(current_sequence, text, "sentence_buffered", validation_passed)

    async def _repair_or_refuse(self, validation: Any) -> str:
        """Attempt to repair a failed sentence, or return a safe refusal."""
        reasons = tuple(
            result.reason for result in getattr(validation, "claims", ()) if getattr(result, "reason", None)
        )
        logger.warning(
            "Validated stream sentence refused reason_codes=%s",
            reasons,
        )
        return _SAFE_REFUSAL

    async def events(
        self,
        provider_tokens: AsyncIterator[str],
        evidence: Mapping[str, str],
        context: Optional[ValidationContext],
        citations: Any = None,
        graph_explanation: Any = "",
        sentence_guardrail: Optional[Callable[[str], Awaitable[Optional[str]]]] = None,
    ) -> AsyncIterator[SseEvent]:
        """Full SSE event stream with the fixed terminal contract.

        Event order:
            status -> metadata -> token* -> citations -> graph_explanation -> done
        """
        yield SseEvent(type="status", content="retrieving")
        yield SseEvent(type="metadata", content="sentence_buffered")

        async for chunk in self.validated_chunks(provider_tokens, evidence, context, sentence_guardrail):
            yield SseEvent(
                type="token",
                content=chunk.content,
                sequence=chunk.sequence,
                validation_mode=chunk.validation_mode,
                validation_passed=chunk.validation_passed,
            )

        yield SseEvent(type="citations", data=[] if citations is None else citations)
        yield SseEvent(type="graph_explanation", data=graph_explanation)
        yield SseEvent(type="done")
