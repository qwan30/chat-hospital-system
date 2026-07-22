# Task 2 report — Corpus contracts and manifests

## Delivered

- Added immutable Pydantic v1 contracts: `CorpusManifestV2`, `SourceArtifact`, and `EvidenceLocator`.
- Added a deterministic builder that validates the canonical 100-PDF, 100-CSV, 200-metadata-record, and 100-patient inventory.
- Patient artifacts map through ingestion metadata and the patient seed; paths, UUIDs, and SHA-256 values are validated before a manifest is returned.
- The five guideline files and drug-interaction matrix are quarantined as public, patient-free artifacts. Nested source copies are recorded as excluded duplicates and never enter the canonical patient inventory.
- Added `scripts/build_eval_manifest.py` with `--output` and `--check` modes.

## Verification

Run from `app/backend` on 2026-07-22:

```text
py -3.12 -m ruff check src/hospital_ai/evaluation/corpus_manifest.py tests/evaluation/test_corpus_manifest.py scripts/build_eval_manifest.py
All checks passed!

py -3.12 -m ruff format --check src/hospital_ai/evaluation/corpus_manifest.py tests/evaluation/test_corpus_manifest.py scripts/build_eval_manifest.py
3 files already formatted

py -3.12 -m pytest tests/evaluation -q
9 passed

py -3.12 scripts/build_eval_manifest.py --check
evaluation corpus manifest is valid
```

The CLI was also exercised with a temporary `--output` file followed by `--check --output`; both returned exit 0.

## Scope

Only Task 2 manifest contracts, CLI, tests, and this report are staged for its commit. Existing benchmark generation remains unchanged.
