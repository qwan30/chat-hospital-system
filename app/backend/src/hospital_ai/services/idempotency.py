import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.errors import ConflictError
from hospital_ai.db.clinical_documents import IdempotencyRecord


@dataclass(frozen=True)
class IdempotencyDecision:
    record_id: uuid.UUID
    is_replay: bool
    status_code: int | None = None
    response_body: dict[str, Any] | None = None

def canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

class IdempotencyService:
    def __init__(self, session: AsyncSession, actor_user_id: uuid.UUID) -> None:
        self.session = session
        self.actor_user_id = actor_user_id

    async def _lock(self, actor_user_id: uuid.UUID, scope: str, key_hash: str) -> IdempotencyRecord | None:
        stmt = select(IdempotencyRecord).where(
            IdempotencyRecord.actor_user_id == actor_user_id,
            IdempotencyRecord.scope == scope,
            IdempotencyRecord.key_hash == key_hash,
        ).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def begin(self, scope: str, key: str, payload: Mapping[str, Any]) -> IdempotencyDecision:
        key_hash = sha256(key.encode()).hexdigest()
        payload_hash = sha256(canonical_json(payload)).hexdigest()
        record = await self._lock(self.actor_user_id, scope, key_hash)
        if record is not None:
            if record.payload_sha256 != payload_hash:
                raise ConflictError("Idempotency-Key was already used with a different payload.")
            return IdempotencyDecision(record.id, True, record.status_code, record.response_body)
        
        created = IdempotencyRecord(
            actor_user_id=self.actor_user_id,
            scope=scope,
            key_hash=key_hash,
            payload_sha256=payload_hash,
            state="started",
        )
        self.session.add(created)
        await self.session.flush()
        return IdempotencyDecision(created.id, False)

    async def complete(self, record_id: uuid.UUID, status_code: int, response_body: dict[str, Any]) -> None:
        stmt = select(IdempotencyRecord).where(IdempotencyRecord.id == record_id).with_for_update()
        result = await self.session.execute(stmt)
        record = result.scalars().first()
        if record:
            record.state = "completed"
            record.status_code = status_code
            record.response_body = response_body
            self.session.add(record)
            await self.session.flush()
