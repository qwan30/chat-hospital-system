# HOSP-AI-001 Synthetic Dataset

This package was generated from `dataset_generation_instruction.md` for end-to-end ingestion testing: file upload, OCR/text parsing, chunking, embedding, Graph RAG, RBAC/ABAC, and audit logging.

## Important Safety Notice
All clinical content is synthetic. It is not medical advice and must not be used for patient care.

## Normalization Applied
The uploaded `patients_100.xlsx` starts at MRN-0006 and ends at MRN-0105. The generated dataset normalizes the MVP scope to MRN-0001 through MRN-0100. MRN-0001 to MRN-0003 use the migration seed identities. MRN-0004 and MRN-0005 are synthetic filler records. MRN-0006 to MRN-0100 come from the uploaded patient workbook. MRN-0101 to MRN-0105 are intentionally excluded.

## Contents
- `app/backend/data/patients_documents/`: 100 patient PDF documents.
- `app/backend/data/patients_labs/`: 100 per-patient CSV lab trend files.
- `app/backend/data/drugs/drug_interaction_matrix.csv`: 500 medication safety rows.
- `app/backend/data/guidelines/nursing/`: 5 nursing guideline Markdown files.
- `app/backend/data/security/audit_logs.jsonl`: 10,000 synthetic audit logs.
- `app/backend/data/metadata/ingestion_metadata.jsonl`: patient-file metadata payloads.
- `app/backend/data/metadata/generated_patients_seed.csv`: normalized patient seed records and deterministic UUIDs.

## Suggested Project Copy Command
From the extracted package root, copy the `app/backend/data` directory into your project root:

```bash
cp -R app/backend/data /path/to/chatbot-hospital-system/app/backend/
```

## Notes
The lab trend files are CSV instead of XLSX because the instruction allows `.xlsx` or `.csv` for lab trend sheets. CSV keeps ingestion simple and parser-friendly while preserving the required lab columns.
