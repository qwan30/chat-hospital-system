head_sha=29e5b8351f6be40fbe235ff7728b1dcffef287a1
backend: python -m ruff check .
migration: alembic upgrade head && alembic check
frontend: bun run lint && bun run typecheck && bun run test && bun run build
e2e: bun run test:e2e -- cdi-v2-document-intelligence.spec.ts
