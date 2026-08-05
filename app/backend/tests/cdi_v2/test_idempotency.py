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
