# Task 3 report — Source-backed RAG benchmark

## Delivered

- Replaced generated canonical-fact and runtime chunk-ID fixtures with immutable `EvalCaseV2`, `ExpectedFact`, `GraphExpectation`, `ReviewRecord`, and `BenchmarkValidationResult` contracts.
- Built exactly 300 deterministic cases from the Task 2 `CorpusManifestV2` and canonical PDF/CSV sources:
  - 70 `single_hop`
  - 50 `multi_document`
  - 35 `temporal_conflict`
  - 45 `graph_multi_hop`
  - 30 `overlapping_patient`
  - 45 `permission_adversarial`
  - 25 `safe_refusal`
- Grounded answer facts in `EvidenceLocator` paths plus real PDF page or CSV row positions. Answer cases include other-patient forbidden evidence; refusal cases contain no allowed evidence.
- Added deterministic proportional sentinel selection (50 cases) and persisted draft artifacts under `app/backend/data/evaluation/`.
- Added a review gate requiring `approved` status, two distinct reviewer identities, and no unresolved issues for every sentinel case.
- Generated cases and the checked-in sentinel remain `draft` with no reviewer identities. No human or agent review was fabricated.
- Replaced the old benchmark CLI with `scripts/build_rag_benchmark.py --manifest <path> --output-dir <path> [--check]` and removed the old v1 generated-fact artifacts.

## TDD and verification

The first focused run failed during collection because `CATEGORY_COUNTS` and the new contracts did not exist. After the initial implementation, the persistence test failed because the sentinel had not yet been generated. A later source-type regression test failed on a real `imaging_report` source and exposed a hard-coded `lab_result` label; the builder now derives document-type facts from each manifest artifact.

Run from `app/backend` on 2026-07-22:

```text
py -3.12 -m pytest tests/evaluation -q
16 passed

py -3.12 -m ruff check src/hospital_ai/evaluation/benchmark.py tests/evaluation/test_benchmark.py scripts/build_rag_benchmark.py
All checks passed!

py -3.12 -m ruff format --check src/hospital_ai/evaluation/benchmark.py tests/evaluation/test_benchmark.py scripts/build_rag_benchmark.py
3 files already formatted
```

The CLI wrote 300 benchmark cases and 50 draft sentinel cases. Its `--check` mode returned exit code `3` with `sentinel review gate blocked`, as required for the truthful current state. A temporary fixture-only test using two explicit independent reviewer IDs passes the review gate; those fixture identities were not persisted.

GitNexus pre-edit impact checks reported LOW risk with no callers or execution flows for the replaced benchmark symbols. The staged `detect_changes` check also reported LOW risk and no affected execution flows.

## Release status

The benchmark content and deterministic generation gates pass. The sentinel review release gate is intentionally **blocked** until two real independent reviewers approve every sentinel case and resolve all review issues.
