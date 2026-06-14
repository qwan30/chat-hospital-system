# Technology Stack

> Project: HOSP-AI-001 — AI Hospital Knowledge Assistant  
> Version: 1.0 · Owner: System Architect · Last Updated: 2026-06-14  

## 1. Backend

| Category | Technology | Version |
|----------|-----------|---------|
| Framework | FastAPI | 0.95+ |
| Server | Uvicorn | 0.30+ |
| ORM | SQLAlchemy (async) | 2.0+ |
| Migrations | Alembic | 1.13+ (6 versions) |
| Database | PostgreSQL + pgvector | 16+ |
| Queue | RQ (Redis Queue) | 1.16+ |
| Cache | Redis | 5.0+ |
| Auth | PyJWT | 2.8+ |
| HTTP | HTTPX | 0.27+ |
| Rate Limit | slowapi | 0.1+ |
| OCR | PyMuPDF | 1.24+ |
| OCR (opt) | PaddleOCR | 3.0+ |
| Reranker (opt) | sentence-transformers | 2.2+ |
| Vector DB | pgvector | 0.3+ |
| LLM Local | Ollama (Qwen2.5 3B/7B) | latest |
| LLM Cloud | OpenAI-compatible | — |
| Packaging | Poetry | latest |
| Lint | Ruff | 0.6+ |
| Test | pytest + pytest-asyncio | 8.2+ |

## 2. Frontend

| Category | Technology | Version |
|----------|-----------|---------|
| Framework | Next.js (App Router) | 16.2 |
| UI Library | React | 19.2 |
| Language | TypeScript | 6.0 |
| Styling | Tailwind CSS | 4.2 |
| Components | shadcn/ui (Radix UI) | 4.5 |
| Forms | React Hook Form + Zod | 7.74 / 4.3 |
| Charts | Recharts | 3.8 |
| Animation | Motion (Framer Motion) | 12.38 |
| Icons | Lucide React | 1.11 |
| Tables | TanStack React Table | 8.21 |
| Toast | Sonner | 2.0 |
| Themes | next-themes | 0.4 |
| Command Palette | cmdk | 1.1 |
| Unit Test | Vitest | 4.1 |
| E2E Test | Playwright | 1.60 |
| Lint | ESLint | 9.39 |

## 3. LLM & AI

| Component | Technology |
|-----------|-----------|
| LLM Provider 1 | Ollama (Qwen2.5 3B/7B Q4 quantized) |
| LLM Provider 2 | OpenAI-compatible (Azure, Groq, Together, Mistral) |
| LLM Provider 3 | Stub (deterministic, testing only) |
| Embedding 1 | Ollama `/api/embed` |
| Embedding 2 | Deterministic (SHA-256 based, zero-dependency) |
| Embedding 3 | OpenAI text-embedding-3-small |
| Embedding Dim | 1024 (consistent across providers) |
| Retrieval 1 | pgvector HNSW (vector similarity) |
| Retrieval 2 | BM25 (probabilistic keyword) |
| Retrieval 3 | Hybrid (vector + BM25 combined) |
| Retrieval 4 | Graph RAG (entity relationship traversal) |
| Reranker | Cross-encoder (sentence-transformers, optional) |

## 4. Architecture Decisions

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-001 | FastAPI BFF | Single UI entry point, simpler than API Gateway |
| ADR-002 | PostgreSQL + pgvector | One DB for transactions + vectors |
| ADR-003 | PyMuPDF primary | Lightweight, no GPU needed |
| ADR-004 | RQ over Celery | Simpler, same Redis dependency |
| ADR-005 | LLM Manager pattern | Runtime-switchable, testable |
| ADR-006 | JWT bridged from HMS | No separate user registry |
| ADR-007 | Local-first PHI | No patient data to cloud LLMs |

## Change Log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | Created from pyproject.toml + package.json + codebase analysis |
