# Task 5 report — CI evaluation integration

## Outcome

Replaced the pass-by-construction RAG CI check with the source-backed AI evaluation runner. The deterministic lane is now blocking, produces the four required artifacts on every invocation, and runs the 50-case sentinel for pull requests or the 300-case suite for main, scheduled, and manual runs.

Requested retrieval, Graph RAG, and chat components now require a real evaluation adapter. A missing adapter produces a hard `evaluation_adapter_configured` gate failure; it can never turn skipped case rows into a passing component. The PR lane is therefore deliberately scoped to corpus/sentinel-contract validation. Main, nightly, and manual release lanes request corpus, controlled-scan OCR, retrieval, Graph RAG, and chat, and will remain honestly failing until those real adapters and OCR engine are configured.

The optional live lane is available only through an explicit `workflow_dispatch` boolean and runs only after the deterministic job passes. Missing provider configuration remains visible in the runner artifact as `skipped`; no synthetic `1.0` score is emitted.

## Delivered files

- `.github/workflows/ci.yml`
- `app/backend/tests/test_ci_workflow.py`
- `app/backend/tests/test_rag_eval.py` (removed)
- `README.md`

## CI behavior

- Pull requests run `smoke` with `corpus` against the source-backed 50-case sentinel. This validates the corpus and review contract; it does not claim product quality.
- Main pushes, nightly schedule, and manual runs run `release` against all 300 cases with `corpus,ocr,retrieval,graph,chat`.
- The old `continue-on-error: true` and `pytest tests/test_rag_eval.py` path are removed.
- `run.json`, `cases.jsonl`, `junit.xml`, and `summary.md` are uploaded with `if: always()` and `if-no-files-found: error`.
- The live lane is manual, credential-scoped, and depends on a successful deterministic gate.
- CI summary includes deterministic and live evaluation results.

## TDD evidence

### RED

`py -3.12 -m pytest tests\\test_ci_workflow.py -q` produced two failures before implementation: the deterministic job lacked the direct `changes` dependency/source-backed runner, and `live-ai-evaluation` did not exist.

A README regression test then failed on the obsolete `6/6 RAG synthetic evaluation` claim.

### GREEN

- `py -3.12 -m pytest tests\\test_ci_workflow.py -q` -> `4 passed`.
- `py -3.12 -m pytest tests\\evaluation tests\\test_ci_workflow.py tests\\test_golden_dataset.py -q` -> `51 passed, 1 skipped`.
- Ruff check passed for the evaluation sources, tests, workflow contract test, and runner CLI.
- Ruff format check passed for 13 files.

## Real runner evidence

The checked-in corpus smoke command returned exit `1` and emitted exactly `cases.jsonl`, `junit.xml`, `run.json`, and `summary.md`. This is the expected honest result: the 50-case sentinel remains draft and blocks release until two independent reviewers approve it with no unresolved issues. The checked-in full release command also selected all 300 cases and returned exit `1` with `sentinel_independent_review`, `image_ocr_executed`, and three `evaluation_adapter_configured` blockers. A deterministic request for an unbound product component therefore cannot report skipped rows as a pass.

## Impact and integrity review

GitNexus reported LOW risk for `test_rag_eval`, `evaluate_with_llm`, and `test_ci_workflow_parsing_and_structure`, with no affected product process. No product chat, retrieval, Graph RAG, OCR, or authorization symbol was modified.

README badges and metrics now identify the evaluation verdict as `CONDITIONAL`, link to the source-backed artifacts, and explicitly state that draft sentinel review blocks release.
