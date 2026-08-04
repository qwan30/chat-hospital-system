# Public Data Governance Foundation

**Date:** 2026-08-04  
**Status:** Implemented by PR #86  
**Scope:** Governance contracts and misleading-script cleanup only

## Purpose

This change establishes reusable provenance and integrity contracts for public-source artifacts without choosing or committing a product dataset.

The foundation supports future qualification data and the later unified clinical corpus, while keeping those concerns outside the canonical patient benchmark until their end-to-end design is approved.

## Decisions

1. No MedQuAD or other standalone public dataset is committed by this change.
2. Public qualification artifacts are not registered as canonical patient-corpus artifacts.
3. Backend container images do not bundle `data/public/**`.
4. GitHub Actions does not download or validate a repository-wide public dataset in this change.
5. A source registry is validated only when a caller supplies both the registry path and the local artifact root explicitly.
6. Registered local artifacts are checked fail-closed for path containment, byte size, and SHA-256.
7. Public source metadata records upstream revision, license, attribution, intended use, limitations, and artifact identity.
8. Misleading scripts that presented hand-authored or unrelated data as MIMIC/MACCROBAT clinical notes are removed or renamed.

## Included components

- `hospital_ai.data_sources.registry`: immutable Pydantic contracts and offline validation.
- `scripts/validate_public_source_registry.py`: explicit command-line entry point.
- `scripts/seed_mock_clinical_notes.py`: deterministic synthetic Graph RAG fixture with honest naming.
- data-governance tests using temporary artifacts rather than a committed product dataset.

## Explicit non-goals

This foundation does not:

- define the final unified corpus;
- add public medical knowledge to chat;
- add OCR input documents;
- change the canonical 300-case benchmark;
- change the corpus manifest;
- copy data into Docker images;
- download data in CI;
- claim clinical validity or training suitability.

## Example validation

```bash
cd app/backend
python scripts/validate_public_source_registry.py \
  --data-root /path/to/staged/artifacts \
  --registry /path/to/sources.json
```

No default registry is assumed. A future workflow must pass an explicit versioned registry belonging to the approved qualification set or unified corpus.

## Follow-up

The full OCR → revision history → approved indexing → Graph RAG → timeline → grounded-chat corpus is specified separately. That follow-up will decide R2 layout, corpus item identity, benchmark partitions, and which smoke slice—if any—belongs in Git.
