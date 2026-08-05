"""Tests for the database-backed settings API.

Verifies that:
- GET /settings returns defaults when no overrides exist.
- PUT /settings persists overrides to the system_settings table.
- Overrides survive a fresh GET (round-trip persistence).
- Multiple PUT calls merge overrides correctly.
"""
from __future__ import annotations

import pytest

from hospital_ai.db.settings_store import (
    delete_setting,
    effective_value,
    get_all_overrides,
    get_setting,
    upsert_many,
    upsert_setting,
)


@pytest.mark.asyncio
async def test_get_setting_returns_none_for_missing(session_and_settings):
    """get_setting returns None when no override exists for the key."""
    session, settings = session_and_settings
    result = await get_setting(session, "nonexistent_key")
    assert result is None


@pytest.mark.asyncio
async def test_upsert_and_get_setting(session_and_settings):
    """A setting can be upserted and then retrieved."""
    session, settings = session_and_settings

    await upsert_setting(session, "chat_provider", "openai")
    await session.commit()

    result = await get_setting(session, "chat_provider")
    assert result == "openai"


@pytest.mark.asyncio
async def test_upsert_overwrites_existing(session_and_settings):
    """Upserting the same key replaces the previous value."""
    session, settings = session_and_settings

    await upsert_setting(session, "retrieval_top_k", 5)
    await session.commit()
    assert await get_setting(session, "retrieval_top_k") == 5

    await upsert_setting(session, "retrieval_top_k", 10)
    await session.commit()
    assert await get_setting(session, "retrieval_top_k") == 10


@pytest.mark.asyncio
async def test_get_all_overrides_returns_dict(session_and_settings):
    """get_all_overrides returns a dictionary of all persisted keys."""
    session, settings = session_and_settings

    await upsert_setting(session, "chat_provider", "ollama")
    await upsert_setting(session, "streaming_enabled", True)
    await upsert_setting(session, "retrieval_top_k", 8)
    await session.commit()

    overrides = await get_all_overrides(session)
    assert overrides["chat_provider"] == "ollama"
    assert overrides["streaming_enabled"] is True
    assert overrides["retrieval_top_k"] == 8


@pytest.mark.asyncio
async def test_upsert_many_batch_insert(session_and_settings):
    """upsert_many inserts multiple keys in one call."""
    session, settings = session_and_settings

    updates = {
        "embedding_provider": "sentence-transformer",
        "chunk_size": 512,
        "evidence_threshold": 0.42,
    }
    await upsert_many(session, updates)

    overrides = await get_all_overrides(session)
    assert overrides["embedding_provider"] == "sentence-transformer"
    assert overrides["chunk_size"] == 512
    assert overrides["evidence_threshold"] == 0.42


@pytest.mark.asyncio
async def test_delete_setting_removes_key(session_and_settings):
    """delete_setting removes a key and returns True."""
    session, settings = session_and_settings

    await upsert_setting(session, "chat_model", "gpt-4")
    await session.commit()
    assert await get_setting(session, "chat_model") == "gpt-4"

    removed = await delete_setting(session, "chat_model")
    await session.commit()
    assert removed is True
    assert await get_setting(session, "chat_model") is None


@pytest.mark.asyncio
async def test_delete_missing_setting_returns_false(session_and_settings):
    """delete_setting returns False when the key does not exist."""
    session, settings = session_and_settings

    removed = await delete_setting(session, "nonexistent_key")
    assert removed is False


@pytest.mark.asyncio
async def test_effective_value_prefers_override(session_and_settings):
    """effective_value returns the DB override over the env default."""
    session, settings = session_and_settings

    overrides = {"chat_provider": "ollama"}
    result = effective_value("chat_provider", overrides, settings)
    assert result == "ollama"


@pytest.mark.asyncio
async def test_effective_value_falls_back_to_settings(session_and_settings):
    """effective_value falls back to the Settings default when no override."""
    session, settings = session_and_settings

    overrides = {}
    result = effective_value("chat_provider", overrides, settings)
    assert result == settings.chat_provider


@pytest.mark.asyncio
async def test_boolean_round_trip(session_and_settings):
    """Boolean values round-trip through JSON serialization correctly."""
    session, settings = session_and_settings

    await upsert_setting(session, "streaming_enabled", False)
    await session.commit()

    result = await get_setting(session, "streaming_enabled")
    assert result is False
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_float_round_trip(session_and_settings):
    """Float values round-trip through JSON serialization correctly."""
    session, settings = session_and_settings

    await upsert_setting(session, "evidence_threshold", 0.78)
    await session.commit()

    result = await get_setting(session, "evidence_threshold")
    assert result == 0.78
    assert isinstance(result, float)
