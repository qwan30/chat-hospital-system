# Task 1 Implementation Report — Freeze Dokploy/VPS Deployment Contract

## Status

DONE_WITH_CONCERNS — the selected Vercel + Dokploy/Traefik contract is frozen for the Compose/docs layer. The existing SSH GitHub Actions workflow still describes the older direct-Compose deployment and needs a separate follow-up before it is enabled for Dokploy.

## Delivered

- Updated `infra/docker-compose.yml` to remove Nginx and all public PostgreSQL, Redis, and backend host port mappings.
- Added a shared backend/worker environment contract for R2, Gemini, explicit OpenAI-compatible/DeepSeek configuration, HMS, and RS256/JWKS.
- Added `BACKEND_IMAGE`/`IMAGE_TAG` support so releases can use an immutable GHCR tag or digest.
- Updated `.env.example` to label Ollama as local-only and document Gemini, DeepSeek-compatible, and HMS JWT variables.
- Updated deployment and environment-variable guides for Vercel frontend + Dokploy/Traefik API routing, R2 storage, staging/demo boundaries, and backend-only secrets.
- Updated deployment contract tests for the new no-Ollama/no-Nginx/private-port contract.
- Supabase remains out of scope; no Supabase implementation existed on the branch or in the preserved stash.

## Verification

```text
docker compose -f infra/docker-compose.yml config --quiet
PASS (warnings only because local shell has no deployment secrets)

docker compose -f infra/docker-compose.yml config --format json
PASS; backend exposes only internal 8000; PostgreSQL/Redis have no host ports;
chat/embedding defaults are gemini; storage backend is r2; JWT algorithm is RS256.

git diff --check
PASS

& .\\app\\backend\\.venv\\Scripts\\python.exe -m pytest app/backend/tests/test_deployment_contracts.py -q -p no:cacheprovider
6 passed, 1 warning
```

Literal scan passed: no `nginx:` service, no `HOSPITAL_AI_OLLAMA_BASE_URL` in the production Compose file, and no public `5432`, `6379`, or `8000` mapping.

## Remaining concerns

- Dokploy route/network configuration is external to this repository and must map `api.<domain>` to `backend:8000` through Traefik.
- `.github/workflows/cd.yml`, rollback, and security-scan workflows still contain older direct-Compose/image-path assumptions; update them in a later deployment automation task.
- Compose intentionally warns when secrets are absent during local validation. Dokploy must inject `POSTGRES_PASSWORD`, Gemini/R2 credentials, and HMS JWT values before deployment.
- DeepSeek is an explicit OpenAI-compatible provider configuration, not automatic fallback. Provider fallback belongs in a later application-code task.
