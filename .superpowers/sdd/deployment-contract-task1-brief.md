# Task 1 Brief — Freeze Dokploy/VPS Deployment Contract

## Objective

Freeze the repository contract for the selected deployment shape:

- frontend remains on Vercel;
- backend and RQ worker run on the Dokploy-managed VPS;
- Dokploy/Traefik owns public HTTPS routing;
- PostgreSQL and Redis remain private Compose services;
- Ollama is not part of the VPS deployment;
- Gemini is the configured chat and embedding provider;
- the existing OpenAI-compatible contract is documented for a future or explicit DeepSeek chat deployment;
- Cloudflare R2 is the durable document storage backend;
- HMS JWT/OIDC uses RS256/JWKS in non-local environments;
- Supabase is out of scope for this deployment.

## Owned files

- `infra/docker-compose.yml`
- `app/backend/.env.example`
- `docs/10-deployment/env-variables.md`
- `docs/10-deployment/deployment-guide.md` only if the Compose/Dokploy routing contract needs a concise correction.

Do not edit application provider/auth/storage symbols in this task. Do not edit or restore the user's previous Supabase branch changes. Do not commit secrets or a real `.env` file.

## Required contract

1. Remove the application Nginx service and its public port mapping from the Dokploy Compose stack; Dokploy/Traefik is the public ingress.
2. Do not publish PostgreSQL or Redis host ports by default. Keep them reachable by service name inside the Compose network.
3. Backend is reachable internally on port 8000 and may use `expose`, not a public `ports` mapping.
4. Remove Ollama as the deployment default and do not include an Ollama service.
5. Backend and worker receive the same required runtime configuration for database, Redis, R2, Gemini, OpenAI-compatible/DeepSeek, HMS, and JWT settings.
6. Production examples must use placeholders for secrets and exact variable names already supported by `app/backend/src/hospital_ai/core/config.py`.
7. The docs must distinguish `HOSPITAL_AI_CHAT_PROVIDER=gemini` from the OpenAI-compatible `openai` provider configured with a DeepSeek base URL; Task 1 must not claim automatic provider fallback.
8. The docs must state that Vercel supplies `VITE_API_URL` pointing at the API domain and that R2/LLM/JWT secrets are backend-only.
9. The docs must state that the deployment is staging/demo unless separate hospital production approval and PHI controls exist.
10. The backend and worker image must accept `BACKEND_IMAGE` so Dokploy/CI can deploy an immutable SHA tag or digest; `latest` is only a local validation fallback.

## Verification

Run from the repository root:

```powershell
docker compose -f infra/docker-compose.yml config --quiet
git diff --check
```

Also run a literal scan proving the production Compose file no longer contains an `nginx:` service or an `HOSPITAL_AI_OLLAMA_BASE_URL` environment entry, while the local `.env.example` may retain Ollama as a local-only option if clearly labeled.

The implementer must report the exact files changed, verification commands/results, and any remaining contract gap. Commit only the owned files and this task's process brief/report if those artifacts are created.
