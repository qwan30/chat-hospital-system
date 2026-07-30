# Task 2 — Corpus contracts and manifests

Implement only the source-backed corpus governance foundation under `app/backend/src/hospital_ai/evaluation/` and `app/backend/tests/evaluation/`.

Create immutable Pydantic v1 contracts named `CorpusManifestV2`, `SourceArtifact`, and `EvidenceLocator`. Each artifact must record source SHA-256, canonical relative source path, kind, patient UUID where applicable, MIME type, document type, generator/version, provenance/license status, access tags, and duplicate-of reference where applicable.

Create a deterministic manifest builder for canonical roots only:

- `data/patients_documents`: exactly 100 PDFs.
- `data/patients_labs`: exactly 100 patient CSVs.
- `data/metadata/ingestion_metadata.jsonl`: 200 patient metadata records.
- `data/metadata/generated_patients_seed.csv`: 100 patient rows.

Detect duplicate files by SHA-256 across all data roots and exclude noncanonical duplicates from `artifacts`; do not delete files. Keep `data/drugs/drug_interaction_matrix.csv` and `data/guidelines/**` in `quarantined_public_artifacts`, never in patient artifacts. Audit logs are not truth sources.

Validate source paths are under the backend data root, every patient-owned artifact maps to metadata/known patient identity, hash values are 64 lowercase hexadecimal, and public records have no patient UUID. Expose a CLI script `scripts/build_eval_manifest.py` with `--output <path>` and `--check` modes. `--check` must fail with exit 2 on invalid manifest/data.

Use TDD. Add focused tests that avoid hardcoded absolute paths and assert expected inventory counts, public quarantine, deterministic hashes, duplicate exclusion, and locator serialization. Do not modify the existing generated benchmark yet. Commit only Task 2 files. Write report to `.superpowers/sdd/task-2-report.md`.
