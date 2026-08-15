from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.errors import ConflictError
from hospital_ai.db.clinical_documents import IdempotencyRecord


@dataclass(frozen=True)
class IdempotencyDecision:
    record_id: uuid.UUID
    is_replay: bool
    is_in_progress: bool = False
    status_code: Optional[int] = None
    response_body: dict[str, Any] = field(default_factory=dict)


def canonical_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class IdempotencyService:
    def __init__(self, session: AsyncSession, actor_user_id: uuid.UUID) -> None:
        self.session = session
        self.actor_user_id = actor_user_id

    async def _lock(self, actor_user_id: uuid.UUID, scope: str, key_hash: str) -> Optional[IdempotencyRecord]:
        stmt = (
            select(IdempotencyRecord)
            .where(
                IdempotencyRecord.actor_user_id == actor_user_id,
                IdempotencyRecord.scope == scope,
                IdempotencyRecord.key_hash == key_hash,
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    def _decision_for_record(record: IdempotencyRecord, payload_hash: str) -> IdempotencyDecision:
        if record.payload_sha256 != payload_hash:
            raise ConflictError("Idempotency-Key was already used with a different payload.")
        if record.state != "completed":
            return IdempotencyDecision(
                record.id,
                is_replay=False,
                is_in_progress=True,
                status_code=409,
                response_body={"detail": "Request is already in progress; retry later."},
            )
        return IdempotencyDecision(
            record.id,
            is_replay=True,
            status_code=record.status_code,
            response_body=record.response_body or {},
        )

    async def begin(self, scope: str, key: str, payload: Mapping[str, Any]) -> IdempotencyDecision:
        key_hash = sha256(key.encode()).hexdigest()
        payload_hash = sha256(canonical_json(payload)).hexdigest()
        record = await self._lock(self.actor_user_id, scope, key_hash)
        if record is not None:
            return self._decision_for_record(record, payload_hash)

        created = IdempotencyRecord(
            actor_user_id=self.actor_user_id,
            scope=scope,
            key_hash=key_hash,
            payload_sha256=payload_hash,
            state="started",
        )
        self.session.add(created)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            record = await self._lock(self.actor_user_id, scope, key_hash)
            if record is None:
                return IdempotencyDecision(
                    uuid.UUID(int=0),
                    is_replay=False,
                    is_in_progress=True,
                    status_code=409,
                    response_body={"detail": "Request is already in progress; retry later."},
                )
            return self._decision_for_record(record, payload_hash)
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

    async def abort(self, record_id: uuid.UUID) -> None:
        """Release an unfinished key after a mutation failed before completion."""
        await self.session.rollback()
        if record_id != uuid.UUID(int=0):
            record = await self.session.get(IdempotencyRecord, record_id)
            if record is not None:
                await self.session.delete(record)
                await self.session.commit()
