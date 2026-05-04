# Discovery — Codebase Audit 2026-05

_Populated during Phase 1 (`khuym:exploring`)._

## GitNexus Baseline

- Repo: `chatbot-hospital-system`
- Files: 209 | Nodes: 1989 | Edges: 5286 | Processes: 162 | Communities: 71 | Embeddings: 904 (pre-audit snapshot).

## Exploration Queue

### Security concepts
- [ ] `permission filter` / `patient scope`
- [ ] `PHI sanitization` / `error sanitization`
- [ ] `bearer token` / `auth validation`
- [ ] `CORS`
- [ ] `input validation` / `schema validation`
- [ ] `SQL injection` / raw SQL
- [ ] `file upload` / `OCR` / `path traversal`
- [ ] secrets / env loading

### Bug / edge-case concepts
- [ ] `AbortController` lifecycle
- [ ] `SSE streaming` error paths
- [ ] citation validation / orphaned citations
- [ ] empty-evidence / honest no-answer paths
- [ ] unhandled promise / bare except / swallowed errors
- [ ] retry / DLQ / worker queue

### Structure concepts
- [ ] cluster inventory
- [ ] process-to-file layering
- [ ] circular dependencies (via `gitnexus_cypher`)

### RAG / clinical safety concepts
- [ ] retrieval → LLM context pipeline
- [ ] permission-before-retrieval ordering
- [ ] chunk ownership metadata

### Testing gaps
- [ ] permission test coverage
- [ ] RAG leakage test coverage

## Findings Log

Format: `[area] symbol/process — observation — severity-guess — evidence`

(empty — to be filled)
