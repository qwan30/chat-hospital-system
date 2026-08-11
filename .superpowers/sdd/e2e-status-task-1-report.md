# Task 1 Report — Seed status contract

Date: 2026-08-09
Branch: `fix/full-project-e2e-20260809`

## Summary

Implemented the seed-status contract fix by aligning all six in-scope backend scripts with the current `Document.status` schema contract (`ready` instead of legacy `indexed`), and added a regression test that reproduces the real SQLite `ck_documents_status` failure path through `seed_dev._add_document`.

## RED

Command:

```powershell
& 'D:\projects\chatbot-hospital-system\app\backend\.venv\Scripts\python.exe' -m pytest tests/test_seed_status_contract.py -k seed_dev_add_document_creates_ready_document -q
```

Output:

```text
F                                                                        [100%]
FAILED tests/test_seed_status_contract.py::test_seed_dev_add_document_creates_ready_document
E   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) CHECK constraint failed: ck_documents_status
E   [parameters: (... 'status', 'indexed', ...)]
1 failed, 6 deselected, 1 warning in 6.18s
```

Notes:

- I first hit an environment mismatch using the shell-default Python 3.9 / global 3.12 installs, so I switched to the repo-local backend virtualenv that matches `requires-python = ">=3.11"` and the repo’s pinned dependencies.
- The effective RED run above is the real regression signal for this task: `seed_dev._add_document` flushed a `Document(status="indexed")` into the live SQLAlchemy/SQLite check constraint and failed exactly at `ck_documents_status`.

## GREEN

Command:

```powershell
& 'D:\projects\chatbot-hospital-system\app\backend\.venv\Scripts\python.exe' -m pytest tests/test_seed_status_contract.py tests/test_documents.py tests/test_migrations.py -q
```

Output:

```text
..........................                                               [100%]
26 passed, 2 warnings in 13.90s
```

Warnings:

- `DeprecationWarning` from `opentelemetry.instrumentation.dependencies` / `pkg_resources`
- `PendingDeprecationWarning` from `starlette.formparsers` / `multipart`

These warnings pre-existed this task and were not changed here.

## Files changed

- `app/backend/tests/test_seed_status_contract.py`
- `app/backend/scripts/seed_dev.py`
- `app/backend/scripts/seed_data.py`
- `app/backend/scripts/seed_mock_clinical_notes.py`
- `app/backend/scripts/run_rag_eval.py`
- `app/backend/scripts/generate_documents.py`
- `app/backend/scripts/demo_setup.py`

Diff summary:

```text
6 backend script files changed, 6 insertions, 6 deletions
1 new focused regression test file added
```

## What changed

1. Added `tests/test_seed_status_contract.py`
   - `test_seed_dev_add_document_creates_ready_document`
     - Exercises the real `seed_dev._add_document` helper against the current schema.
     - Proves the inserted document flushes successfully and lands in `status == "ready"`.
   - `test_seed_scripts_do_not_use_legacy_indexed_document_status`
     - Source-contract regression check covering:
       - `seed_dev.py`
       - `seed_data.py`
       - `seed_mock_clinical_notes.py`
       - `run_rag_eval.py`
       - `generate_documents.py`
       - `demo_setup.py`

2. Minimal status-contract fix in all six allowed scripts
   - Replaced legacy `status="indexed"` with `status="ready"`
   - Preserved helper/function structure
   - Did not touch migrations
   - Did not broaden runtime behavior outside the requested seed/demo script contract

## Verification and review

- GitNexus impact before edits:
  - `seed_dev._add_document`: LOW risk, 1 direct caller, scripts-only surface
  - `seed_data.seed`: LOW risk
  - `seed_mock_clinical_notes.main`: LOW risk
  - `run_rag_eval.create_indexed_document`: LOW risk
  - `generate_documents.generate`: LOW risk
  - `demo_setup.setup_demo`: LOW risk
- GitNexus `detect_changes(scope="all")` after edits:
  - changed symbols: 6
  - affected processes: 0
  - risk: low
- `rg -n "status\\s*=\\s*['\"]indexed['\"]" app/backend/scripts`
  - no matches

## Self-review

- The fix stays exactly inside the requested ownership boundary: one focused regression test file plus the six named backend scripts.
- The regression test is behavior-level, not a string-only assertion: it reproduces the actual SQLite integrity failure path and proves the post-fix flush succeeds.
- The source-contract check closes the remaining gap by preventing new legacy `indexed` literals from reappearing in the six production seed/demo scripts.
- I did not modify the migration chain, the local database, user-owned `.tmp-*` directories, unrelated docs, or the old tracked `.superpowers/sdd/task-1-brief.md`.

## Concerns

- The repo has pre-existing untracked `.tmp-*` directories and an unrelated untracked planning doc at `docs/superpowers/plans/2026-08-09-seed-status-contract-fix.md`; I left them untouched.
- Running backend tests requires the repo-local virtualenv, not the shell-default Python installation.
