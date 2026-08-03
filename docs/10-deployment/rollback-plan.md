# Dokploy/VPS rollback and contingency plan

> Project: AI-Powered Hospital Knowledge Assistant  
> Target: 4 GB RAM / 45 GB disk VPS staging/demo
> Status: Operator runbook; provisioning and backup execution are not verified
> Last updated: 2026-08-04

This runbook covers the Dokploy-managed staging/demo stack only. The frontend
is hosted separately. The VPS may contain synthetic or de-identified data only;
it is not a production or clinical deployment boundary.

## 1. Network and service boundary

Dokploy's Traefik ingress is the only public entry point. PostgreSQL, Redis,
the background worker, and the backend service port stay private on the
Compose network. Do not publish their container ports on the VPS host.

| Component | Exposure | Operational rule |
|---|---|---|
| Dokploy/Traefik | Public 80/443 | Terminates the approved HTTPS route to the backend. |
| Backend | Private service port | Reachable through Traefik and the internal Compose network only. |
| PostgreSQL | Private service port | Reachable by backend/worker and the operator's backup procedure only. |
| Redis | Private service port | Reachable by backend/worker only. |
| Worker | No public listener | Runs document jobs from the private queue. |

## 2. Rollback decision and approval

Rollback is a manually approved operator action. A failed smoke check, a P0/P1
application defect, data-integrity risk, or a permission leak is sufficient to
pause promotion and start incident response. Record the incident, target
environment, current release identifier, requested rollback identifier, and
approver before invoking a rollback.

The repository rollback workflow accepts an immutable GHCR tag in the form
`sha-<short-sha>` produced by CI. An operator may use an immutable image digest
such as `sha256:<digest>` directly in Dokploy when the external hook/UI
contract supports digest input; do not convert it to a floating tag.

Never use `latest`, an unqualified branch name, or another floating tag as a
rollback target. Verify that the requested image exists in GHCR and record its
full reference before changing Dokploy.

The Task 2 rollback handoff is a separate contract from the normal deploy
handoff. The rollback workflow must pass the validated immutable backend image
reference and environment to a separately configured Dokploy rollback hook
(for example, the environment-scoped secret `DOKPLOY_ROLLBACK_HOOK_URL`). It
must not reuse the normal deploy hook implicitly. If the rollback hook is not
configured, the workflow must fail closed and the operator must use the
Dokploy UI with the same approval and evidence requirements. A successful
webhook request is only a handoff acknowledgement; it is not proof that the
VPS changed state.

### Operator-run rollback sequence

Run these steps from the approved operator workstation or Dokploy UI. Replace
every angle-bracket placeholder; do not paste credentials into a shell or into
this repository.

1. Freeze new promotion and note the incident timeline. If the backend is
   unsafe, disable its public route at Traefik/Dokploy while preserving access
   for the incident operator.
2. Confirm the target is staging/demo and confirm the exact immutable image
   reference. Verify the image digest, image architecture, and release commit
   against CI/GHCR evidence.
3. Confirm the pre-deployment database backup exists, is encrypted, and has a
   known restore-test result. If it does not, stop and obtain an explicit
   incident decision before continuing.
4. Confirm migration compatibility. Do not roll back an application image
   across a destructive or incompatible schema change. Use a forward fix or a
   coordinated database restore instead.
5. Obtain manual approval from `<APPROVER>` and invoke the separate Dokploy
   rollback hook with `<IMMUTABLE_BACKEND_IMAGE>` and `<ENVIRONMENT>`, or carry
   out the equivalent reviewed action in the Dokploy UI.
6. Wait for the Dokploy deployment result. Check the public HTTPS health route
   through Traefik and the private container health/status from the Dokploy
   console. Do not expose the backend port to perform the check.
7. Confirm worker and queue health, run the smallest applicable synthetic-data
   smoke flow, and check error/audit logs for the original symptom.
8. If health does not recover, keep the route disabled, escalate, and preserve
   logs, image references, database backup identifiers, and operator actions.

## 3. Migration safety

Database migrations are not automatically reversible just because the image is
reversible. Before deployment, the operator must:

1. review the migration for expand/contract compatibility;
2. take and validate an encrypted PostgreSQL backup;
3. deploy additive schema changes before code that depends on them;
4. avoid dropping or renaming data in the same release as an application
   rollback path; and
5. record the migration revision with the image reference.

If a migration fails, stop the release and keep the application on the last
compatible image where possible. Restore only after an incident decision,
because restoring PostgreSQL can discard writes made after the backup. A
database restore is a separate recovery operation, not a routine image
rollback.

## 4. PostgreSQL backup and restore

No backup schedule, destination, encryption key, retention job, or successful
restore is claimed by this document. An operator must configure and verify
these controls in Dokploy/the selected backup system before treating the VPS
as recoverable.

### Backup procedure

The following are operator-run examples with placeholders. Use a protected
backup host or approved encrypted object store; do not leave the only copy on
the 45 GB VPS disk.

```bash
# OPERATOR-RUN: substitute approved values; do not put secrets in this file.
COMPOSE_FILE="<absolute-path-to-infra/docker-compose.yml>"
BACKUP_ID="<UTC-timestamp-and-incident-or-release-id>"
PLAIN_DUMP="<protected-temporary-path>/${BACKUP_ID}.dump"
ENCRYPTED_DUMP="<protected-backup-destination>/${BACKUP_ID}.dump.age"

docker compose -f "$COMPOSE_FILE" exec -T postgres \
  pg_dump --format=custom --no-owner --no-acl \
  --username="<POSTGRES_USER>" --dbname="<POSTGRES_DB>" > "$PLAIN_DUMP"

# OPERATOR-RUN: obtain the recipient from the approved secret/key store.
age --encrypt --recipient "<BACKUP_ENCRYPTION_RECIPIENT>" \
  --output "$ENCRYPTED_DUMP" "$PLAIN_DUMP"

sha256sum "$ENCRYPTED_DUMP" > "${ENCRYPTED_DUMP}.sha256"
# Delete the plaintext dump after checksum/encryption verification.
```

The operator must verify the encrypted artifact, checksum, database revision,
backup timestamp, and off-host upload before deleting any local temporary
file. The minimum retention policy for this staging/demo profile is 14 daily
copies, 8 weekly copies, and 12 monthly copies, subject to the approved
storage budget. Apply retention after confirming that a newer restore point is
usable; never prune the only known-good copy.

### Restore procedure

Restore into an isolated database or maintenance window first. Confirm the
incident approval, target database, backup checksum, encryption-key access,
and expected data-loss window before replacing the active database.

```bash
# OPERATOR-RUN: verify the artifact and decrypt only on a protected host.
sha256sum --check "<encrypted-backup-path>.sha256"
age --decrypt --identity "<BACKUP_DECRYPTION_KEY_PATH>" \
  --output "<protected-temporary-path>/<BACKUP_ID>.dump" \
  "<encrypted-backup-path>"

# OPERATOR-RUN: stop application writes before restoring the selected target.
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" \
  exec -T postgres dropdb --if-exists --username="<POSTGRES_USER>" "<RESTORE_DB>"
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" \
  exec -T postgres createdb --username="<POSTGRES_USER>" "<RESTORE_DB>"
docker compose -f "<absolute-path-to-infra/docker-compose.yml>" \
  exec -T postgres pg_restore --exit-on-error --no-owner --no-acl \
  --username="<POSTGRES_USER>" --dbname="<RESTORE_DB>" \
  < "<protected-temporary-path>/<BACKUP_ID>.dump"
```

The destructive database commands above require an explicit operator change
approval and a verified target. Run schema, health, permission, and synthetic
smoke checks before reopening the Traefik route. Record the restored revision,
backup identifier, validation results, and any known data loss. Remove the
decrypted temporary file using the approved secure-destruction procedure.

## 5. R2 object retention and restore

R2 is the durable document source for this profile; the VPS storage volume is
not the authoritative copy. R2 bucket access, encryption, object versioning or
equivalent retention, lifecycle rules, and restore testing are not verified
here. Configure them through the approved Cloudflare account and record the
policy owner before loading even synthetic demo documents.

Required controls:

- Keep bucket encryption enabled and use client-side encryption for any export
  that leaves the provider boundary; store encryption keys separately from
  object data and application secrets.
- Retain current objects and recoverable prior versions/deletion markers for a
  documented period, with at least 14 daily recovery points for the demo
  profile. Confirm the chosen R2 plan and lifecycle behavior before relying on
  this number.
- Test restoration at least monthly and after a retention-policy change using
  synthetic data. Verify object checksum, metadata, content type, and
  application readability.
- Rotate R2 access keys on personnel change, suspected exposure, or the
  approved periodic schedule. Update backend and worker secrets together and
  revoke the old key only after the new key passes a controlled read/write
  check.

### Operator-run object restore

Use placeholders and an approved S3-compatible client. Do not print access
keys, signed URLs, or patient data in logs.

```bash
# OPERATOR-RUN: list the retained version for one synthetic object.
aws s3api list-object-versions \
  --bucket "<R2_BUCKET>" \
  --prefix "<OBJECT_KEY>" \
  --endpoint-url "<R2_ENDPOINT>"

# OPERATOR-RUN: copy the selected version to quarantine and verify it first.
aws s3api get-object \
  --bucket "<R2_BUCKET>" --key "<OBJECT_KEY>" \
  --version-id "<VERSION_ID>" \
  --endpoint-url "<R2_ENDPOINT>" "<QUARANTINE_PATH>"
sha256sum "<QUARANTINE_PATH>"

# OPERATOR-RUN: after approval, restore the verified object to its key.
aws s3 cp "<QUARANTINE_PATH>" \
  "s3://<R2_BUCKET>/<OBJECT_KEY>" \
  --endpoint-url "<R2_ENDPOINT>"
```

Apply the R2 bucket's provider-supported encryption policy or the approved
client-side encryption process; do not add an unsupported `--sse` option to
the R2 copy command.

If the required version is unavailable, do not improvise from the VPS cache;
escalate to the R2 account owner and use the last verified encrypted export.
Re-run document status/index checks after object restoration and record the
object version, checksum, and result.

## 6. Incident escalation

```text
Level 1: staging/demo operator — freeze promotion, preserve evidence, check health
  └── Level 2: technical lead — approve rollback, migration, or restore decision
        └── Level 3: security/data owner — assess access incidents and key rotation
```

Escalate immediately for suspected unauthorized access, corruption, lost
backup, repeated health failure, or exhausted disk/RAM. Preserve Dokploy
deployment history, Traefik/backend/worker logs, database and object backup
identifiers, image digest, migration revision, and the incident timeline.

## Change log

| Version | Date | Change |
|---|---|---|
| 3.0 | 2026-08-04 | Replaced legacy rollback assumptions with the Dokploy/VPS staging-demo operational contract. |
