# BR-003: OCR Document Indexing

## Metadata
- **ID:** BR-003
- **Status:** approved
- **Owner:** Product Owner
- **Stakeholders:** Records Staff, Doctor, QA Lead
- **Priority:** Must
- **Target Quarter:** MVP

## Background
Hospitals generate large volumes of scanned documents (prescriptions, lab results, referral letters, discharge summaries) that are currently unsearchable. Staff must manually open and read each document to find relevant information.

## Goal
System can OCR and index medical documents so they become searchable via semantic search with page-level citations.

## Success Metrics
- Uploaded document becomes searchable after processing: 100% for supported formats
- OCR accuracy on clean scans: ≥90%
- Failed OCR documents are clearly flagged for review

## In Scope
- PDF and image upload
- OCR text extraction (PaddleOCR/PP-OCR)
- Chunking and embedding for vector search
- Document state tracking (Uploaded → Processing → Indexed/Failed)
- Batch upload with progress tracking
- Low-confidence OCR review workflow

## Out of Scope
- Handwriting recognition (MVP uses printed text only)
- Real-time document sync from external systems
- Document editing/annotation

## Related Use Cases
- UC-003: Upload and OCR Document
- UC-004: Search Documents Semantically

## Constraints
- **Technical:** CPU-mode OCR on 16GB RAM (slower but feasible)
- **Storage:** Original documents must be preserved alongside OCR output
- **Privacy:** Document content is PHI — same access controls apply

## Open Questions
- [ ] What document formats beyond PDF and PNG/JPG should be supported?
- [ ] What is acceptable OCR processing time for a single document?

## History
- v1 (2026-04-27, Original): Initial draft
- v2 (2026-06-07, Agent): Extracted to individual file
