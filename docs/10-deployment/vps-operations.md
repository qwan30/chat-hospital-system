# Dokploy/VPS staging-demo operations

> Profile: 4 GB RAM / 45 GB disk
> Scope: Vercel frontend plus Dokploy-managed VPS backend stack
> Data: synthetic or de-identified only
> Status: Runbook; no live provisioning or backup verification is claimed
> Last updated: 2026-08-04

This document is the day-two operating contract for a staging/demo VPS. It is
not a production-readiness, clinical-safety, or HIPAA certification.

## 1. Service boundary

Dokploy/Traefik owns the public HTTPS ingress. The backend is addressed through
the configured Traefik route; PostgreSQL, Redis, the worker, and the backend
container port remain private. Keep host port publishing disabled for those
services. The frontend remains on Vercel and must call the approved API origin.

The VPS image is selected by an immutable GHCR `sha-<short-sha>` tag or digest.
The Compose `latest` fallback is for local validation only and is not a
staging/demo release identity.

## 2. 4 GB / 45 GB preflight

Run the following checks as an operator before first installation, every
release, and after an incident. These commands are intentionally placeholders
for the actual operator host and route.

```bash
# OPERATOR-RUN: resource and swap checks.
free -h
df -h "<VPS_DATA_MOUNT>"
swapon --show

# OPERATOR-RUN: confirm only the intended public listeners exist.
ss -ltnp

# OPERATOR-RUN: inspect service resource use and health.
docker stats --no-stream
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" ps
curl --fail --silent --show-error "https://<API_DOMAIN>/api/v1/health"
```

Record free disk, used RAM, swap activity, listening ports, image digests,
container health, and the backup/restore-test identifiers. Stop the operation
if disk headroom is insufficient for a database dump plus image pull, swap is
thrashing, an unexpected public listener exists, or a required service is
unhealthy. Keep enough headroom for one image replacement and temporary backup
artifacts; the 45 GB disk is not a backup repository.

## 3. Release and rollback operations

1. Confirm the release is staging/demo-only and contains no real patient data.
2. Confirm the CI artifact is an immutable tag or digest and that its migration
   is expand/contract compatible.
3. Confirm an encrypted PostgreSQL backup and a recoverable R2 object version
   or export exist. Their existence and restore-test result must be recorded;
   neither is configured by this repository.
4. Confirm the required backend/worker secrets are present in Dokploy and not
   in Git or Vercel client variables.
5. Use the normal Dokploy deploy handoff for a release. Production promotion is
   outside this runbook and must remain manually approved and environment-gated.
6. After Dokploy reports completion, check the Traefik HTTPS health route,
   container health, worker queue activity, and a small synthetic document/chat
   flow. A webhook acknowledgement alone is not a deployment proof.
7. For a rollback, use the separate Task 2 Dokploy rollback hook and pass the
   approved immutable image reference. Require manual approval; do not switch
   to a floating tag or bypass the migration-safety check.

See [`rollback-plan.md`](rollback-plan.md) for the full image, database, and
object recovery procedures.

## 4. Backup, retention, and restore controls

Before the VPS is used for a demo, the operator must configure and evidence:

| Control | Required contract | Evidence to retain |
|---|---|---|
| PostgreSQL backup | Custom-format dump, encrypted off-host, checksum recorded | Backup ID, revision, destination, checksum |
| PostgreSQL retention | At least 14 daily, 8 weekly, and 12 monthly copies unless an approved policy says otherwise | Retention policy and pruning log |
| PostgreSQL restore test | Monthly and after backup-policy changes, with synthetic data | Test date, restored revision, validation result |
| R2 retention | Encryption plus versioning or equivalent recoverable retention and lifecycle policy | Bucket policy, object version, checksum |
| R2 restore test | Monthly and after retention changes; verify metadata and application readability | Object key/version, checksum, result |
| Secret rotation | Rotate database, R2, provider, and auth secrets through Dokploy/secret manager; revoke old values after a controlled check | Rotation ticket and verification result |

Use placeholders only and follow the procedures in `rollback-plan.md`. Never
store plaintext dumps, decrypted exports, credentials, or signed URLs in this
repository. No backup or restore success is implied by the presence of a
runbook.

## 5. Resource-aware observability

Observability is opt-in. Measure the base stack first; do not enable the full
observability overlay on a 4 GB VPS until RAM, disk, CPU, and swap behavior have
been recorded under a representative synthetic workload. If enabled, add one
component at a time, cap retention, and re-run the preflight checks. A resource
alert is a reason to disable the overlay, not to expand public exposure.

The minimum operating signal set is:

- Traefik route and TLS health;
- backend health and 5xx/error rate;
- PostgreSQL/Redis/worker container health;
- queue age and failed-job count;
- free disk, RAM, swap, and container restart count;
- backup age, checksum, retention state, and latest restore-test result; and
- R2 object/index status for the synthetic demo corpus.

Do not put secrets, access tokens, document contents, or patient identifiers in
logs, metrics labels, screenshots, or incident tickets.

## 6. Incident response and escalation

On an incident, freeze promotion, capture the exact image digest and migration
revision, check the public health route and private service health, and preserve
logs before restarting anything. Disable the Traefik route when the application
could leak data or corrupt writes. Do not expose a private service port as a
diagnostic shortcut.

```text
Level 1: staging/demo operator — triage, preserve evidence, freeze promotion
  └── Level 2: technical lead — approve image rollback or data restore
        └── Level 3: security/data owner — access incident, retention, and key rotation
```

Escalate immediately for suspected unauthorized access, missing or untested
backups, corruption, repeated health-check failure, disk exhaustion, or RAM /
swap exhaustion. Resume the route only after the incident owner records the
validation result and approval.

## 7. Change boundaries

This profile is a staging/demo contract. It does not authorize live Dokploy,
VPS, DNS, R2, database, provider, or secret provisioning. It does not approve
production traffic, real PHI, clinical use, or regulatory certification.

## Change log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-08-04 | Added the 4 GB / 45 GB Dokploy/VPS day-two operations runbook. |
