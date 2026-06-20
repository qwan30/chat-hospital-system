"""Tests for the POST /chat/stream endpoint (SSE streaming).

Exercises the streaming chat route handler through its FastAPI dependencies,
verifying SSE event format, authorization, no-evidence fallback, and error
handling per F-SEC-004.
"""

import json
import uuid
from unittest.mock import patch

import pytest
from starlette.requests import Request

from hospital_ai.api.routes.chat_stream import chat_stream
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
from hospital_ai.db.models import User
from hospital_ai.schemas.chat import ChatRequest
from hospital_ai.services.chat import SAFE_NO_EVIDENCE_ANSWER
from hospital_ai.services.llm.stub_provider import StubLLM
from tests.conftest import create_indexed_document

_client_counter = 0


def _request() -> Request:
    global _client_counter
    _client_counter += 1
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/chat/stream",
            "headers": [],
            "client": (f"10.0.0.{_client_counter}", 50000),
        }
    )


def _parse_sse_events(body: bytes) -> list[dict]:
    """Parse SSE-formatted bytes into a list of event dicts."""
    text = body.decode("utf-8")
    events = []
    for line in text.strip().split("\n\n"):
        line = line.strip()
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


@pytest.mark.asyncio
async def test_chat_stream_token_events(session_and_settings):
    """SSE response yields token events with text content."""
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Progress Note",
        content="Patient shows signs of recovery. Status: improving. Vital signs: stable.",
    )

    payload = ChatRequest(
        patient_id=PATIENT_ALICE_ID,
        question="What is the status?",
    )

    response = await chat_stream(
        payload=payload,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    body = b""
    async for chunk in response.body_iterator:
        body += chunk.encode("utf-8")

    events = _parse_sse_events(body)
    token_events = [e for e in events if e.get("type") == "token"]

    assert len(token_events) >= 1
    for te in token_events:
        assert "content" in te
        assert isinstance(te["content"], str)
        assert len(te["content"]) > 0


@pytest.mark.asyncio
async def test_chat_stream_metadata_event(session_and_settings):
    """SSE response includes a metadata event with confidence."""
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Lab Report",
        content="Hemoglobin: 13.5. Status: stable.",
    )

    payload = ChatRequest(
        patient_id=PATIENT_ALICE_ID,
        question="What are the lab results?",
    )

    response = await chat_stream(
        payload=payload,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    body = b""
    async for chunk in response.body_iterator:
        body += chunk.encode("utf-8")

    events = _parse_sse_events(body)
    meta_events = [e for e in events if e.get("type") == "metadata"]

    assert len(meta_events) >= 1
    meta = meta_events[0]
    assert "confidence" in meta
    assert meta["confidence"] in ("low", "medium", "high")
    assert "pipeline" in meta
    assert "model" in meta


@pytest.mark.asyncio
async def test_chat_stream_done_event(session_and_settings):
    """SSE response ends with a done event containing query_id."""
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Admission Note",
        content="Patient admitted. Status: critical.",
    )

    payload = ChatRequest(
        patient_id=PATIENT_ALICE_ID,
        question="What is the admission status?",
    )

    response = await chat_stream(
        payload=payload,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    body = b""
    async for chunk in response.body_iterator:
        body += chunk.encode("utf-8")

    events = _parse_sse_events(body)
    done_events = [e for e in events if e.get("type") == "done"]

    assert len(done_events) >= 1
    done = done_events[0]
    assert "query_id" in done
    uuid.UUID(done["query_id"])


@pytest.mark.asyncio
async def test_chat_stream_permission_denied_error(session_and_settings):
    """SSE error event when user lacks patient access (not a crash)."""
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    payload = ChatRequest(
        patient_id=PATIENT_BOB_ID,
        question="What is the status?",
    )

    response = await chat_stream(
        payload=payload,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    body = b""
    async for chunk in response.body_iterator:
        body += chunk.encode("utf-8")

    events = _parse_sse_events(body)
    error_events = [e for e in events if e.get("type") == "error"]

    assert len(error_events) >= 1
    error = error_events[0]
    assert "not authorized" in error.get("message", "").lower()


@pytest.mark.asyncio
async def test_chat_stream_no_evidence_returns_safe_answer(session_and_settings):
    """SSE returns SAFE_NO_EVIDENCE_ANSWER when no evidence exists."""
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    payload = ChatRequest(
        patient_id=PATIENT_ALICE_ID,
        question="What is the condition?",
    )

    response = await chat_stream(
        payload=payload,
        request=_request(),
        session=session,
        current_user=doctor,
        settings=settings,
    )

    body = b""
    async for chunk in response.body_iterator:
        body += chunk.encode("utf-8")

    events = _parse_sse_events(body)
    assert len(events) >= 1
    first = events[0]
    assert first.get("type") == "token"
    assert SAFE_NO_EVIDENCE_ANSWER in first.get("content", "")

    done_events = [e for e in events if e.get("type") == "done"]
    assert len(done_events) >= 1
    assert "query_id" in done_events[0]


@pytest.mark.asyncio
async def test_chat_stream_error_no_leak(session_and_settings):
    """SSE error events must not leak internal exception details (F-SEC-004)."""
    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Test Document",
        content="Some clinical content for the patient.",
    )

    async def _failing_stream(self, messages, **kw):
        if False:
            yield
        raise ValueError("INTERNAL_CRASH_WITH_SECRET_DATA_12345")

    with patch.object(StubLLM, "stream", _failing_stream):
        payload = ChatRequest(
            patient_id=PATIENT_ALICE_ID,
            question="What is happening?",
        )

        response = await chat_stream(
            payload=payload,
            request=_request(),
            session=session,
            current_user=doctor,
            settings=settings,
        )

        body = b""
        async for chunk in response.body_iterator:
            body += chunk.encode("utf-8")

    events = _parse_sse_events(body)
    error_events = [e for e in events if e.get("type") == "error"]
    assert len(error_events) >= 1
    error = error_events[0]

    # F-SEC-004: internal details never reach the wire
    assert "INTERNAL_CRASH_WITH_SECRET_DATA_12345" not in body.decode("utf-8")
    assert error.get("code") == "INTERNAL_ERROR"
    assert "internal error" in error.get("message", "").lower()
