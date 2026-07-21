# HOSP-AI-001 Synthetic Dataset

This package was generated from `dataset_generation_instruction.md` for end-to-end ingestion testing: file upload, OCR/text parsing, chunking, embedding, Graph RAG, RBAC/ABAC, and audit logging.

## Important Safety Notice
All clinical content is synthetic. It is not medical advice and must not be used for patient care.

## Normalization Applied
The uploaded `patients_100.xlsx` starts at MRN-0006 and ends at MRN-0105. The generated dataset normalizes the MVP scope to MRN-0001 through MRN-0100. MRN-0001 to MRN-0003 use the migration seed identities. MRN-0004 and MRN-0005 are synthetic filler records. MRN-0006 to MRN-0100 come from the uploaded patient workbook. MRN-0101 to MRN-0105 are intentionally excluded.

## Canonical Corpus Contract
The canonical raw corpus lives in the repository at `app/backend/data/`; this
directory retains its immutable manifest and provenance notes only. The former
nested `app/backend/data` copy was removed after a complete SHA-256 pairing
against the canonical files.

- `patients_documents/`: 100 patient PDF records.
- `patients_labs/`: 100 per-patient CSV lab trend records.
- `metadata/generated_patients_seed.csv`: deterministic MRN-to-patient UUID ownership.
- `drugs/` and `guidelines/nursing/`: synthetic public knowledge, quarantined from
  runtime retrieval as `excluded_pending_review` until provenance and licensing
  review is complete.
- `security/` and remaining `metadata/` files: synthetic audit and metadata fixtures.

`MANIFEST.json` is generated from these canonical paths. Regenerate and validate
it from `app/backend` with:

```bash
python scripts/validate_rag_corpus.py \
  --data-root data \
  --write-manifest data/hosp_ai_synthetic_dataset/MANIFEST.json
```

The validator streams SHA-256 digests, rejects path escapes and unsupported MIME
types, enforces deterministic patient ownership, and returns all detected
validation errors in one result.

## Notes
The lab trend files are CSV instead of XLSX because the instruction allows `.xlsx` or `.csv` for lab trend sheets. CSV keeps ingestion simple and parser-friendly while preserving the required lab columns.
