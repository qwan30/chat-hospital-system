from __future__ import annotations

import uuid

import pytest

from hospital_ai.services.idempotency import IdempotencyService


@pytest.mark.asyncio
async def test_same_idempotency_key_replays_once(session_and_settings) -> None:
    session, _ = session_and_settings
    actor_user_id = uuid.uuid4()
    service = IdempotencyService(session, actor_user_id)
    first = await service.begin("draft.save", "key-1", {"text": "A"})
    await service.complete(first.record_id, 201, {"revision_id": "r1"})
    replay = await service.begin("draft.save", "key-1", {"text": "A"})
    assert replay.is_replay is True
    assert replay.response_body == {"revision_id": "r1"}

    from hospital_ai.core.errors import ConflictError

    with pytest.raises(ConflictError):
        await service.begin("draft.save", "key-1", {"text": "B"})


@pytest.mark.asyncio
async def test_started_duplicate_returns_explicit_retry_response(session_and_settings) -> None:
    session, _ = session_and_settings
    service = IdempotencyService(session, uuid.uuid4())

    first = await service.begin("draft.save", "key-in-progress", {"text": "A"})
    duplicate = await service.begin("draft.save", "key-in-progress", {"text": "A"})

    assert first.is_replay is False
    assert duplicate.is_replay is False
    assert duplicate.is_in_progress is True
    assert duplicate.status_code == 409
    assert duplicate.response_body == {"detail": "Request is already in progress; retry later."}

    await service.abort(first.record_id)
    retry = await service.begin("draft.save", "key-in-progress", {"text": "A"})
    assert retry.is_in_progress is False
    assert retry.is_replay is False


@pytest.mark.asyncio
async def test_concurrent_begin_enforces_unique_key_and_in_progress(session_and_settings) -> None:
    session, _ = session_and_settings
    actor_user_id = uuid.uuid4()
    import asyncio

    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_factory = async_sessionmaker(session.bind, expire_on_commit=False)
    decisions = []
    lock = asyncio.Lock()

    async def run_begin():
        async with session_factory() as worker_session:
            svc = IdempotencyService(worker_session, actor_user_id)
            decision = await svc.begin("concurrent.scope", "same-key", {"data": 123})
            async with lock:
                decisions.append(decision)

    await asyncio.gather(run_begin(), run_begin())

    assert len(decisions) == 2
    started_decisions = [d for d in decisions if not d.is_in_progress and not d.is_replay]
    in_progress_decisions = [d for d in decisions if d.is_in_progress]
    assert len(started_decisions) == 1
    assert len(in_progress_decisions) == 1
    assert in_progress_decisions[0].status_code == 409
