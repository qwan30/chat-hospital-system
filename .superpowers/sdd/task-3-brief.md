# Task 3 — Source-backed benchmark

Implement only the real-source RAG benchmark on top of Task 2 contracts.

Replace `hospital_ai.evaluation.benchmark` generated canonical facts with `EvalCaseV2`, `ExpectedFact`, `GraphExpectation`, `ReviewRecord`, and `BenchmarkValidationResult` contracts using `EvidenceLocator` values, never generated/runtime chunk UUIDs. Build exactly 300 deterministic cases from the canonical manifest with these categories: 70 `single_hop`, 50 `multi_document`, 35 `temporal_conflict`, 45 `graph_multi_hop`, 30 `overlapping_patient`, 45 `permission_adversarial`, and 25 `safe_refusal`.

Each answer case must have source-backed expected facts, at least one allowed evidence locator, at least one forbidden locator from another patient where applicable, actor identity, patient scope, and answer/refusal policy. Permission-adversarial and safe-refusal cases must never include allowed evidence. Create a deterministic stratified 50-case sentinel and persist it under `app/backend/data/evaluation/`.

Do not mark cases agent-reviewed automatically. Generated cases must be `draft`; sentinel cases require an explicit review record and a gate must block release when a sentinel lacks two independent reviewer identities or has unresolved status. Use non-fabricated reviewer IDs only in tests/fixtures; do not claim human review.

Provide `scripts/build_rag_benchmark.py --manifest <path> --output-dir <path> [--check]`, retain no pass-by-construction benchmark tests, and add TDD tests for counts, source locator resolution, patient isolation, forbidden/allowed disjointness, review-gate behavior, and reproducibility. Commit only Task 3 files and report to `.superpowers/sdd/task-3-report.md`.
