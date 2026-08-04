# Vendored Public Medical Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` task-by-task. Apply test-driven development for production behavior and verify every claimed result against the exact branch SHA.

**Goal:** Commit a compact, licensed public medical corpus directly into the repository, validate it offline, remove misleading dataset scripts, and deliver a CI-backed pull request without downloading external data in GitHub Actions.

**Architecture:** A JSON source registry is authoritative for vendored artifacts. Python domain code loads and validates immutable entries, a CLI performs fail-closed integrity checks, tests enforce data/license/workflow contracts, and committed XML files travel with Git clone/pull and VPS source deployments.

**Tech stack:** Python 3.11+, Pydantic 1.x, pytest, Ruff, GitHub Actions, JSON, Git/GitHub.

## Global constraints

- Work only on `feat/vendor-public-medical-data`; do not modify `main` directly.
- External dataset content must be committed under `app/backend/data/public/`.
- GitHub Actions must not download external datasets.
- All validation must work without network access.
- Every vendored artifact must have pinned upstream commit/path/blob identity, CC-compatible redistribution metadata, exact byte size, and SHA-256.
- The first corpus is a five-file MedQuAD GARD XML sample pinned at upstream commit `577bd37b96c02d1833b2c9eed2de9f96964e96cb`.
- Do not represent MedQuAD as patient records, MIMIC, discharge summaries, or production clinical truth.
- Preserve upstream XML bytes; do not rewrite medical content.
- Use failing tests before production code where behavior changes.
- Preserve the existing canonical 100-patient synthetic corpus and its six quarantined public-reference artifacts.

## Task 1: Establish branch documentation and source contract

**Files:**
- Create/update: `docs/superpowers/specs/2026-08-04-vendored-public-medical-data-design.md`
- Create/update: `docs/superpowers/plans/2026-08-04-vendored-public-medical-data.md`

**Steps:**
- [x] Create the isolated feature branch from current `main` SHA.
- [x] Commit the approved design and plan.
- [x] Refine the design from a binary ZIP to readable upstream XML after GitHub rejected cross-repository blob reuse.
- [ ] Self-review documents for placeholders, contradictions, ambiguous dataset naming, and scope drift.

## Task 2: Add RED tests for the vendored-data contract

**File:** `app/backend/tests/data_sources/test_vendored_public_data.py`

**Tests must initially fail because implementation/data are absent:**
- registry declares one pinned MedQuAD GARD source and exactly five expected upstream paths;
- source uses `CC-BY-4.0`, contains attribution, and declares evaluation-only clinical limitations;
- all vendored paths are relative and contained by backend data root;
- every artifact size and SHA-256 matches the registry;
- missing or modified artifacts fail validation without repair;
- `.github/workflows/*.yml` and `*.yaml` contain no public-data download command;
- legacy `download_hf_notes.py` and `seed_mimic.py` paths are absent.

**Verification:**
- Record expected RED failures caused by missing registry/module/artifacts.

## Task 3: Vendor exact MedQuAD XML and provenance files

**Files:**
- Create: `app/backend/data/public/sources.json`
- Create: `app/backend/data/public/medquad/README.md`
- Create: `app/backend/data/public/medquad/LICENSE.txt`
- Create under `app/backend/data/public/medquad/sample/`:
  - `2_GARD_QA/0003206.xml`
  - `2_GARD_QA/0003638.xml`
  - `2_GARD_QA/0004425.xml`
  - `2_GARD_QA/0004873.xml`
  - `2_GARD_QA/0005459.xml`

**Steps:**
- [ ] Copy each upstream XML byte-for-byte from pinned commit `577bd37b96c02d1833b2c9eed2de9f96964e96cb`.
- [ ] Verify each local Git blob SHA equals the upstream blob SHA.
- [ ] Calculate and record exact byte size and SHA-256.
- [ ] Record upstream repository, commit, path, blob SHA, retrieval date, license, attribution, intended use, and limitations.
- [ ] Document that this is a small evaluation fixture, not the full MedQuAD corpus.

## Task 4: Implement offline registry validation

**Files:**
- Create: `app/backend/src/hospital_ai/data_sources/__init__.py`
- Create: `app/backend/src/hospital_ai/data_sources/registry.py`
- Create: `app/backend/scripts/validate_vendored_public_data.py`

**Behavior:**
- parse `sources.json` through immutable Pydantic models;
- reject absolute paths and `..` traversal;
- require source, upstream, license, attribution, intended-use, limitation, artifact, size, and lowercase SHA-256 fields;
- hash files in chunks;
- fail on missing, size-mismatched, or hash-mismatched files;
- return structured validation results and a non-zero CLI exit code on failure;
- never download, repair, or mutate data.

**Verification:**
- Re-run Task 2 tests to GREEN.
- Run Ruff on new code.

## Task 5: Remove misleading external-data scripts

**Files:**
- Delete: `app/backend/scripts/download_hf_notes.py`
- Delete: `app/backend/scripts/seed_mimic.py`
- Create: `app/backend/scripts/seed_mock_clinical_notes.py`
- Update: references found by repository search.

**Behavior:**
- preserve the existing two-note Graph RAG development fixture;
- rename constants, MRNs, patient labels, log messages, and comments to explicitly say synthetic/mock;
- do not imply MIMIC provenance;
- add no replacement network downloader.

**Verification:**
- Search for `tstadel/maccrobat`, `NOTEEVENTS.csv`, `MIMIC-`, `Mimic Patient`, and misleading messages.

## Task 6: Integrate approved public artifacts with corpus inventory

**Files:**
- Update: `app/backend/src/hospital_ai/evaluation/corpus_manifest.py`
- Update: `app/backend/tests/evaluation/test_corpus_manifest.py`

**Behavior:**
- represent approved vendored evaluation datasets separately from six quarantined guideline/drug artifacts;
- preserve exact canonical patient counts and duplicate-exclusion behavior;
- expose registry provenance/license fields;
- never ingest MedQuAD as patient data or clinical knowledge automatically.

**TDD:** Add failing manifest test, implement minimal collection/type, then run manifest tests.

## Task 7: Add offline CI validation and deployment documentation

**Files:**
- Update: appropriate existing backend workflow under `.github/workflows/`
- Update: `README.md`
- Create/update: dataset documentation under `docs/`

**Behavior:**
- CI invokes offline validator after checkout;
- no external dataset download step is introduced;
- README states clone/pull includes public XML;
- VPS source deployment receives it automatically;
- Docker inclusion depends on build context/Dockerfile copy rules;
- document size governance for future data.

## Task 8: Verification and review

**Checks:**
- `python app/backend/scripts/validate_vendored_public_data.py`
- targeted data-source and corpus-manifest tests;
- full backend pytest where environment permits;
- Ruff for modified Python;
- workflow/static contract tests;
- compare branch with `main` for unintended or oversized files;
- verify no secrets, PHI, gated data, cache, or clinical-validity claims.

## Task 9: Publish draft PR

- [x] Push feature branch through the connected GitHub repository.
- [x] Open draft PR #86 to `main`.
- [ ] Keep PR body synchronized with refined XML sample scope.
- [ ] Complete structured self-review and request review where available.

## Task 10: CI log and fix loop

1. Fetch workflow runs for exact PR head SHA.
2. For failed jobs, fetch job steps and complete logs.
3. Apply `superpowers:systematic-debugging`; identify root cause before edits.
4. Add/adjust a reproducing test when applicable.
5. Commit minimal fix on same branch.
6. Review fix diff.
7. Fetch CI for new head SHA.
8. Repeat until green or document an evidenced external blocker.

## Completion criteria

- Five original MedQuAD GARD XML files are committed byte-for-byte.
- Registry and offline validator verify exact bytes, license, provenance, and limitations.
- CI performs no external dataset download.
- Misleading MIMIC/MACCROBAT scripts are removed or accurately renamed.
- Existing synthetic corpus/quarantine guarantees remain intact.
- Draft PR #86 accurately documents scope and deployment behavior.
- Latest-head CI is green, or any unresolvable external blocker is evidenced with exact job/log details.
