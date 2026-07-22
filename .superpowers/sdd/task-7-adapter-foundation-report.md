# Task 7 report — Live-evaluation adapter foundation

## Delivered

- Added a fail-closed `SourceEvidenceResolver` that anchors runtime evidence to the canonical corpus SHA-256, source path, patient, and PDF page or CSV row.
- Added isolation contracts and deterministic evaluation-actor materialisation so later product adapters cannot target the development database or persist test users.
- Added async evaluation orchestration with one event loop per run and a typed case context for product adapters.
- Treats raw runtime chunk identifiers as untrusted until resolved to canonical source evidence.

## Verification

Run from `app/backend` on 2026-07-22:

```text
py -3.12 -m pytest tests/evaluation/test_adapter_foundation.py tests/evaluation/test_evaluation_runner.py -q
26 passed

ruff check src/hospital_ai/evaluation/adapter_foundation.py src/hospital_ai/evaluation/runner.py tests/evaluation/test_adapter_foundation.py tests/evaluation/test_evaluation_runner.py
All checks passed!
```

## Follow-up

This foundation deliberately does not claim live product retrieval, Graph RAG, or chat coverage. Those adapters must use the isolated context and source resolver before a release suite may report product quality.

## Review remediation

Independent review found rank loss, adapter-asserted provenance, and database-alias isolation bypasses. The foundation now preserves retrieval rank, accepts only `RuntimeEvidenceChunk` observations resolved through registered canonical candidates, and normalizes PostgreSQL drivers plus loopback aliases while requiring an explicitly approved evaluation-database identity. The focused foundation/runner suite reports 32 passing tests.
