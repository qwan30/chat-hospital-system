# 🏥 AI-Powered Hospital Knowledge Assistant

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![TanStack Start](https://img.shields.io/badge/TanStack_Start-1.167-FF4154?style=for-the-badge&logo=vite&logoColor=white)](https://tanstack.com/start)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-✓-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-Active-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/qwan30/chat-hospital-system/actions)
[![Tests](https://img.shields.io/badge/Tests-260%2B_Passing-22C55E?style=for-the-badge)](https://github.com/qwan30/chat-hospital-system/actions)
[![AI Eval](https://img.shields.io/badge/AI_Eval-Review_Pending-F59E0B?style=for-the-badge)](app/backend/data/evaluation/rag_sentinel_v2.jsonl)
[![Release Gate](https://img.shields.io/badge/Release_Gate-Conditional-F59E0B?style=for-the-badge)](app/backend/scripts/run_ai_evaluation.py)

**An AI-powered clinical decision support system** integrating RAG (Retrieval-Augmented Generation) with permission-aware vector search, citation hallucination detection, and HMS (Hospital Management System) data synchronization. Built with a **hybrid Clean/Pipeline architecture** — framework-free domain core, abstract provider interfaces, centralized prompt registry, and domain-driven exceptions. Designed to demonstrate production-grade AI engineering with strict PHI (Protected Health Information) compliance considerations.

> **🟠 AI evaluation status: CONDITIONAL**
> The versioned corpus and 300 source-backed cases are available, but the 50-case sentinel is still `draft`. It requires two independent reviewer approvals with no unresolved issues and therefore blocks release. Retrieval, Graph RAG, chat, and controlled-scan OCR are not represented as passing until their real adapters execute and produce run artifacts.
>
> 📚 **[Interactive Documentation Portal →](docs/documentation-portal.html)** | 📂 **[Documentation Index →](docs/README.md)** | 📋 **[API Contract →](docs/05-api/api-contract.md)**

</div>

---

## 🎯 Key Features & Business Value

| # | Clinical Domain | Technical Implementation | Business Impact |
|---|---------------|-------------------------|-----------------|
| 🔍 | **Permission-Aware RAG** | Vector search with SQL JOIN permission filter — only document chunks the user's role can access are included in LLM context | Zero PHI leakage across role boundaries; HIPAA-aligned data access |
| ✅ | **Citation Validation** | Regex-based post-generation verification: validates that LLM citation IDs (e.g. [E1]) exist in retrieved evidence. (Note: factual content cross-checking is unimplemented) | Blocks hallucinated source references before streaming |
| 📄 | **Document OCR & Indexing** | Async RQ pipeline: PDF parsing (PyMuPDF) → conditional OCR fallback (PaddleOCR) → chunking → embedding (Ollama/Gemini) → pgvector index → BM25 tsvector → Graph RAG extraction → CDSS trigger | Converts unstructured hospital documents into searchable knowledge base |
| 🏥 | **HMS Data Sync** | API bridge to Hospital Management System — imports appointments, lab results, medications; caches as RAG-readable context | Real-time patient context without manual data entry |
| 💊 | **Drug-Allergy Pre-Check** | Cross-references prescribed medications against patient allergy list + current medications using RAG context + LLM analysis | Prevents adverse drug events at point of care |
| 🔐 | **RBAC + ABAC Security** | JWT authentication with role-based claims; 7 roles with scoped patient permissions; enforcement at API gateway + RAG retrieval layers | Enforced separation of duties; audit-ready access control |
| 🚨 | **Autonomous CDSS Agent** | Background RQ worker automatically analyses every ingested document using a flat dump of the patient's Knowledge Graph entities/relations as context; feeds LLM a structured risk-analysis prompt; persists `ClinicalAlert` records | Proactive clinical decision support — alerts clinicians to risk factors before they are noticed manually |
| 📊 | **Impact Metrics** | Time-saved and cost-saved tracking per AI-assisted query; helpfulness feedback loop; dashboard analytics | Quantifiable ROI for hospital administration |
| 🔄 | **Streaming SSE** | Server-Sent Events for real-time token streaming; buffered until citation validation passes; client-side progressive rendering | Immediate clinician feedback with safety gate |

---

## 🎯 Engineering Skills Demonstrated

| Dimension | Demonstrated Skills |
|-----------|-------------------|
| **AI/ML Engineering** | RAG pipeline with citation ID validation, permission-aware vector search, multi-provider LLM/embedding abstraction (Ollama/Gemini), source-backed AI evaluation contracts, centralized prompt registry |
| **Backend Engineering** | FastAPI async, SQLAlchemy 2.0+asyncpg, pgvector HNSW, Redis/RQ workers, Alembic migrations, API contract verification, structured JSON logging |
| **Frontend Engineering** | TanStack Start (Vite 8), React 19, shadcn/ui, Tailwind CSS v4, SSE streaming, Playwright E2E, 90+ routes with RBAC-gated navigation |
| **DevOps / SRE** | 5 GitHub Actions workflows (CI/CD/Security/Rollback/Dependabot), Docker multi-stage, Trivy+CodeQL scanning, Grafana+Prometheus+Loki+Tempo observability |
| **Security** | JWT RBAC+ABAC, PHI-aware SQL JOIN filters, citation hallucination detection, TruffleHog+Bandit+pip-audit+npm audit, security headers |
| **Documentation** | 100+ docs across 12 domains, interactive HTML portal with dark mode+search+Mermaid, ADRs, 5 architecture diagrams |

---

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        U[👨‍⚕️ Healthcare Staff<br/><i>Doctors · Nurses · Pharmacists</i>]
        N[🔀 Nginx :80<br/><i>Reverse Proxy</i>]
    end

    subgraph "Application Layer"
        FE[⚛️ TanStack Start Frontend<br/><i>Vite 8 · shadcn/ui · Streaming SSE</i>]
        BE[🐍 FastAPI Backend<br/><i>Python 3.12 · Async · JWT Auth</i>]
        W[⚙️ RQ Worker<br/><i>Document Processing · OCR · Embedding</i>]
        CD[🚨 CDSS Worker<br/><i>Graph Context · LLM Risk Analysis</i>]
    end

    subgraph "Data Layer"
        PG[("🐘 PostgreSQL + pgvector<br/><i>14 Tables · Vector Search · HNSW</i>")]
        RD[("🗄️ Redis 7<br/><i>Job Queue · Cache</i>")]
    end

    subgraph "AI Layer"
        LLM[🧠 LLM Provider<br/><i>Ollama / OpenAI<br/>Citation Validation</i>]
        EMB[📐 Embedding Provider<br/><i>Deterministic / Ollama / Gemini</i>]
    end

    subgraph "External"
        HMS[🏥 HMS API<br/><i>Appointments · Labs · Sync</i>]
    end

    subgraph "Observability"
        PR[📊 Prometheus] --> GF[📈 Grafana]
        LK[📝 Loki · Tempo] --> GF
    end

    U --> N
    N -->|"/api/*"| BE
    N -->|"/"| FE
    FE --> BE
    BE --> PG
    BE --> RD
    BE --> LLM
    BE --> EMB
    BE --> HMS
    W --> PG
    W --> RD
    W --> EMB
    W --> CD
    CD --> PG
    CD --> LLM
    BE -.-> PR
    BE -.-> LK

    style U fill:#1e40af,stroke:#3b82f6,color:#fff
    style N fill:#ea580c,stroke:#fb923c,color:#fff
    style FE fill:#000,stroke:#666,color:#fff
    style BE fill:#059669,stroke:#34d399,color:#fff
    style W fill:#7c3aed,stroke:#a78bfa,color:#fff
    style PG fill:#1e40af,stroke:#60a5fa,color:#fff
    style RD fill:#dc2626,stroke:#f87171,color:#fff
    style LLM fill:#b91c1c,stroke:#ef4444,color:#fff
    style EMB fill:#0891b2,stroke:#22d3ee,color:#fff
    style CD fill:#be185d,stroke:#f472b6,color:#fff
    style HMS fill:#4b5563,stroke:#9ca3af,color:#fff
    style PR fill:#eab308,stroke:#facc15,color:#000
    style GF fill:#eab308,stroke:#facc15,color:#000
    style LK fill:#eab308,stroke:#facc15,color:#000
```

---

## 📸 Application Screenshots

<div align="center">

### 🔐 Login & Authentication

![Login](screen-demo/login-demo.png)

### 🏠 Dashboard & Navigation

| | |
|:---:|:---:|
| **Dashboard** — KPI metrics, recent patients, clinical overview | **Screen Index** — Navigation hub |
| ![Dashboard](screen-demo/dashboard.png) | ![Screen Index](screen-demo/screen-index.png) |

### 👤 Patient Management

| | |
|:---:|:---:|
| **Patient Records** — RBAC-filtered patient roster | **Patient Timeline** — Chronological clinical events |
| ![Patients](screen-demo/patient.png) | ![Timeline](screen-demo/time-line.png) |

### 🤖 AI Chat & Knowledge Graph

| | |
|:---:|:---:|
| **AI Chat** — Evidence-cited clinical Q&A with streaming SSE | **Graph RAG** — Knowledge graph explainability view |
| ![Chat](screen-demo/chat.png) | ![Graph RAG](screen-demo/graph-rag.png) |

| |
|:---:|
| **Graph RAG Detail** — Node relationships, evidence, and citations |
| ![Graph RAG Detail](screen-demo/graph-rag-detail.png) |

### 📋 Audit & Compliance

| | |
|:---:|:---:|
| **Audit Log** — Full event trail with filtering | **Notifications** — Real-time clinical alerts |
| ![Audit](screen-demo/audit-screen-new.png) | ![Notifications](screen-demo/notification.png) |

</div>

---

## 🔐 Permission-First RAG Flow

This sequence diagram shows the two-stage authorization applied before any context reaches the LLM. **Patient-scope permissions are enforced in the SQL `WHERE` clause**, so chunks the user has no grant for never leave the database. A second **role-scope filter runs in Python after retrieval** (`_apply_role_filters`) — note it executes *after* `LIMIT :top_k`, so a filtered result set can be smaller than the requested `top_k`:

```mermaid
sequenceDiagram
    actor D as 👨‍⚕️ Doctor
    participant A as Auth (JWT)
    participant R as Role Check
    participant G as Guardrails & Chit-Chat
    participant V as Vector Search<br/>+ Permission Filter
    participant C as Context Builder
    participant L as LLM
    participant CV as Citation Validator
    participant S as Stream Buffer

    D->>A: Ask clinical question
    A->>A: Validate JWT token
    A->>R: Extract role + patient context
    R->>R: Check RBAC permissions
    R->>G: Input Guardrail & Chit-Chat Check
    alt Is Chit-Chat or Injection
        G-->>S: Short-circuit response
        S-->>D: Return safe/canned response
    else Valid Clinical Question
        G->>V: Query with patient-scope filter (SQL JOIN)

        Note over V: WHERE EXISTS (active permission grant)<br/>AND patient_id = :patient_id<br/>expiry- and soft-delete-aware

        V-->>R: Patient-authorized chunks
        R->>R: Apply role scope filter (Python, post-query)
        R-->>C: Return permitted chunks only

        Note over C: Assemble safe context<br/>from verified sources

        C->>L: Prompt + filtered context
        L-->>G: Output Guardrail Check (PHI)
        G-->>CV: Generated answer + citations

        alt Citations valid & matched
            CV-->>S: ✅ Answer verified
            S-->>D: Stream response with sources
        else Hallucinated or unauthorized
            CV-->>S: ❌ Citation mismatch
            S-->>D: "Unable to answer — insufficient evidence"
        end
    end
```

---

## 🔄 CI/CD Pipeline

> **Note on the `main` build status.** Pull requests run the evaluation `smoke` suite and
> pass. Pushes to `main` and the nightly schedule run the **`release`** suite, which enforces
> `sentinel_independent_review` — *50 sentinel cases approved by two independent reviewers
> with no unresolved issues*. That human review is still outstanding, so the
> `rag-evaluation` job fails **by design** rather than passing by skip. Every other job
> (CodeQL ×2, backend tests, migrations, frontend, observability, Docker) is green.
> This is a deliberate quality gate, not a broken pipeline — see
> [`evaluation/runner.py`](app/backend/src/hospital_ai/evaluation/runner.py) and
> [`rag_sentinel_v2.jsonl`](app/backend/data/evaluation/rag_sentinel_v2.jsonl).

```mermaid
graph LR
    subgraph "Trigger"
        P[Push / PR to main]
    end

    subgraph "Security Gates"
        CQ[CodeQL<br/>Python + JS/TS]
        TS[TruffleHog<br/>Secret Scan]
    end

    subgraph "Quality Gates"
        RL[Ruff Lint<br/>+ Format]
        PY[Pytest<br/>250+ tests]
        AC[API Contract<br/>Verification]
        ES[ESLint<br/>+ TypeScript]
        VT[Vitest<br/>Unit Tests]
        PW[Playwright<br/>E2E Tests]
        MG[Alembic<br/>Migration Check]
    end

    subgraph "Build & Scan"
        DB[Docker Build<br/>Multi-stage]
        TV[Trivy Scan<br/>CRITICAL+HIGH]
        GH[Push to GHCR]
    end

    subgraph "Deploy"
        STG[Staging<br/>Auto-deploy]
        SMK[Smoke Test<br/>Health Check]
        PRD[Production<br/>Manual Promote]
        SLK[Slack<br/>Notification]
    end

    P --> CQ
    P --> RL --> PY --> AC
    P --> ES --> VT --> PW
    PY --> MG
    CQ --> DB
    PW --> DB
    MG --> DB
    DB --> TV --> GH
    GH --> STG --> SMK --> PRD --> SLK
```

---

## 🗄️ Database Entity Relationship

```mermaid
erDiagram
    users ||--o{ chat_threads : creates
    users ||--o{ audit_events : triggers
    users ||--o{ access_requests : submits
    chat_threads ||--o{ chat_messages : contains
    documents ||--o{ document_chunks : splits_into
    document_chunks ||--o{ embeddings_cache : stores
    patients ||--o{ access_requests : scoped_to
    patients ||--o{ clinical_alerts : receives
    documents ||--o{ clinical_alerts : triggers
    chat_messages ||--o{ feedback : receives
    chat_messages ||--o{ citations : references
    patients ||--o{ graph_entities : has
    graph_entities ||--o{ graph_relations : participates_in

    users {
        uuid id PK
        string email
        string role "doctor|nurse|pharmacist|admin"
        string hashed_password
    }
    chat_threads {
        uuid id PK
        uuid user_id FK
        uuid patient_id FK
        string title
    }
    chat_messages {
        uuid id PK
        uuid thread_id FK
        text question
        text answer
        jsonb citations
    }
    documents {
        uuid id PK
        string filename
        string status "pending|processing|ready|failed"
        jsonb metadata
    }
    document_chunks {
        uuid id PK
        uuid document_id FK
        text content
        vector embedding
        jsonb permissions
    }
    audit_events {
        uuid id PK
        uuid user_id FK
        string action
        jsonb details
    }
    clinical_alerts {
        uuid id PK
        uuid patient_id FK
        uuid source_document_id FK "nullable"
        string severity "low|medium|high"
        string title
        text description
        boolean is_acknowledged "default: false"
        timestamp created_at
    }
    graph_entities {
        uuid id PK
        uuid patient_id FK
        string entity_type
        string name
        jsonb metadata
    }
    graph_relations {
        uuid id PK
        uuid source_entity_id FK
        uuid target_entity_id FK
        string relationship_type
        jsonb evidence_references
    }
```

---

## 🚢 Deployment Architecture

```mermaid
graph TB
    subgraph "VPS / Cloud Instance"
        NG[🔀 Nginx :80<br/><i>Reverse Proxy</i>]
        FE[⚛️ Frontend<br/><i>TanStack Start :3000</i>]
        BE[🐍 Backend<br/><i>FastAPI :8000</i>]
        W[⚙️ Worker<br/><i>RQ :queue</i>]
        PG[("🐘 PostgreSQL<br/><i>pgvector :5432</i>")]
        RD[("🗄️ Redis<br/><i>:6379</i>")]
    end

    subgraph "Observability Stack"
        GF[📈 Grafana<br/><i>:3001</i>]
        PR[📊 Prometheus<br/><i>:9090</i>]
        LK[📝 Loki<br/><i>:3100</i>]
        TP[🔍 Tempo<br/><i>:3200</i>]
    end

    subgraph "External Services"
        GHCR[📦 GitHub Container Registry]
        LLM[🧠 LLM Provider<br/><i>Ollama / OpenAI</i>]
        HMS[🏥 HMS<br/><i>Hospital System</i>]
    end

    NG -->|"/"| FE
    NG -->|"/api/*"| BE
    FE -->|"REST + SSE"| BE
    BE --> PG
    BE --> RD
    W --> PG
    W --> RD
    BE --> LLM
    BE --> HMS
    BE -.->|"metrics"| PR
    BE -.->|"logs/traces"| LK
    BE -.->|"traces"| TP
    PR --> GF
    LK --> GF
    TP --> GF
    GHCR -.->|"pull image"| BE

    style NG fill:#ea580c,stroke:#fb923c,color:#fff
    style FE fill:#000,stroke:#666,color:#fff
    style BE fill:#059669,stroke:#34d399,color:#fff
    style W fill:#7c3aed,stroke:#a78bfa,color:#fff
    style PG fill:#1e40af,stroke:#60a5fa,color:#fff
    style RD fill:#dc2626,stroke:#f87171,color:#fff
    style GF fill:#eab308,stroke:#facc15,color:#000
    style PR fill:#eab308,stroke:#facc15,color:#000
    style LK fill:#eab308,stroke:#facc15,color:#000
    style TP fill:#eab308,stroke:#facc15,color:#000
    style GHCR fill:#4b5563,stroke:#9ca3af,color:#fff
    style LLM fill:#b91c1c,stroke:#ef4444,color:#fff
    style HMS fill:#4b5563,stroke:#9ca3af,color:#fff
```

---

## 📊 Verified Project Metrics

```mermaid
xychart-beta
    title "Source-Backed Evaluation Inputs"
    x-axis ["PDF Docs", "Lab CSV", "Benchmark Cases", "Sentinel Cases"]
    y-axis "Count" 0 --> 300
    bar [100, 100, 300, 50]
```

| Metric | Value | Status |
|--------|-------|--------|
| **Canonical patient corpus** | 100 PDF documents + 100 lab CSV files | ✅ Versioned manifest: `synthetic-100-v2` |
| **Source-backed AI benchmark** | 300 cases; 50-case sentinel | 🟠 Corpus smoke validates all 50 contracts; independent review still blocks release |
| **Evaluation evidence** | `run.json`, `cases.jsonl`, `junit.xml`, `summary.md` | ✅ Produced by each evaluation-runner invocation |
| **REST API surface** | 62 OpenAPI paths/routes | ℹ️ Repository inventory; not a production-traffic claim |
| **Database schema** | 18 tables, 16 Alembic migrations | ℹ️ Repository inventory; migration execution is environment-specific |
| **Frontend components** | 84 React components (32 domain, 6 shell, 46 shadcn/ui) | ℹ️ Repository inventory |
| **Backend test suite** | 550 Pytest tests | ✅ Verified locally; see CI for the current run |
| **E2E test suites** | 13 Playwright specs (auth, RBAC, business flow, CDSS, chat, graph, accessibility) | 🔴 Written but **not executed in CI** — the job needs a backend service container (gh#123) |
| **CI/CD workflows** | 5 pipelines (CI, CD, Security, Rollback, Dependabot) | ℹ️ Workflow inventory; check the current GitHub run for status |
| **Backend coverage** | 73.3% statements (6,117 / 8,059), branch coverage on | ✅ CI gate at `--cov-fail-under=60`. Gaps are concentrated in LLM/embedding providers and document loaders (0%) — they need live services to exercise meaningfully |
| **Code quality** | Ruff + ESLint + TypeScript strict | ✅ Focused evaluation checks are recorded; no blanket “zero errors” claim |

---

## 🧠 Architectural Decision: Why Hybrid Clean/Pipeline Architecture?

> **"Why not full DDD layers like `hospital-management-system`?"**

The `hospital-management-system` is a **complex ERP CRUD** application with deep domain logic, multi-role workflows, inventory, billing, and clinical operations. Full DDD layers (domain/application/infrastructure/presentation) add **necessary structure** to manage that complexity.

This project (`chatbot-hospital-system`) is a **RAG data pipeline** — the core flow is:

```
Ingest Document → Chunk → Embed → Store Vector → Query → Retrieve → Generate → Validate → Stream
```

This maps naturally to a **pipeline architecture** where each stage is a self-contained service. Adding DDD directory layers would introduce **indirection without benefit** — the data flow IS the domain.

**However**, we still achieve the **same architectural goals** as DDD:

```mermaid
graph TB
    subgraph api["🔴 api/ — Presentation Layer"]
        direction LR
        A1[14 Route Modules]
        A2[Middleware]
        A3[Exception Handlers]
    end

    subgraph svc["🔵 services/ — Application Layer"]
        direction LR
        S1[RAG Pipeline]
        S2[Chat Orchestration]
        S3[Document OCR]
        S4[HMS Sync]
    end

    subgraph core["🟢 core/ — Domain Layer (ZERO framework deps)"]
        direction LR
        C1["Exceptions<br/>13 domain errors"]
        C2["Interfaces<br/>7 ABC/Protocol"]
        C3["Prompts<br/>4 modules"]
        C4["Config<br/>JWT · Rate Limit"]
    end

    subgraph db["⚫ db/ — Infrastructure Layer"]
        direction LR
        D1[SQLAlchemy Models]
        D2[Alembic Migrations]
        D3[pgvector]
    end

    api --> svc --> core --> db

    style api fill:#b91c1c,stroke:#ef4444,color:#fff,stroke-width:2px
    style svc fill:#1d4ed8,stroke:#60a5fa,color:#fff,stroke-width:2px
    style core fill:#059669,stroke:#34d399,color:#fff,stroke-width:2px
    style db fill:#4b5563,stroke:#9ca3af,color:#fff,stroke-width:2px
```

> ⬆️ **Dependency Flow: db ← core ← services ← api** (inner layers never depend on outer layers)

| DDD Principle | How We Achieve It |
|---------------|-------------------|
| **Dependency Inversion** | `core/` has ZERO FastAPI imports. Business logic depends on abstract protocols (`ILLMProvider`, `IEmbeddingProvider`), not frameworks |
| **Domain Isolation** | Domain exceptions (`MedicalDataAccessException`, `CitationHallucinationException`) live in `core/`. The API layer maps them to HTTP codes |
| **Separation of Concerns** | `api/` handles HTTP, `services/` handles orchestration, `core/` handles pure business rules, `db/` handles persistence |
| **Testability** | Every component testable in isolation. Core logic tested without database or HTTP |

This is the **Clean Architecture dependency rule** implemented through convention, not directory structure. An interviewer who reads the `core/` directory will immediately recognize the discipline.

---

## 📂 Project Structure

```
.
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # 8-job CI pipeline (CodeQL, test, build, scan)
│   │   ├── cd.yml              # Multi-env CD (staging → production)
│   │   ├── security-scan.yml   # Weekly: pip-audit, npm audit, TruffleHog, Trivy
│   │   └── rollback.yml        # Manual rollback with confirmation gate
│   └── dependabot.yml          # Automated dependency updates (npm, pip, GHA)
├── infra/
│   ├── docker-compose.yml           # Production stack (5 services)
│   ├── docker-compose.observability.yml  # Grafana, Prometheus, Loki, Tempo
│   ├── nginx/default.conf           # Reverse proxy with SSE streaming
│   └── observability/              # Prometheus, Tempo, Loki, Grafana configs
├── app/
│   ├── backend/
│   │   ├── src/hospital_ai/
│   │   │   ├── api/            # FastAPI routes, middleware, exception handlers
│   │   │   ├── core/           # Framework-free business logic (ZERO FastAPI deps)
│   │   │   ├── db/             # SQLAlchemy models, sessions, migrations
│   │   │   ├── schemas/        # Pydantic request/response models
│   │   │   ├── services/       # RAG pipeline, LLM, embedding, HMS integration
│   │   │   └── workers/        # RQ job handlers: OCR, Graph indexing, CDSS agent
│   │   ├── alembic/            # Database migration history
│   │   └── tests/              # 260+ Pytest tests (incl. CDSS agent tests)
│   └── frontend/
│       ├── src/
│       │   ├── routes/         # TanStack Router pages (90+ routes)
│       │   ├── components/     # 100+ React components (shadcn/ui)
│       │   ├── hooks/          # Custom React hooks
│       │   └── lib/            # API client, auth, session, utilities
│       └── e2e/                # Playwright E2E tests
└── docs/
    ├── documentation-portal.html   # Interactive HTML documentation portal
    ├── 00-overview/                # Project foundation & governance
    ├── 01-business/                # BRD, BRs, stakeholders, glossary
    ├── 04-architecture/            # ADRs, tech stack, security architecture
    ├── 05-api/                     # API contract & error codes
    ├── 06-database/                # ERD, schema, data dictionary
    └── ... (12 documentation domains, 100+ files)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ · Node.js 22+ · Docker & Docker Compose

### 1. Start Infrastructure
```bash
docker compose up -d postgres redis
```

### 2. Backend (FastAPI)
```bash
cd app/backend
python -m venv venv && source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -e ".[dev,postgres]"
alembic upgrade head
uvicorn "hospital_ai.main:create_app" --factory --host 0.0.0.0 --port 8000 --reload
```
Swagger UI: http://localhost:8000/docs

### 3. Frontend (TanStack Start)
```bash
cd app/frontend
bun install
bun run dev
```
UI: http://localhost:3000 (Vite dev server; the Docker image serves on **8082**)

### 4. Full Local Docker Stack
```bash
export BACKEND_IMAGE=hospital-ai-backend:local
docker compose -f infra/docker-compose.yml -f infra/docker-compose.local-build.yml up -d
# Optional local observability:
docker compose -f infra/docker-compose.yml -f infra/docker-compose.local-build.yml -f infra/docker-compose.observability.yml up -d
```

Staging uses the GitHub-built immutable GHCR image through Dokploy. Set
`BACKEND_IMAGE` to the approved `sha-<7-hex>` tag or digest in Dokploy; do not
build the backend from a VPS source clone.

### Demo Accounts

Synthetic local-only accounts seeded by `scripts/seed_dev.py`. **All roles share the
password `demo`** — `/auth/token` is a portfolio stub that checks for that literal and
returns a static dev token; there is no password hashing or credential store. These
accounts exist only against synthetic data and are refused outside `HOSPITAL_AI_ENVIRONMENT=local`
(audit finding F-SEC-001).

| Role | Email | Password | Static token |
|------|-------|----------|--------------|
| 👨‍⚕️ Doctor | `doctor@example.test` | `demo` | `dev-doctor` |
| 👩‍⚕️ Nurse | `nurse@example.test` | `demo` | `dev-nurse` |
| 💊 Pharmacist | `pharmacist@example.test` | `demo` | `dev-pharmacist` |
| 📁 Records | `records@example.test` | `demo` | `dev-records` |
| 🔒 Security | `security@example.test` | `demo` | `dev-security` |
| ⚙️ Admin | `admin@example.test` | `demo` | `dev-admin` |

### Before a live demo

The prompt-injection and PHI-redaction scanners are ONNX models that run on CPU. Measured on
a dev laptop: **~7.8s** for the first input scan and **~4.4s** for the first output scan,
settling to **~4s per chat turn** once warm. The app warms the models on startup
(`warm_up_guardrails`), but the very first chat still pays model-load cost.

Measured end-to-end chat latency: **22.5s cold → 5.7s → 4.0s warm**.

So: **start the backend and send one throwaway question before presenting.** Watch for
`Guardrail scanners warmed up` in the log, then verify with:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Authorization: Bearer dev-doctor" -H "Content-Type: application/json" \
  -d '{"question":"List the current medications","patient_id":"20000000-0000-0000-0000-000000000001","top_k":3}'
```

A healthy response has `"pipeline":"simple_qa"` and a non-empty `citations` array. If you
see `"pipeline":"blocked"` with *"security policy violation"*, the guardrail scan exceeded
`HOSPITAL_AI_GUARDRAIL_TIMEOUT_SECONDS` (default 15s) and failed closed — raise it rather
than disabling guardrails. Setting `HOSPITAL_AI_DISABLE_GUARDRAILS=true` removes the delay
but also removes the prompt-injection defence that is worth demonstrating.

Note `HOSPITAL_AI_CHAT_PROVIDER=stub` in `.env` returns canned answers. Point it at
`ollama` or `openai` if you want the LLM path live.

---

## 🧪 Testing & Quality

```bash
# Backend — 549 Pytest tests (546 pass, 3 skipped)
cd app/backend && python -m pytest tests/ -v --tb=short

# Backend — deterministic source-backed PR sentinel contract (not product scoring)
cd app/backend && python scripts/run_ai_evaluation.py --suite smoke --lane deterministic --components corpus --output-dir evaluation-artifacts/deterministic

# Backend — full 300-case deterministic evaluation
cd app/backend && python scripts/run_ai_evaluation.py --suite release --lane deterministic --components corpus,ocr,retrieval,graph,chat --output-dir evaluation-artifacts/release

# Note: retrieval, Graph RAG, chat, and controlled-scan OCR require real adapters.
# If an adapter is unavailable, the requested component is a hard failing gate; it is never a pass by skip.

# Backend — API contract verification
cd app/backend && python scripts/verify_contracts.py

# Frontend — Unit tests (Vitest)
cd app/frontend && bun run test

# Frontend — E2E tests (Playwright)
cd app/frontend && bun run test:e2e

# CDSS-specific E2E test
cd app/frontend && bun run test:e2e e2e/cdss-flow.spec.ts
```

---

## 📈 CI/CD & Observability

| Pipeline | Trigger | Actions |
|----------|---------|---------|
| **CI** (`ci.yml`) | Push / PR | CodeQL · Ruff · Pytest · ESLint · Playwright · Docker build+Trivy → GHCR |
| **CD** (`cd.yml`) | CI success / Manual | SCP configs · SSH deploy · Alembic migrate · Smoke checks · Slack notify |
| **Rollback** (`rollback.yml`) | Manual | Confirmation gate · Specific tag deploy · Health check |
| **Security** (`security-scan.yml`) | Weekly / Manual | pip-audit · npm audit · Bandit · TruffleHog · Trivy container scan |
| **Dependabot** (`dependabot.yml`) | Weekly | Automated PRs for npm, pip, GitHub Actions |

**Observability Stack:** `Nginx → Backend → Prometheus → Grafana + Loki → Tempo`

Configurations in [`infra/observability/`](infra/observability/) — Prometheus metrics, Grafana dashboards, Loki log aggregation, Tempo distributed tracing.

---

## 📚 Documentation

| Section | Content | Primary Doc |
|---------|---------|-------------|
| **00-overview** | Project foundation, conventions, governance | [`project-foundation.md`](docs/00-overview/project-foundation.md) |
| **01-business** | Business rules, BR-001–BR-007 + BR-CDSS-001, glossary, scope | [`business-rules.md`](docs/01-business/business-rules.md) |
| **02-product** | PRD, personas, MVP criteria | [`prd.md`](docs/02-product/prd.md) |
| **03-requirements** | SRS (25 FRs + 22 NFRs), use cases UC-001–UC-009, permissions | [`srs.md`](docs/03-requirements/srs.md) |
| **04-architecture** | System design, security architecture, ADR-001–ADR-012, coding standards | [`architecture.md`](docs/04-architecture/architecture.md) |
| **05-api** | API contract, endpoint specs, error codes | [`api-contract.md`](docs/05-api/api-contract.md) |
| **06-database** | Schema (14 tables), ERD, data dictionary, migrations | [`db-schema.md`](docs/06-database/db-schema.md) |
| **07-flows** | Business flows, state machines, user journeys | [`end-to-end-business-flow.md`](docs/07-flows/end-to-end-business-flow.md) |
| **08-ui-ux** | Design system, Figma specs, UI/API traceability | [`00_product_ui_truth.md`](docs/08-ui-ux/00_product_ui_truth.md) |
| **09-testing** | Test strategy, plan, RTM, 250+ test cases | [`test-plan.md`](docs/09-testing/test-plan.md) |
| **10-deployment** | CI/CD (5 workflows), env variables, Docker, rollback | [`deployment-guide.md`](docs/10-deployment/deployment-guide.md) |
| **11-operations** | Monitoring (Grafana), incident response, troubleshooting | [`monitoring-guide.md`](docs/11-operations/monitoring-guide.md) |
| **12-handover** | Developer onboarding, repository guide, known issues | [`developer-onboarding.md`](docs/12-handover/developer-onboarding.md) |

> 📄 **[Interactive Documentation Portal →](docs/documentation-portal.html)** | 📂 **[Full Documentation Index →](docs/README.md)**

---

## 🛡️ Security & Compliance

- **PHI Protection**: Permission filters applied at SQL JOIN level before LLM context assembly — zero PHI leakage to unauthorized roles
- **Citation Validation**: Every LLM response verified against source database before streaming to client — hallucination detection blocks fabricated references
- **Authentication**: JWT bearer validation with pinned algorithm, issuer/audience checks, and expiry enforcement (`services/jwt_auth.py`). ⚠️ The demo login endpoint is a **portfolio stub** — it accepts the literal password `demo` and returns a static token; password hashing, refresh rotation, and httpOnly cookies are documented as future work, not implemented
- **Authorization**: RBAC with ABAC overlay — 7 roles with scoped patient permissions enforced at API gateway + RAG retrieval layers
- **Rate Limiting**: Per-endpoint limits via slowapi, enabled by default and fail-closed — login `10/min`, chat `10/min`, streaming `5/min`, search `20/min`, access requests `3/min`, global default `60/min`. Disabled only when `TESTING=true` is set explicitly (test suite and local dev)
- **Audit Trail**: Patient reads, permission denials, chat queries, document access, and config changes are logged with actor ID, trace ID, and timestamp via `PermissionService.require_read` / `AuditService`. User-authored text is passed through `sanitize_audit_query` so raw clinical free text does not enter audit metadata
- **Container Scanning**: Trivy scans on every CI push (CRITICAL+HIGH severity) + weekly scheduled full scan (CRITICAL,HIGH,MEDIUM)
- **Secret Detection**: TruffleHog weekly scan across full git history + Bandit SAST for Python source code
- **Dependency Monitoring**: Dependabot (npm, pip, GitHub Actions) + pip-audit + npm audit for continuous vulnerability tracking
- **Transport Security**: Nginx reverse proxy with security headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy)

---

## 🧠 Knowledge Graph Explainability

The Knowledge Graph (previously "Graph RAG") is a backend-backed explainability feature that shows how clinical reasoning connects patient data, diagnoses, medications, labs, and evidence documents.

```mermaid
graph LR
    P[👤 Patient] -->|diagnosed with| D[🩺 Diagnosis]
    D -->|treated with| M[💊 Medication]
    P -->|allergic to| A[⚠️ Allergy]
    P -->|lab result| L[🧪 Lab]
    M -->|documented in| DOC[📄 Document]
    M -->|contraindicates| A
    L -->|evidence for| M
    DOC -->|supports| D

    style P fill:#1e40af,stroke:#3b82f6,color:#fff
    style D fill:#059669,stroke:#34d399,color:#fff
    style M fill:#7c3aed,stroke:#a78bfa,color:#fff
    style A fill:#dc2626,stroke:#f87171,color:#fff
    style L fill:#0891b2,stroke:#22d3ee,color:#fff
    style DOC fill:#4b5563,stroke:#9ca3af,color:#fff
```

**Key capabilities:**
- **Backend-backed graph data** — nodes/edges come from the database, not hardcoded frontend data
- **Multi-patient support** — graph works for any accessible seeded patient, not only Eleanor Vance
- **Interactive controls** — zoom, fullscreen, filter by node type, highlight reasoning paths
- *(Planned)* **Node detail side panel** — click any node to see clinical summary, related evidence, and source citations
- *(Planned)* **Edge evidence** — click any relationship to see why two nodes are connected and the source document/page
- *(Planned)* **Export** — PNG screenshot and JSON data export; PDF report export

---

## ⚠️ Known Limitations

This project is a **portfolio demonstration**, not a certified medical device. The following limitations are clearly acknowledged:

| Area | Current Status | Future Plan |
|------|---------------|-------------|
| **Citation Validation** | Uses regex to verify citation IDs (`[E1]`) exist in context. Factual content cross-checking is currently dead code. | Implement full semantic verification of generated claims against source evidence |
| **Streaming Endpoint** | The `chat_stream.py` endpoint forces `simple_qa` and ignores advanced reasoning pipelines (`decompose`, `patient_summary`) and HyDE | Enable full reasoning pipeline support for streaming responses |
| **Document Loaders** | Advanced file loaders (`docx`, `xlsx`, `html`) are implemented but bypassed by the worker which only calls PyMuPDF | Wire up the `services/loaders/` suite into the `jobs.py` ingestion worker |
| **OCR Pipeline** | PaddleOCR is an optional fallback for blank/image PDFs. Cohere and OpenAI are not wired to the embedding pipeline | Make OCR a standard deterministic step; fix provider integrations |
| **Login / Credentials** | `/auth/token` is a stub: accepts the literal password `demo` and returns a static, non-expiring token. JWT *validation* is real; JWT *issuance* is not | Password hashing (argon2), real token minting, refresh rotation, revocation |
| **Token Storage** | Bearer token is kept in-memory to prevent XSS, but session rehydration re-derives a dev token | Implement an httpOnly refresh cookie for secure, persistent sessions |
| **CDSS Alert Grounding** | Clinical alerts are written from raw LLM JSON with no citation or confidence gate | Apply the same evidence-grounding contract to the CDSS worker |
| **E2E in CI** | 13 Playwright specs exist but do not run in CI — the job needs a backend service container (gh#123) | Add a backend service to the frontend CI job and make E2E blocking |
| **PHI Redaction** | Not implemented — UI honestly states "PHI redaction is planned for production hardening" | Implement NER-based PHI detection before embedding pipeline |
| **Break-Glass Emergency Access** | Disabled by default (`ENABLE_BREAK_GLASS=false`) — treated as planned/future | Implement with justification, expiry, audit trail, and mandatory review |
| **Session-Only Attachments** | All uploaded files go to the knowledge base — session-only temp files are planned | Add ephemeral document scope that expires with the chat thread |
| **PDF Graph Export** | PNG and JSON export available — PDF clinical report export is planned | Generate formatted PDF reports from graph data |
| **Multi-Role Users** | One role per account — multi-role mapping documented as future work | Many-to-many user-role table with role-switching workflow |
| **LLM Provider** | Requires Ollama or OpenAI API key — no built-in LLM bundled | Support additional providers (Anthropic, Azure OpenAI, local models) |
| **Data Source** | Uses synthetic/de-identified seed data only | Production deployment requires real HMS integration |

---

## 🔮 Future Improvements

- **PHI Redaction Pipeline** — NER-based detection (Presidio/spaCy) with dual-storage: redacted text for embeddings, originals for authorized citation viewing
- **Break-Glass Emergency Access** — Justification-required emergency override with automatic expiry, audit logging, and mandatory compliance review
- **Session-Only Chat Attachments** — Temporary file scope that doesn't persist to the hospital knowledge base
- **PDF Graph Reports** — Formatted clinical reasoning reports generated from Knowledge Graph data
- **Multi-Role Users** — Role-switching workflow with many-to-many user-role mapping
- **Live AI Evaluation Adapters** — Execute retrieval, Graph RAG, chat, and controlled-scan OCR against the source-backed benchmark and publish comparable regression artifacts
- **Real-Time HMS Integration** — WebSocket-based live sync with Hospital Management System for appointment updates, lab results, and medication orders
- **Mobile-Responsive UI** — Optimized touch-friendly layout for tablet/mobile clinical use

---

<div align="center">

**Built with ❤️ following Clean Architecture principles, AI safety engineering practices, and healthcare industry compliance standards.**

*This project uses synthetic/de-identified data. It demonstrates engineering capability for portfolio purposes — not a certified medical device.*

</div>
