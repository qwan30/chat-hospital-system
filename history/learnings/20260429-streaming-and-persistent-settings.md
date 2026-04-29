# Streaming RAG and Persistent Settings Learnings

- **Feature**: streaming-rag-and-persistent-settings
- **Date**: 2026-04-29
- **Scope**: SSE streaming, settings store, worker DLQ, GraphRAG

## Learnings

### 1. Streaming RAG Client-Side Lifecycle
Streaming responses (SSE) in a React chat interface require robust `AbortController` management. If a user navigates away or starts a new question while a stream is active, the previous stream must be explicitly aborted to prevent "zombie" UI updates and orphaned backend processing.
- **Pattern**: Use `useRef` for the `AbortController` and cleanup in `useEffect` or before starting a new request.
- **Contract**: Ensure `onDone` and `onError` callbacks are resilient to the component being unmounted.

### 2. Database-Backed Settings vs. Environment Variables
Clinical workflows often require runtime tuning (e.g., retrieval `top_k`, safe-refusal thresholds) that shouldn't require a container restart or deployment.
- **Decision**: Migrate critical "tuning" parameters to a persistent `SettingsStore` (PostgreSQL/Alembic).
- **Pattern**: Use a `SettingsStore` singleton with a cache-aside pattern to avoid database roundtrips on every RAG request.

### 3. Worker DLQ and Retry Backoff
Processing medical documents is high-latency and prone to transient failures (OOM, LLM rate limits).
- **Pattern**: Implement an explicit `dead_letter_queue` and exponential backoff for worker jobs.
- **Learning**: Failing fast and moving to a DLQ is safer than infinite retries which can starve the worker pool for urgent clinical queries.

### 4. GraphRAG Reasoners
Linear RAG (vector search only) often fails to connect disparate evidence across large patient records.
- **Pattern**: Introduce a `GraphRAG` reasoner that maps entities and relationships before synthesis.
- **Observation**: This significantly improves answer usefulness for complex "how is X related to Y" clinical questions.

## Actionable Patterns to Promote

- [ ] [Pattern] Streaming Chat Lifecycle with AbortController
- [ ] [Pattern] SettingsStore for Dynamic Configuration
- [ ] [Pattern] Worker Retry with Dead-Letter Support
