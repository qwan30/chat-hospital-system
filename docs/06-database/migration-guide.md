# Database Migration Guide

> Project: HOSP-AI-001 · Version: 1.0 · Owner: Backend Lead · Last Updated: 2026-06-14  

## 1. Quick Commands

```bash
cd app/backend
poetry run alembic revision --autogenerate -m "description"  # Create
poetry run alembic upgrade head                                # Apply all
poetry run alembic downgrade -1                                # Rollback 1
poetry run alembic current                                     # Show state
poetry run alembic history                                     # Show history
```

## 2. Migration History

| # | File | Description |
|---|------|-------------|
| 0001 | `0001_initial_schema.py` | Core: users, patients, permissions, documents, pages, chunks, audit, queries |
| 0002 | `0002_add_document_index_generation.py` | index_generation, indexed_source_sha256 |
| 0003 | `0003_add_chat_threads.py` | chat_threads, participants, messages |
| 0004 | `0004_add_hms_sync_logs.py` | hms_sync_logs |
| 0005 | `0005_add_system_settings.py` | system_settings key-value store |
| 0006 | `0006_add_phase4_tables.py` | Phase 4: extended observability + access |

## 3. Naming: `NNNN_snake_case_description.py`

## 4. Rules

- Autogenerate first, then review and adjust.
- Test both `upgrade` and `downgrade` before commit.
- Don't edit applied migrations — create new ones.
- Use expand-and-contract for breaking production changes:
  1. Add new column (backward-compatible)
  2. Deploy writing to both old+new
  3. Backfill data
  4. Switch reads to new
  5. Remove old in future migration

## 5. Testing

```bash
poetry run alembic upgrade head && poetry run alembic downgrade -1 && poetry run alembic upgrade head
poetry run python scripts/seed_dev.py
poetry run pytest
```

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Created with 6-migration history + expand-and-contract guide |
