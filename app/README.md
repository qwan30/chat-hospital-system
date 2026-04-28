# Application Workspace

This folder separates executable application code from the root documentation pack.

| Folder | Purpose |
|---|---|
| `frontend/` | Next.js 16, React 19, TypeScript, Tailwind v4, shadcn-style UI. |
| `backend/` | FastAPI, SQLAlchemy, PostgreSQL/SQLite dev support, OCR/indexing hooks, permission-filtered RAG, shared chat threads, general knowledge answers, and HMS appointment evidence import. |

Use `app/frontend` as the working directory for frontend commands:

```bash
cd app/frontend
npm run dev
```

Use `app/backend` as the working directory for backend commands:

```bash
cd app/backend
python -m pytest
python scripts/seed_dev.py
```
