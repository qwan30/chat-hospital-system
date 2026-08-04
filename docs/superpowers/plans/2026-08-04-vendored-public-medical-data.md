# Vendored Public Medical Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` task-by-task. Apply test-driven development for production behavior and verify every claimed result against the exact branch SHA.

**Goal:** Commit a compact, licensed public medical corpus directly into the repository, validate it offline, remove misleading dataset scripts, and open a CI-backed pull request without downloading external data in GitHub Actions.

**Architecture:** A JSON source registry is the authority for vendored artifacts. Python domain code loads and validates registry entries, a CLI performs fail-closed integrity checks, tests enforce artifact/license/workflow contracts, and the committed dataset travels with Git clone/pull and VPS deployments.

**Tech stack:** Python 3.11+, Pydantic 1.x, pytest, Ruff, GitHub Actions, JSON, Git/GitHub.

## Global constraints

- Work only on `feat/vendor-public-medical-data`; do not modify `main` directly.
- External dataset content must be committed under `app/backend/data/public/`.
- GitHub Actions must not download external datasets.
- All validation must work without network access.
- Every vendored artifact must have a pinned upstream identity, CC-compatible redistribution metadata, byte size, and SHA-256.
- The first artifact is the official MedQuAD LiveQA judged-set archive, not the complete 47,457-pair corpus.
- Do not represent MedQuAD as patient records, MIMIC, discharge summaries, or production clinical truth.
- Use failing tests before production code where behavior changes.
- Preserve the existing canonical 100-patient synthetic corpus and its six quarantined public-reference artifacts.

## Task 1: Establish branch documentation and source contract

**Files:**
- Create: `docs/superpowers/specs/2026-08-04-vendored-public-medical-data-design.md`
- Create: `docs/superpowers/plans/2026-08-04-vendored-public-medical-data.md`

**Steps:**
- [x] Create the isolated feature branch from the current `main` SHA.
- [x] Commit the approved design.
- [x] Commit this implementation plan.
- [ ] Self-review both documents for placeholders, contradictions, ambiguous dataset naming, and scope drift.

**Verification:**
- Compare branch with `main`; only the two documentation files should exist at this checkpoint.

## Task 2: Add RED tests for the vendored-data contract

**Files:**
- Create: `app/backend/tests/data_sources/test_vendored_public_data.py`

**Tests must initially fail because implementation/data are absent:**
- registry loads a non-empty source list;
- MedQuAD entry uses `CC-BY-4.0`, contains attribution, and declares evaluation-only limitations;
- vendored path is relative and contained by the backend data root;
- artifact size and SHA-256 match registry values;
- missing or modified artifacts fail validation;
- validator performs no network repair;
- `.github/workflows/*.yml` and `*.yaml` contain no public-data download command;
- legacy `download_hf_notes.py` and `seed_mimic.py` paths are absent.

**Verification:**
- Run only this test module and record the expected failures caused by missing modules/artifacts.

## Task 3: Vendor the MedQuAD judged set and provenance files

**Files:**
- Create: `app/backend/data/public/sources.json`
- Create: `app/backend/data/public/medquad/README.md`
- Create: `app/backend/data/public/medquad/LICENSE.txt`
- Create: `app/backend/data/public/medquad/QA-TestSet-LiveQA-Med-Qrels-2479-Answers.zip`

**Steps:**
- [ ] Import the official archive bytes without re-encoding or modifying the upstream artifact.
- [ ] Calculate and record the local SHA-256 and exact byte size.
- [ ] Record upstream repository, path, pinned blob SHA `bb81b5cc2497f09b411e2ae5d20cf17aaf099a3d`, retrieval date, license, attribution, intended use, and limitations.
- [ ] Document that the artifact is an official judged test set and not the full MedQuAD corpus.

**Verification:**
- Independently hash the committed blob and compare it with the registry.
- Inspect ZIP structure without extracting files into Git history.

## Task 4: Implement offline registry validation

**Files:**
- Create: `app/backend/src/hospital_ai/data_sources/__init__.py`
- Create: `app/backend/src/hospital_ai/data_sources/registry.py`
- Create: `app/backend/scripts/validate_vendored_public_data.py`

**Behavior:**
- parse `sources.json` through immutable Pydantic models;
- reject absolute paths and `..` traversal;
- require source ID, upstream identity, license, attribution, intended use, limitations, expected size, and lowercase SHA-256;
- hash artifacts in chunks;
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
- Update: any references found by repository search.

**Behavior:**
- preserve the existing two-note Graph RAG development fixture;
- rename constants, MRNs, patient labels, log messages, and comments to explicitly say synthetic/mock;
- do not imply MIMIC provenance;
- add no replacement network downloader.

**Verification:**
- Search branch for `tstadel/maccrobat`, `NOTEEVENTS.csv`, `MIMIC-`, `Mimic Patient`, and misleading success messages.
- Run relevant seed-script import/static tests.

## Task 6: Integrate public artifacts with corpus inventory without weakening quarantine

**Files:**
- Update: `app/backend/src/hospital_ai/evaluation/corpus_manifest.py`
- Update: `app/backend/tests/evaluation/test_corpus_manifest.py`

**Behavior:**
- represent approved vendored evaluation datasets separately from the existing six quarantined guideline/drug artifacts;
- preserve exact canonical patient counts and existing duplicate exclusion behavior;
- expose provenance/license fields from the public source registry;
- do not ingest MedQuAD as patient data or automatically place it in the clinical knowledge base.

**TDD sequence:**
- add failing manifest tests first;
- implement the minimal new artifact kind/collection;
- run all evaluation manifest tests.

## Task 7: Add offline CI validation and deployment documentation

**Files:**
- Update: the most appropriate existing backend CI workflow under `.github/workflows/`
- Update: `README.md`
- Create or update: dataset documentation under `docs/`

**Behavior:**
- CI checks out the repository and invokes the offline validator;
- no `curl`, `wget`, Hugging Face loader, or dataset download step is introduced;
- README explains that clone/pull includes the public artifact;
- VPS documentation explains that source deployments receive it automatically, while Docker images receive it only if the build context/Dockerfile copies the data directory;
- state repository-size governance for future datasets.

**Verification:**
- inspect workflow diff for network dataset operations;
- run YAML/static workflow tests already present in the repo;
- run documentation link checks if available.

## Task 8: Full local-equivalent verification and self-review

**Commands/checks:**
- `python app/backend/scripts/validate_vendored_public_data.py`
- backend targeted tests for data sources and corpus manifest;
- full backend pytest suite where environment permits;
- Ruff check for modified Python files;
- existing repository contract/workflow tests;
- compare branch against `main` for unintended files and oversized artifacts.

**Review:**
- verify source/license claims against upstream documentation;
- verify no secrets, PHI, gated data, or generated cache files were committed;
- verify the branch does not claim clinical validity;
- verify source data reaches VPS by clone/pull and is not runner-only.

## Task 9: Push and open draft pull request

**Steps:**
- [ ] Confirm branch head and clean intended diff.
- [ ] Push feature branch.
- [ ] Open a draft PR to `main` with scope, source, license, size impact, tests, limitations, and deployment behavior.
- [ ] Request review or submit a structured self-review if no independent reviewer is configured.

## Task 10: CI log and fix loop

**Loop:**
1. Fetch workflow runs for the exact PR head SHA.
2. Wait only by re-querying in the current session; do not assume success from an older SHA.
3. For each failed job, fetch steps and complete logs.
4. Apply `superpowers:systematic-debugging`: identify root cause before editing.
5. Add or adjust a reproducing test when applicable.
6. Commit the minimal fix to the same branch.
7. Re-review the fix diff.
8. Fetch CI for the new head SHA.
9. Repeat until checks are green or a genuine external blocker is documented.

## Completion criteria

- The official compact MedQuAD judged-set artifact is committed in the repository.
- Registry and offline validator verify exact bytes, license, provenance, and limitations.
- CI performs no external dataset download.
- Misleading MIMIC/MACCROBAT scripts are removed or accurately renamed.
- Existing synthetic corpus/quarantine guarantees remain intact.
- Draft PR exists with source-backed documentation.
- Latest-head CI is green, or any unresolvable external blocker is evidenced with exact job/log details.
