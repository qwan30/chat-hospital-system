# Deployment Task 3 report — VPS operational safety

## Outcome

Replaced the stale rollback notes with a Dokploy/VPS staging-demo operations
contract for the measured 4 GB RAM / 45 GB disk profile.

## Delivered

- Documented private service boundaries, immutable release rollback, migration
  compatibility, manual approval, and separate Dokploy rollback-hook behavior.
- Added operator-run encrypted PostgreSQL backup/restore examples with
  checksum, off-host retention, restore-test, and secure-destruction controls.
- Added Cloudflare R2 retention/versioning/restore and key-rotation controls
  without claiming that the bucket or backup system is provisioned.
- Added resource, disk, swap, port, health, queue, and opt-in observability
  checks appropriate for the 4 GB / 45 GB VPS.
- Removed legacy Ollama/direct-Nginx rollback assumptions and kept the profile
  synthetic/de-identified-data-only.

## Verification

- `git diff --check` passed.
- Owned runbooks were searched for stale direct-Nginx/Ollama runtime claims and
  real credentials; none were introduced.

## External boundary

No Dokploy, VPS, DNS, R2, backup schedule, encryption key, restore test, or
production/PHI approval is claimed by these documents.
