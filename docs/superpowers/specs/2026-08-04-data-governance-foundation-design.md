# Public Data Governance Foundation — Design Specification

**Spec ID:** DATA-GOV-001  
**Date:** 2026-08-04  
**Status:** Ready for merge  
**Relationship:** Foundation for the later unified Clinical Document Intelligence specification

## 1. Goal

Provide trustworthy, reusable contracts for describing and validating public-source artifacts while avoiding premature integration of an unrelated dataset into the product corpus.

## 2. Problem

The repository contained scripts and naming that could imply external clinical provenance where the records were actually hand-authored or mapped from an unrelated source. The first PR direction also attempted to commit five MedQuAD XML files and classify them as an approved evaluation dataset.

That approach conflicts with the later requirement that the headline product benchmark use one logical corpus across OCR, correction, indexing, Graph RAG, timeline, chat, and evaluation.

## 3. Architecture

### 3.1 Source registry

A registry contains:

- stable source ID;
- source name;
- upstream repository and pinned commit;
- SPDX license and attribution;
- retrieval timestamp;
- intended use;
- limitations;
- artifact upstream path;
- local staged path;
- media type;
- byte size;
- SHA-256;
- upstream blob SHA.

### 3.2 Offline validation

Validation is side-effect free and fail-closed:

```text
explicit registry path
+ explicit local data root
→ schema validation
→ relative-path validation
→ containment check
→ file existence
→ byte-size check
→ SHA-256 check
→ immutable validation result
```

The validator never downloads, repairs, rewrites, or registers data into the product corpus.

### 3.3 Product boundaries

This foundation must remain independent from:

- `evaluation/corpus_manifest.py`;
- canonical patient artifacts;
- active chat knowledge;
- Docker image contents;
- deployment workflow behavior;
- R2 runtime storage;
- the unified corpus version.

## 4. Script cleanup

- Delete `download_hf_notes.py`; it installed dependencies at runtime, used a hard-coded Windows output path, and transformed MACCROBAT into misleading `NOTEEVENTS.csv` semantics.
- Rename `seed_mimic.py` to `seed_mock_clinical_notes.py`.
- Use `MOCK-*` identifiers while cleaning up legacy `MIMIC-*` rows during migration.
- Preserve the deterministic Graph RAG development fixture behavior.

## 5. Repository policy

PR #86 must not contain:

- MedQuAD XML artifacts;
- a repository-wide `data/public/sources.json` product registry;
- `approved_public_artifacts` or `public_evaluation_dataset` corpus fields;
- `COPY data/public/ data/public/` in the backend image;
- a dedicated vendored-public-data workflow;
- unrelated CD workflow compatibility edits.

## 6. Testing

Tests must prove:

- a temporary registered artifact validates successfully;
- path traversal is rejected before file access;
- the canonical corpus contains no public-qualification integration;
- Docker does not bundle a standalone public dataset;
- the repository contains no standalone MedQuAD product fixture;
- misleading legacy scripts are absent and the mock seed is present.

## 7. Acceptance criteria

- Generic registry and validator remain reusable.
- No dataset is selected by this PR.
- Canonical benchmark behavior is unchanged from `main`.
- Deployment and container behavior are unchanged from `main`.
- Script naming reflects actual provenance.
- Full CI is green on the final head SHA.
- PR description explicitly defers corpus selection and R2 integration to the unified Clinical Document Intelligence design.
