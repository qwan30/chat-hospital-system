# CDI V2 Release Gates

## Release Criteria

Before any CDI V2 functionality can be enabled in production, the following machine-readable release gates must pass:

1. **`migration_chain`**: Database migration must pass `alembic check` with no un-applied or dropped states.
2. **`legacy_parity`**: The legacy corpus v1/v2 pipeline must generate exact parity with v3 for existing data.
3. **`zero_unauthorized_evidence`**: RAG context must strictly exclude cross-tenant or unapproved source segments.
4. **`zero_wrong_patient_citations`**: Citations must only reference documents attached to the target patient.
5. **`zero_superseded_retrieval`**: Once a generation is superseded, its contents must not surface in standard RAG queries.
6. **`graph_provenance_coverage`**: 100% of generated knowledge graph edges must link to a valid source node.
7. **`claim_validation`**: Every LLM generation claim must be verified against source text.
8. **`sentinel_two_reviewers`**: At least two independent reviewers must sign off on the sentinel 50-case holdout dataset.
9. **`threshold_artifact_frozen`**: Performance metric thresholds must be frozen and SHA-signed.
10. **`hash_reproducibility`**: Source parsing must be reproducible via hash.
11. **`ocr_strata_reported`**: Metrics for each OCR difficulty stratum (e.g., handwriting, low contrast) must be published.

These gates are verified automatically by the CI pipeline and via `verify_cdi_v2_release.py`. Any missing or failed gate results in an immediate `NO-GO` release decision.
