# 🏥 AI-Powered Hospital Knowledge Assistant

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-✓-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![CI](https://img.shields.io/badge/CI-Passing-10b981?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/qwan30/chat-hospital-system/actions)

**A Permission-Aware RAG System for Clinical Decision Support**

[📖 Documentation Portal](docs/documentation-portal.html) · [🏗️ Architecture ADRs](docs/04-architecture/adr/) · [🔒 Security](docs/04-architecture/security-architecture.md) · [🚀 Deployment](docs/10-deployment/deployment-guide.md)

</div>

---

## 🎯 What This Project Demonstrates

This is a **production-grade AI application** built to showcase full-stack engineering skills across multiple dimensions:

| Dimension | Demonstrated Skills |
|-----------|-------------------|
| **AI/ML Engineering** | RAG pipeline with citation validation, permission-aware vector search, multi-provider LLM/embedding abstraction, synthetic RAG evaluation suite |
| **Backend Engineering** | FastAPI with async SQLAlchemy, pgvector, Redis/RQ workers, Alembic migrations, API contract verification, structured logging |
| **Frontend Engineering** | Next.js 16 App Router, React 19, shadcn/ui, Tailwind CSS v4, streaming SSE, Playwright E2E, Vitest |
| **DevOps / SRE** | Multi-environment CI/CD (GitHub Actions), Docker multi-stage builds, Trivy container scanning, CodeQL SAST, full Grafana observability stack (Prometheus, Loki, Tempo), Dependabot, automated rollback |
| **Security** | JWT RBAC, PHI-aware permission filtering, citation hallucination detection, TruffleHog secret scanning, npm audit + pip-audit + Bandit SAST, security headers |
| **Documentation** | 100+ doc files across 12 domains, interactive HTML portal, ADRs with trade-off rationale, Mermaid/PlantUML diagrams |

---

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        U[👨‍⚕️ Healthcare Staff]
        N[Nginx :80]
    end

    subgraph "Application Layer"
        FE[Next.js Frontend<br/>React 19 · Tailwind v4<br/>shadcn/ui · Streaming SSE]
        BE[FastAPI Backend<br/>Python 3.12 · Async<br/>JWT Auth · Rate Limiting]
        W[RQ Worker<br/>Document Processing<br/>OCR · Chunking · Embedding]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL + pgvector<br/>Vector Search<br/>13 Tables · 6 Migrations)]
        RD[(Redis 7<br/>Job Queue<br/>Cache)]
    end

    subgraph "AI Layer"
        LLM[LLM Provider<br/>Ollama / OpenAI<br/>Citation Validation]
        EMB[Embedding Provider<br/>Deterministic / Ollama<br/>OpenAI · Cohere]
    end

    subgraph "External Systems"
        HMS[Hospital Management<br/>System API<br/>Appointments · Labs]
    end

    subgraph "Observability"
        PR[Prometheus<br/>Metrics]
        GF[Grafana<br/>Dashboards]
        LK[Loki · Tempo<br/>Logs · Traces]
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
    BE --> PR
    PR --> GF
    LK --> GF
```

---

## 🔐 Permission-First RAG Flow

This sequence diagram shows how the system ensures **zero PHI leakage** by filtering document access at the database query level before any context reaches the LLM:

```mermaid
sequenceDiagram
    actor D as 👨‍⚕️ Doctor
    participant A as Auth (JWT)
    participant R as Role Check
    participant V as Vector Search<br/>+ Permission Filter
    participant C as Context Builder
    participant L as LLM
    participant CV as Citation Validator
    participant S as Stream Buffer

    D->>A: Ask clinical question
    A->>A: Validate JWT token
    A->>R: Extract role + patient context
    R->>R: Check RBAC permissions
    R->>V: Query with role filter (SQL JOIN)

    Note over V: WHERE role_can_access = true<br/>AND patient_in_scope = true

    V-->>C: Return permitted chunks only

    Note over C: Assemble safe context<br/>from verified sources

    C->>L: Prompt + filtered context
    L-->>CV: Generated answer + citations

    alt Citations valid & matched
        CV-->>S: ✅ Answer verified
        S-->>D: Stream response with sources
    else Hallucinated or unauthorized
        CV-->>S: ❌ Citation mismatch
        S-->>D: "Unable to answer — insufficient evidence"
    end
```

---

## 🔄 CI/CD Pipeline

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
    chat_messages ||--o{ feedback : receives
    chat_messages ||--o{ citations : references

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
```

---

## 🚢 Deployment Architecture

```plantuml
@startuml
!define RECTANGLE class

skinparam componentStyle rectangle
skinparam backgroundColor #FEFEFE
skinparam defaultFontSize 12

title Hospital AI — Production Deployment

node "VPS / Cloud Instance" {
    component "Nginx :80" as nginx
    component "Frontend\nNext.js :3000" as frontend
    component "Backend\nFastAPI :8000" as backend
    component "Worker\nRQ :queue" as worker
    database "PostgreSQL\npgvector :5432" as postgres
    database "Redis\n:6379" as redis
}

node "Observability" {
    component "Grafana\n:3001" as grafana
    component "Prometheus\n:9090" as prometheus
    component "Loki\n:3100" as loki
    component "Tempo\n:3200" as tempo
}

cloud "GitHub Container Registry" as ghcr
cloud "LLM Provider\n(Ollama / OpenAI)" as llm
cloud "HMS\n(Hospital System)" as hms

nginx --> frontend : "/"
nginx --> backend : "/api/*"
frontend --> backend : "REST + SSE"
backend --> postgres
backend --> redis
worker --> postgres
worker --> redis
backend --> llm
backend --> hms
backend --> prometheus : "metrics"
prometheus --> grafana
loki --> grafana
tempo --> grafana
ghcr --> backend : "pull image"
@enduml
```

---

## 📊 Project Metrics

| Metric | Value | Context |
|--------|-------|---------|
| **Backend Tests** | 250+ Pytest | Unit + integration, 2 skipped (known issues) |
| **RAG Eval Score** | 6/6 scenarios passed | Cited answer, no-evidence refusal, denied patient, HMS appointment, general knowledge, graph relation |
| **API Surface** | 35+ route decorators | 28 OpenAPI-documented endpoints |
| **Database Tables** | 13 models | pgvector vector store, 6 Alembic migrations |
| **Frontend Components** | 60+ | shadcn/ui, custom clinical components |
| **E2E Tests** | Playwright (Chromium) | Critical user flows covered |
| **CI Jobs** | 8 parallel | CodeQL, lint, test, migration, build, scan, deploy |
| **Code Quality** | Ruff + ESLint + TypeScript strict | Zero linting errors |

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
│   │   │   └── services/       # RAG pipeline, LLM, embedding, HMS integration
│   │   ├── alembic/            # Database migration history
│   │   └── tests/              # 250+ Pytest tests
│   └── frontend/
│       ├── src/
│       │   ├── app/            # Next.js App Router pages
│       │   ├── components/     # 60+ React components (shadcn/ui)
│       │   ├── hooks/          # Custom React hooks
│       │   └── lib/            # API client, streaming, utilities
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

### 3. Frontend (Next.js)
```bash
cd app/frontend
npm install
npm run dev
```
UI: http://localhost:3000

### 4. Full Production Stack
```bash
docker compose -f infra/docker-compose.yml up -d
# With observability:
docker compose -f infra/docker-compose.yml -f infra/docker-compose.observability.yml up -d
```

---

## 🔗 Quick Links

| Resource | Description |
|----------|-------------|
| [📖 Documentation Portal](docs/documentation-portal.html) | Interactive HTML portal with all 100+ docs, diagrams, and search |
| [🏗️ Architecture ADRs](docs/04-architecture/adr/) | 12 Architecture Decision Records with trade-off analysis |
| [🔒 Security Architecture](docs/04-architecture/security-architecture.md) | PHI protection, RBAC, audit trails |
| [📊 Database Schema](docs/06-database/db-schema.md) | 13 tables, pgvector, ERD diagram |
| [🧪 Test Plan](docs/09-testing/test-plan.md) | 250+ tests, RAG evaluation, coverage strategy |
| [🚀 Deployment Guide](docs/10-deployment/deployment-guide.md) | Local, staging, production deployment |
| [👨‍💻 Developer Onboarding](docs/12-handover/developer-onboarding.md) | Setup, commands, conventions |

---

## 🛡️ Security

- **PHI Protection**: Permission filters applied at SQL JOIN level before LLM context assembly
- **Citation Validation**: Every LLM response verified against source database before streaming to client
- **Audit Trail**: Every access, denial, query, and config change logged with user+timestamp
- **Container Scanning**: Trivy scans on every CI push (CRITICAL+HIGH severity)
- **Secret Detection**: TruffleHog weekly scan across full git history
- **Dependency Monitoring**: Dependabot + pip-audit + npm audit for vulnerability tracking

---

<div align="center">

**Built with ❤️ for healthcare professionals**

*This project uses synthetic/de-identified data. It is a demonstration of engineering capability, not a certified medical device.*

</div>
