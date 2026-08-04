# VPS / Dokploy preflight evidence template

> Purpose: operator-captured evidence for the Task 6 preflight contract
> Candidate identity placeholders: `<CANDIDATE_SHA>` and `<CI_RUN_ID>`
> Data policy: synthetic or de-identified data only
> Evidence boundary: repository validation is static only and does not prove
> live VPS, Dokploy, DNS, GHCR, R2, HTTPS, backup, restore, or runtime health
> state

Every row in this template starts as `PENDING — operator evidence required`.
Do not convert template presence into a deployment-pass claim. External state
remains UNVERIFIED until an operator records the observed value, timestamp, and
owner for the exact candidate.

| Status | Check | Command | Expected result | Operator-captured value | Timestamp | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| PENDING — operator evidence required | Candidate SHA pinned | `git rev-parse --verify <CANDIDATE_SHA>` | Candidate commit resolves exactly once | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | CI Run ID recorded | `printf '%s\n' "<CI_RUN_ID>"` | Run ID matches the deployment candidate approval record | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Synthetic/de-identified data only | `printf '%s\n' "synthetic-or-de-identified-only"` | Operator confirms no real patient data is used for this environment | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | OS and version | `cat /etc/os-release` | Host OS family and version are captured verbatim | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | RAM headroom | `free -h` | Total and available RAM are captured verbatim | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Disk headroom | `df -h "<VPS_DATA_MOUNT>"` | Target mount has recorded free/used space for the candidate window | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Swap configured or absent | `swapon --show` | Swap state is recorded exactly as observed | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | SSH key access | `ssh -o BatchMode=yes -i "<SSH_PRIVATE_KEY_PATH>" "<VPS_USER>@<VPS_HOST>" "echo ssh-key-auth-ok"` | Key-based access succeeds without password prompt | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Firewall policy | `ufw status numbered` | Firewall rules for the host are captured verbatim | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Listener review for 22/80/443/3000 | `ss -ltn "( sport = :22 or sport = :80 or sport = :443 or sport = :3000 )"` | Only approved listeners are present; any port `3000` exposure is justified explicitly | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Docker server version | `docker --version` | Docker Engine version string is captured verbatim | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Docker Compose version | `docker compose version` | Docker Compose plugin version string is captured verbatim | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Dokploy installed | `docker ps --format '{{.Names}} {{.Status}}' | grep -i dokploy` | Dokploy presence is confirmed or recorded as missing | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Dokploy domain and HTTPS route | `curl --fail --silent --show-error --head "https://<DOKPLOY_DOMAIN>"` | Dokploy domain responds for the operator, or remains UNVERIFIED if unreachable | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | GitHub source connection | `git ls-remote "git@github.com:<GITHUB_ORG>/<REPO>.git" HEAD` | Intended GitHub deployment source is reachable with operator-approved credentials | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | GHCR candidate image access | `docker manifest inspect "ghcr.io/<GHCR_NAMESPACE>/<IMAGE_NAME>:sha-<CANDIDATE_SHA>"` | Candidate image tag or digest resolves for the operator | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Candidate image pulled | `docker compose -f "<absolute-path-to-infra/docker-compose.yml>" pull postgres redis backend worker` | Exact candidate image and dependent base images pull successfully | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Migration revision recorded | `docker compose -f "<absolute-path-to-infra/docker-compose.yml>" run --rm --no-deps backend alembic upgrade head` | Migration completes and the resulting database revision is recorded against the candidate SHA | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Backend and worker use same image | `docker compose -f "<absolute-path-to-infra/docker-compose.yml>" images backend worker` | Backend and worker resolve to the same immutable image or digest | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Container health after rollout | `docker compose -f "<absolute-path-to-infra/docker-compose.yml>" ps` | Backend, worker, PostgreSQL, and Redis statuses are captured for the candidate | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Container memory evidence | `docker stats --no-stream` | Actual usage is recorded against the 4 GB VPS ceilings | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Synthetic runtime smoke | `printf '%s\n' "auth R2 worker Gemini SSE synthetic smoke"` | Operator records candidate-specific smoke results without real patient data | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Secret key presence only | `printf '%s\n' HOSPITAL_AI_DATABASE_URL HOSPITAL_AI_REDIS_URL HOSPITAL_AI_GEMINI_API_KEY HOSPITAL_AI_R2_ENDPOINT HOSPITAL_AI_R2_BUCKET HOSPITAL_AI_R2_ACCESS_KEY_ID HOSPITAL_AI_R2_SECRET_ACCESS_KEY HOSPITAL_AI_JWT_ISSUER HOSPITAL_AI_JWKS_URL HOSPITAL_AI_JWT_AUDIENCE` | Required key names are present in Dokploy; no secret values are exposed | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Vercel `VITE_API_URL` route | `printf '%s\n' "VITE_API_URL=https://<API_DOMAIN>/api/v1"` | Frontend build-time API base includes the explicit `/api/v1` suffix | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | Backend CORS allowlist for Vercel origin | `printf '%s\n' "HOSPITAL_AI_CORS_ORIGINS=https://<VERCEL_FRONTEND_ORIGIN>"` | Backend CORS policy uses an explicit Vercel origin allowlist entry and never `*` | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |
| PENDING — operator evidence required | API health route from the approved domain | `curl --fail --silent --show-error "https://<API_DOMAIN>/api/v1/health"` | Health route result is operator-captured runtime evidence only; template presence is not proof | `<operator-recorded-value>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<owner>` |

## External-state reminders

- `PENDING — operator evidence required` is the correct repository default for
  every row in this template.
- A filled template row is still not a substitute for separate runtime,
  rollback, backup, restore, or incident evidence.
- If a check has not been executed for `<CANDIDATE_SHA>` and `<CI_RUN_ID>`, mark
  it UNVERIFIED in human reporting even if the template exists in git.
