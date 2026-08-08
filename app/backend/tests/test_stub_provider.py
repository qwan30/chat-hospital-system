from __future__ import annotations

import pytest

from hospital_ai.services.chat_utils import SAFE_PHI_LEAK_BLOCKED_ANSWER
from hospital_ai.services.llm.base import LLMMessage
from hospital_ai.services.llm.stub_provider import StubLLM


@pytest.mark.asyncio
async def test_stub_provider_blocks_sensitive_prompt() -> None:
    response = await StubLLM().generate([LLMMessage(role="user", content="Explain chemotherapy safety.")])

    assert response.text == SAFE_PHI_LEAK_BLOCKED_ANSWER


@pytest.mark.asyncio
async def test_stub_provider_stream_uses_the_same_blocked_answer() -> None:
    chunks = [
        chunk async for chunk in StubLLM().stream([LLMMessage(role="user", content="Explain chemotherapy safety.")])
    ]

    assert "".join(chunks) == SAFE_PHI_LEAK_BLOCKED_ANSWER
