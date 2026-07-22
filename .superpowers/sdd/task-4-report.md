# Task 4 report — deterministic evaluation engine

## Outcome

Implemented a source-backed evaluation runner with immutable result contracts, pure metrics, deterministic OCR scan fixtures, adapter-isolated product evaluation, explicit live/OCR unavailable states, and four report artifacts.

The runner does not synthesize product scores when no product adapter or live credentials are configured. Deterministic adapter skips and harness self-tests are labelled as not product quality evidence.

## Delivered files

- `app/backend/src/hospital_ai/evaluation/contracts.py`
- `app/backend/src/hospital_ai/evaluation/metrics.py`
- `app/backend/src/hospital_ai/evaluation/ocr_evaluation.py`
- `app/backend/src/hospital_ai/evaluation/runner.py`
- `app/backend/src/hospital_ai/evaluation/reporting.py`
- `app/backend/scripts/run_ai_evaluation.py`
- `app/backend/tests/evaluation/test_metrics.py`
- `app/backend/tests/evaluation/test_ocr_evaluation.py`
- `app/backend/tests/evaluation/test_evaluation_runner.py`

## Contract and gate behavior

- CLI supports `--suite smoke|release`, `--lane deterministic|live`, requested component subsets, and explicit output/data/benchmark paths.
- Exit `0`: requested gates pass or a live-only run is explicitly skipped for missing provider configuration.
- Exit `1`: a valid evaluation dataset fails a gate, including draft sentinel review or unavailable/unexecuted image OCR.
- Exit `2`: invalid suite/lane/components or invalid/missing corpus and benchmark inputs.
- Outputs: `run.json`, `cases.jsonl`, `junit.xml`, and `summary.md`.
- Safety gates cover unauthorized evidence, wrong-patient evidence/citations, fabricated citations, provenance, refusal behavior, sync/SSE parity, critical fields, and unsupported clinical claims.
- Paddle dependencies are probed independently of native PDF text. Missing dependencies report `engine_unavailable`; installed-but-unexecuted dependencies report `engine_available_not_run`. Neither state receives a native-text-derived OCR score.

## TDD evidence

Tests were added and observed failing for each new module before implementation:

- Metrics: import failure before `metrics.py`; then 8 passing tests.
- OCR: import failure before `ocr_evaluation.py`; then 4 passing tests.
- Runner: import failure before `runner.py`; then 11 passing tests.
- Machine-readable scalar regression: observed numeric metrics coerced to strings, then fixed with strict scalar contracts.
- Sentinel review count regression: observed `-50` for a draft 50-case sentinel, then fixed to report `0` approved cases.

## Verification

- `py -3.12 -m pytest tests\evaluation -q` → `44 passed in 60.10s`.
- `py -3.12 -m ruff check src\hospital_ai\evaluation tests\evaluation scripts\run_ai_evaluation.py` → passed.
- `py -3.12 -m ruff format --check src\hospital_ai\evaluation tests\evaluation scripts\run_ai_evaluation.py` → 13 files already formatted.
- Real CLI deterministic corpus smoke produced all four artifacts and returned `1`, correctly identifying the repository's draft sentinel as a gate failure.
- Coverage measurement was attempted, but `pytest-cov` is not installed in the active Python 3.12 environment; pytest rejected the `--cov` options. No coverage percentage is claimed.

## Honest blockers recorded by the runner

- The checked-in sentinel remains draft and therefore blocks smoke/release gates until two real independent reviewers approve every case with no unresolved issues.
- PaddleOCR/PaddlePaddle image recognition is not executed by this deterministic runner. OCR remains a failing requested component until a real image-OCR adapter runs the controlled scan variants.
- Retrieval, Graph RAG, and chat cases are explicitly skipped without a configured adapter; no fallback scores are emitted.
