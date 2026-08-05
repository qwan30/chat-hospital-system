from __future__ import annotations
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError

@pytest.mark.asyncio
async def test_graph_provenance_tables_exist(session_and_settings):
    session, _ = session_and_settings
    try:
        await session.execute(select(text("1")).select_from(text("graph_entities")))
        await session.execute(select(text("1")).select_from(text("graph_mentions")))
        await session.execute(select(text("1")).select_from(text("graph_relation_assertions")))
        await session.execute(select(text("1")).select_from(text("graph_relation_evidence")))
    except ProgrammingError:
        pytest.fail("Graph provenance tables are missing")
