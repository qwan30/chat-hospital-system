---
name: healthcare-rag-graph-ocr-evaluation
description: Evaluate healthcare OCR, CSV ingestion, RAG, Graph RAG, citations, authorization, PHI protection, and sync/SSE parity. Use for healthcare AI release gates, regression tests, incident analysis, and safety reports.
---

# Healthcare RAG, Graph RAG, and OCR Evaluation

## Build adversarial ground truth

1. Include expected answer, supporting citation, requesting actor, permission state, patient scope, and expected refusal for every case.
2. Include overlapping patient facts, revoked or expired permissions, soft-deleted documents and pages, mismatched joins, temporal conflicts, and no-evidence questions.
3. Pair scan/image PDF fixtures with known text and CSV fixtures with malformed, duplicate, and sensitive rows. Measure OCR completion, extraction fidelity, and failure classification separately.

## Gate retrieval before generation

1. Assert authorization before retrieval and at every patient-document-page-chunk or graph-relation join.
2. Assert that zero unauthorized chunks, relations, or metadata reach the model context.
3. Evaluate recall, precision, evidence fidelity, and answer usefulness. Do not accept citation presence as proof that the citation supports the claim.
4. Verify graph edges respect tenant, patient, lifecycle, and relation-type scope. Test graph enrichment independently from vector retrieval.

## Enforce clinical safety and PHI controls

1. Require grounded citations for evidence-backed claims and safe refusal when evidence is absent, unauthorized, or insufficient.
2. Verify redaction and logs do not disclose PHI, prompts, raw chunks, or identifiers outside the requester’s scope.
3. Record retrieval trace, cited-only evidence, policy outcome, and sanitized error outcome for accepted and refused requests.

## Compare transports and releases

1. Run equivalent cases through synchronous chat and SSE/streaming chat. Compare authorization, retrieval, citation validation, refusal, audit, trace persistence, and error sanitization.
2. Keep deterministic fixture gates separate from live-model evaluation. A mocked browser response is not production evidence.
3. Block release on any permission leak, uncited clinical assertion, unsupported citation, transport-parity failure, or unclassified OCR failure.
