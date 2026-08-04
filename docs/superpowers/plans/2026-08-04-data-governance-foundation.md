# Public Data Governance Foundation — Implementation Plan

**Date:** 2026-08-04  
**Branch:** `feat/vendor-public-medical-data`  
**PR:** #86

## Goal

Refactor PR #86 from a standalone MedQuAD fixture into a narrow, mergeable data-governance foundation that does not conflict with the unified Clinical Document Intelligence design.

## Task 1 — Define the boundary contract

- Add tests that fail while MedQuAD is committed, wired into the corpus, or copied into Docker.
- Keep a positive test proving the generic registry validates an isolated temporary artifact.
- Keep traversal and misleading-script contracts.

Verification:

```bash
cd app/backend
pytest tests/data_sources/test_data_governance_foundation.py
```

## Task 2 — Remove standalone dataset behavior

- Delete five MedQuAD XML files.
- Delete MedQuAD attribution/readme from this PR.
- Delete the repository-wide public source instance.
- Delete the dedicated vendored-public-data workflow.
- Remove the old vendored-data deployment documentation.

## Task 3 — Restore product boundaries

Restore these files byte-for-byte from `main`:

- `.github/workflows/cd.yml`
- `app/backend/Dockerfile`
- `app/backend/.dockerignore`
- `app/backend/src/hospital_ai/evaluation/corpus_manifest.py`
- `app/backend/tests/evaluation/test_corpus_manifest.py`
- `app/backend/tests/test_cd_operations_contracts.py`

This removes unrelated deployment edits and preserves the canonical benchmark contract.

## Task 4 — Keep the reusable foundation

- Keep `hospital_ai.data_sources.registry`.
- Replace the default-path validator with `validate_public_source_registry.py` requiring explicit arguments.
- Keep path, size, checksum, provenance, license, intended-use, and limitation validation.
- Keep tests based on temporary files.

## Task 5 — Keep honest script cleanup

- Delete `download_hf_notes.py`.
- Delete `seed_mimic.py`.
- Keep `seed_mock_clinical_notes.py` with `MOCK-*` identifiers and legacy cleanup.

## Task 6 — Review and verification

Run:

```bash
cd app/backend
python -m ruff check src/ tests/
python -m ruff format --check src/ tests/
pytest
```

Then verify:

- PR diff contains no MedQuAD data;
- no public dataset enters Docker;
- no public fixture enters the canonical corpus;
- no unrelated deployment change remains;
- CI, migration checks, frontend, CodeQL, and evaluation gates are green on one head SHA.

## Task 7 — Update PR metadata

Update title and body to describe data-governance foundation and its relationship to the unified Clinical Document Intelligence spec. Return the PR from draft only after same-SHA verification succeeds.
