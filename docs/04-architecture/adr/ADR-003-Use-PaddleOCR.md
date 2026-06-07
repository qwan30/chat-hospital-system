# ADR-003: Use PaddleOCR/PP-OCR as default OCR

## Metadata
- **ID:** ADR-003
- **Status:** Accepted
- **Decided by:** System Architect / Tech Lead
- **Date:** 2026-04-27
- **Last Updated:** 2026-06-07

## Context
Hospital records include scanned PDF charts, hand-signed consent forms, and physical lab printouts that must be converted into machine-readable text to be indexed and searched. We need an OCR engine that is highly accurate on structured medical layout texts, performs well on CPU and consumer GPUs (to align with the local 16GB RAM limit), and supports Vietnamese and English medical forms.

## Decision
We chose PaddleOCR (PP-OCR model series) as the default open-source OCR engine.

## Alternatives Considered
- **Tesseract OCR:** Wide language support and extremely lightweight, but struggles significantly with complex layouts, multi-column tables, low-contrast scans, and tilted paper angles.
- **Cloud OCR Services (AWS Textract, Google Cloud Document AI):** Extremely accurate with advanced layouts, but excluded due to local-first privacy requirements (zero external PHI leakage).

## Consequences
- **Pros:**
  - Excellent accuracy on complex layouts (multi-column tables, medical lists).
  - High performance, lightweight footprint, runs easily on low-power servers/CPUs.
  - Native multi-language support including robust Vietnamese recognition models.
- **Cons:**
  - Requires setting up a Python background worker process (Celery/Redis) to handle intensive OCR CPU/GPU tasks asynchronously.
  - Installation can be complex due to C++ dependency binaries (PaddlePaddle).
