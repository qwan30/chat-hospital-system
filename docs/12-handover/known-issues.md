# Known Issues

> Project: HOSP-AI-001 · Version: 1.0 · Owner: Tech Lead · Last Updated: 2026-06-14  

## 1. Technical Debt

| ID | Issue | Severity | Mitigation |
|----|-------|----------|------------|
| KI-001 | Deterministic embedding produces lower-quality retrieval than Ollama | MEDIUM | Use Ollama provider in dev/prod |
| KI-002 | Stub LLM returns templated answers — not for clinical accuracy testing | LOW | Use only for pipeline structure testing |
| KI-003 | In-memory embedding cache (2048 entries) not shared across workers | LOW | Use Redis cache when scaling |
| KI-004 | Smoke tests not integrated into CI | MEDIUM | Run manually; integrate into CI pipeline |
| KI-005 | Dev bearer tokens for local dev only — no OIDC discovery yet | MEDIUM | HMS JWT bridge exists; add OIDC |
| KI-006 | Graph RAG silently degrades when entity extraction fails | LOW | Best-effort; doesn't block retrieval |

## 2. Performance Constraints

| ID | Issue | Impact | Mitigation |
|----|-------|--------|------------|
| KI-007 | Qwen2.5 7B Q4 on 16GB RAM — concurrent requests risk OOM | MEDIUM | Use 3B for lighter loads; limit concurrency |
| KI-008 | PyMuPDF OCR CPU-only: 10-15s/page for scans | MEDIUM | Batch via RQ; optional PaddleOCR GPU |
| KI-009 | pgvector HNSW index builds CPU-intensive on large doc sets | LOW | Acceptable for MVP (<10K chunks) |

## 3. Test Coverage Gaps

| ID | Area | Status | Target |
|----|------|--------|--------|
| KI-010 | E2E tests for critical flows | Partial (some specs deleted) | Full critical path |
| KI-011 | RAG eval pipeline not automated | Manual script only | CI-integrated |
| KI-012 | No performance/load tests | None | Baseline benchmarks |

## 4. Security

| ID | Note | Severity |
|----|------|----------|
| KI-013 | dev_bearer_tokens refused in non-local (F-SEC-001) — verified safe | NONE |
| KI-014 | No automated dependency scanning in CI yet | MEDIUM |
| KI-015 | Rate limiting uses in-memory backend — resets on restart | LOW |

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | 15 issues across tech debt, performance, testing, security |
