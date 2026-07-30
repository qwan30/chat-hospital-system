# Task 4 — Deterministic evaluation engine and reports

Implement a deterministic evaluation engine on top of Tasks 2 and 3. Keep all product-service calls behind adapters so tests do not need a live model.

Create versioned result contracts: `RunManifest`, `CaseResult`, `GateResult`, `OcrGoldPage`, and metric result types. Add pure metrics for character/word error rate, numeric critical-field accuracy, CSV structural accuracy, retrieval Recall@K/Precision@K/MRR/nDCG, citation precision/recall, fact coverage, refusal success, and safety leak counts.

Implement reproducible scan-variant generation from PDF pages using deterministic seeds and separate native PDF-text versus rendered-image fixture results. If PaddleOCR/PaddlePaddle is unavailable, report `engine_unavailable` and fail the image-OCR component explicitly; never mark it passing from native extraction.

Implement `scripts/run_ai_evaluation.py`:

`--suite smoke|release --lane deterministic|live --components corpus,ocr,retrieval,graph,chat --output-dir PATH`

It must write `run.json`, `cases.jsonl`, `junit.xml`, and `summary.md`. It must return 0 for a passing requested suite, 1 for gate failure, and 2 for invalid configuration/dataset. Live lane must be explicitly `skipped` with a reason when provider credentials/config are absent; it must never return synthetic 1.0 scores.

Deterministic smoke must run corpus validation, the frozen sentinel, pure metric fixtures, and report generation without external services. Release must validate all benchmark cases and record unavailable external components as failures/skips according to their requested component. Include hard gates for zero unauthorized/wrong-patient evidence, fabricated citations, unsafe refusal, missing provenance, and transport safety parity fixtures.

Use TDD and focused tests for every metric, artifact shape, exit code, unavailable OCR/live behavior, deterministic seed, and hard-gate failure. Do not modify chat/OCR/Graph product code in this task. Commit only Task 4 files and report to `.superpowers/sdd/task-4-report.md`.
