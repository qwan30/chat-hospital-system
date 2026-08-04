# VPS / Dokploy preflight operations contract

> Scope: operator-run preflight for a Vercel frontend plus Dokploy-managed API
> and worker deployment
> Data policy: synthetic or de-identified data only
> Evidence status: external state remains UNVERIFIED until an operator records
> candidate-specific evidence in `vps-preflight-evidence.md`
> Last updated: 2026-08-04

This document is a repository-side operating contract only. Repository validation is static only; it does not prove live VPS, Dokploy, DNS, GHCR, R2, HTTPS, backup, restore, or runtime health state.

Use placeholders only. Do not paste secrets, real domains, private IPs, SSH key
material, access tokens, or provider-specific values into this repository.

## 1. Candidate identity and change boundary

Record the deployment candidate before touching a VPS or Dokploy project:

- Candidate SHA: `<CANDIDATE_SHA>`
- CI Run ID: `<CI_RUN_ID>`
- VPS hostname: `<VPS_HOST>`
- Dokploy domain: `https://<DOKPLOY_DOMAIN>`
- Backend API domain: `https://<API_DOMAIN>`
- Frontend origin on Vercel: `https://<VERCEL_FRONTEND_ORIGIN>`

The expected frontend-to-backend route contract is:

```bash
VITE_API_URL=https://<API_DOMAIN>/api/v1
HOSPITAL_AI_CORS_ORIGINS=https://<VERCEL_FRONTEND_ORIGIN>
```

Do not treat a template, screenshot placeholder, or repository check as proof that the route is live. The route remains UNVERIFIED until an operator captures candidate-specific evidence.

## 2. Safe operator commands

Run the following commands from an operator workstation or the target VPS, as
noted. These are read-only or narrowly scoped verification commands. They do
not provision infrastructure, rotate secrets, or make destructive firewall or
container changes.

### 2.1 OS, RAM, disk, and swap

Run on the target VPS:

```bash
cat /etc/os-release
uname -a
free -h
df -h "<VPS_DATA_MOUNT>"
swapon --show
```

Expected evidence:

- OS family and version are captured exactly as reported by the host.
- RAM and disk headroom are sufficient for one image pull plus normal staging
  workload.
- Swap state is recorded exactly as observed; if swap is disabled, record that
  explicitly instead of assuming it exists.

### 2.2 SSH key access

Run from the operator workstation:

```bash
ssh -o BatchMode=yes -i "<SSH_PRIVATE_KEY_PATH>" "<VPS_USER>@<VPS_HOST>" "echo ssh-key-auth-ok"
```

Expected evidence:

- Key-based access succeeds without prompting for a password.
- The operator records only the success/failure result and target identity.
- Do not commit private key paths that reveal user-specific workstation layout
  if that is sensitive in your environment.

### 2.3 Firewall policy and listener review

Run on the target VPS:

```bash
ufw status numbered
ss -ltnp
ss -ltn "( sport = :22 or sport = :80 or sport = :443 or sport = :3000 )"
```

Expected evidence:

- Firewall policy is recorded as observed.
- Listener review explicitly covers ports `22`, `80`, `443`, and `3000`.
- Any public exposure of port `3000` is recorded with operator justification.
- Unexpected listeners are treated as a blocker, not silently accepted.

### 2.4 Docker and Compose versions

Run on the target VPS:

```bash
docker --version
docker compose version
docker info --format '{{.ServerVersion}}'
```

Expected evidence:

- Docker Engine version is captured verbatim.
- Docker Compose plugin version is captured verbatim.
- The operator records the exact version strings instead of "latest" or
  "installed".

### 2.5 Dokploy installation and domain

Run on the target VPS or an operator workstation, depending on access method:

```bash
docker ps --format '{{.Names}} {{.Status}}' | grep -i dokploy
curl --fail --silent --show-error --head "https://<DOKPLOY_DOMAIN>"
```

Expected evidence:

- Dokploy presence is recorded as observed; absence remains a blocker.
- The Dokploy domain and HTTPS response are recorded as operator evidence only.
- Do not claim that Dokploy is installed or routable unless the operator has
  actually captured the result.

### 2.6 GitHub source and GHCR image access

Run with operator-approved credentials already present in the session. Do not
place credentials in the command history or this repository.

```bash
git ls-remote "git@github.com:<GITHUB_ORG>/<REPO>.git" HEAD
docker manifest inspect "ghcr.io/<GHCR_NAMESPACE>/<IMAGE_NAME>:sha-<CANDIDATE_SHA>"
```

Expected evidence:

- GitHub connectivity to the intended repository is confirmed for the exact
  deployment source.
- GHCR lookup resolves the candidate image tag or digest intended for the VPS.
- Failure to authenticate is recorded as UNVERIFIED, not papered over by the
  presence of a CI workflow.

### 2.7 Candidate image migration and rollout

The normal Dokploy path consumes the GitHub-built image. The source clone on a
VPS is not a build input. Do not run `git pull`, `docker compose build`, or
`infra/docker-compose.local-build.yml` for staging.

When the operator must verify the equivalent Compose procedure, use the exact
candidate image and the following order. Replace every placeholder before
running; do not put credentials in the command history or this repository.

```bash
export BACKEND_IMAGE="ghcr.io/<GHCR_NAMESPACE>/hospital-ai-backend:sha-<CANDIDATE_SHA>"
docker manifest inspect "$BACKEND_IMAGE"
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" pull postgres redis backend worker
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" run --rm --no-deps backend alembic upgrade head
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" up -d postgres redis backend worker
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" ps
docker stats --no-stream
curl --fail --silent --show-error "https://<API_DOMAIN>/api/v1/health"
```

The migration container, backend, and worker must resolve to the same
`BACKEND_IMAGE`. Record the migration revision, image digest, source SHA,
container health, public health result, synthetic/de-identified smoke result,
RAM, swap, disk, and `docker stats` output in the evidence table. Dokploy may
execute the same sequence through its UI or deploy hook; a hook acknowledgement
alone is not deployment or runtime proof.

### 2.8 Secret injection contract

Verify secret key names only. Do not print values.

```bash
printf '%s\n' \
  HOSPITAL_AI_DATABASE_URL \
  HOSPITAL_AI_REDIS_URL \
  HOSPITAL_AI_GEMINI_API_KEY \
  HOSPITAL_AI_R2_ENDPOINT \
  HOSPITAL_AI_R2_BUCKET \
  HOSPITAL_AI_R2_ACCESS_KEY_ID \
  HOSPITAL_AI_R2_SECRET_ACCESS_KEY \
  HOSPITAL_AI_JWT_ISSUER \
  HOSPITAL_AI_JWKS_URL \
  HOSPITAL_AI_JWT_AUDIENCE
```

Operator checkpoint:

- In Dokploy, verify that the required secret keys exist for the backend and
  worker without exposing their values.
- Record only key presence, secret source owner, and timestamp.
- Repository validation does not prove that secrets were injected correctly.

### 2.9 Vercel-to-API route

Check the expected browser route contract and the backend health path using
placeholder values only:

```bash
printf '%s\n' "VITE_API_URL=https://<API_DOMAIN>/api/v1"
printf '%s\n' "HOSPITAL_AI_CORS_ORIGINS=https://<VERCEL_FRONTEND_ORIGIN>"
curl --fail --silent --show-error "https://<API_DOMAIN>/api/v1/health"
```

Expected evidence:

- The Vercel build-time API base includes the explicit `/api/v1` suffix.
- The backend CORS origin is an explicit allowlist entry for the frontend
  origin; wildcard CORS is not acceptable.
- Health-route success, if any, is operator-captured runtime evidence and must
  stay outside repository-only proof claims.

## 3. Operator preflight checklist

Treat the following as a blocking preflight sequence:

1. Record `<CANDIDATE_SHA>` and `<CI_RUN_ID>`.
2. Confirm synthetic or de-identified data usage only.
3. Capture OS, version, RAM, disk, and swap evidence.
4. Prove SSH key access without disclosing key material.
5. Capture firewall and listener evidence for `22/80/443/3000`.
6. Capture Docker Engine and Docker Compose versions.
7. Capture Dokploy presence and domain evidence.
8. Capture GitHub repository reachability and GHCR candidate-image reachability.
9. Verify the candidate pull, one-off migration, same-image backend/worker
   rollout, and container health.
10. Confirm required secret key names are present in Dokploy without exposing
   values.
11. Capture the exact Vercel-to-API route contract:
    `VITE_API_URL=https://<API_DOMAIN>/api/v1` and
    `HOSPITAL_AI_CORS_ORIGINS=https://<VERCEL_FRONTEND_ORIGIN>`.

If any step is missing, the deployment remains UNVERIFIED and should not be
described as provisioned, ready, healthy, or externally validated.

## 4. What this contract does not prove

This repository does not claim that any of the following have been completed or
verified:

- VPS provisioning
- Dokploy installation completion
- DNS cutover
- GHCR credential setup
- Cloudflare R2 configuration
- secret correctness
- HTTPS certificate issuance
- backup creation
- restore success
- runtime health or load behavior

Those checks require operator-captured evidence outside the repository and must
remain explicitly UNVERIFIED until recorded.
