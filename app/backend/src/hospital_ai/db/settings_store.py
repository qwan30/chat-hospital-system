from __future__ import annotations
"""Database-backed system settings store.

Replaces the in-memory ``_overrides`` dict in ``routes/settings.py`` with
a persistent key-value table, allowing admin settings to survive restarts.

Every setting is stored as a ``SystemSetting`` row keyed by the config
field name (e.g. ``chat_provider``).  CRUD helpers expose the simple
get/put/list/delete operations that the settings API route needs.
"""


import json
import uuid
from typing import Optional, Any

from sqlalchemy import String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from hospital_ai.core.config import Settings
from hospital_ai.db.models import Base, TimestampMixin

# ── ORM Model ───────────────────────────────────────────────────────────


class SystemSetting(TimestampMixin, Base):
    """Single-row-per-key configuration store.

    Values are serialised as JSON text so that booleans, integers, floats,
    and strings all round-trip correctly.
    """

    __tablename__ = "system_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    value_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    description: Optional[Mapped[str]] = mapped_column(String(512), nullable=True)


# ── CRUD helpers ─────────────────────────────────────────────────────────


async def get_setting(session: AsyncSession, key: str) -> Optional[Any]:
    """Return the deserialised value for *key*, or ``None`` if unset."""
    result = await session.execute(select(SystemSetting).where(SystemSetting.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return json.loads(row.value_json)


async def get_all_overrides(session: AsyncSession) -> dict[str, Any]:
    """Return every persisted override as ``{key: value}``."""
    result = await session.execute(select(SystemSetting))
    rows: list[SystemSetting] = list(result.scalars().all())
    return {row.key: json.loads(row.value_json) for row in rows}


async def upsert_setting(
    session: AsyncSession,
    key: str,
    value: Any,
    *,
    user_id: Optional[uuid.UUID] = None,
    description: Optional[str] = None,
) -> SystemSetting:
    """Insert or update a setting, returning the row."""
    result = await session.execute(select(SystemSetting).where(SystemSetting.key == key))
    row = result.scalar_one_or_none()
    serialised = json.dumps(value)
    if row is None:
        row = SystemSetting(
            key=key,
            value_json=serialised,
            updated_by_user_id=user_id,
            description=description,
        )
        session.add(row)
    else:
        row.value_json = serialised
        row.updated_by_user_id = user_id
        if description is not None:
            row.description = description
    await session.flush()
    return row


async def upsert_many(
    session: AsyncSession,
    overrides: dict[str, Any],
    *,
    user_id: Optional[uuid.UUID] = None,
) -> None:
    """Bulk upsert — used by the PUT settings route."""
    for key, value in overrides.items():
        await upsert_setting(session, key, value, user_id=user_id)
    await session.commit()


async def delete_setting(session: AsyncSession, key: str) -> bool:
    """Remove a single override.  Returns ``True`` if the row existed."""
    result = await session.execute(select(SystemSetting).where(SystemSetting.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        return False
    await session.delete(row)
    await session.flush()
    return True


def effective_value(
    key: str,
    overrides: dict[str, Any],
    settings: Settings,
) -> Any:
    """Return the DB override if present, else the env/default value."""
    if key in overrides:
        return overrides[key]
    return getattr(settings, key)
