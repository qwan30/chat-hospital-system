---
name: ai-eval-dataset-governance
description: Govern AI evaluation datasets with inventory, source hashes, provenance, duplicate policy, immutable ground truth, review status, and public/private boundaries. Use before curating, changing, sharing, or evaluating an AI corpus.
---

# AI Evaluation Dataset Governance

## Inventory every source

1. Record a stable dataset ID, logical split, source URI or owner, acquisition date, license or consent status, classification, and intended evaluation use.
2. Hash every canonical source file with SHA-256. Preserve the raw source separately from derived chunks, OCR text, embeddings, and labels.
3. Store a manifest revision with the exact file paths, hashes, schema version, and generation tool version.

## Apply duplicate and boundary policy

1. Detect exact duplicates by source hash before ingesting. Remove only verified duplicates and preserve the retained canonical source.
2. Flag semantic near-duplicates for human review; do not silently merge conflicting clinical, temporal, or permission-bearing records.
3. Separate public knowledge from private or patient evidence. Exclude unreviewed public material from runtime retrieval until provenance and license review pass.
4. Prevent private data, PHI, credentials, and access-controlled labels from entering public fixtures, exports, prompts, or reports.

## Freeze ground truth

1. Version ground-truth questions, expected answers, citations, requesting actor, authorization state, refusal expectation, and evaluator rubric together.
2. Make released ground-truth revisions immutable. Create a new revision with review rationale instead of editing accepted labels in place.
3. Require independent review status for every new or changed record: `draft`, `reviewed`, `approved`, or `rejected`.
4. Fail the evaluation gate when a required hash, provenance field, review, or boundary classification is missing.

## Report dataset readiness

1. State the manifest revision, record counts, duplicate decisions, reviewed fraction, unresolved exceptions, and permitted uses.
2. Do not claim dataset readiness from schema validation alone; verify source availability, hashes, and review evidence.
