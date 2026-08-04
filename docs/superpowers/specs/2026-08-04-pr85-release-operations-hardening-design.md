# PR #85 Release and Operations Hardening Design

## Context

PR #85 adds release records, a Dokploy staging smoke test, and VPS operations runbooks. Review found five correctness gaps: image verification can fail open and records the wrong digest, the smoke job cannot reliably read the staging environment URL, queue monitoring targets queues the worker does not consume, the JWKS incident procedure recommends an ineffective algorithm switch, and the R2 recovery procedure assumes versioning/cache behavior that the application does not implement.

## Goals

- Make immutable-image verification fail closed and record the top-level registry manifest digest.
- Make staging smoke checks use the `staging` GitHub Environment, validate configuration, and fail the staging workflow when health checks fail.
- Keep production promotion manual while requiring a concrete staging smoke run identifier for approver review.
- Align all worker monitoring commands with `document-indexing` and `cdss-analysis`.
- Keep authentication fail-closed during JWKS outages; do not switch signing algorithms as an incident shortcut.
- Replace unsupported R2 versioning/local-cache claims with an explicit off-host backup and restore policy.
- Add repository contract tests that prevent these regressions.

## Non-goals

- Provisioning Dokploy, Cloudflare R2, GitHub Environments, cron, or systemd from this repository.
- Implementing automatic cross-run attestation for production promotion.
- Adding an application-level R2 failover cache.
- Changing the worker queue topology or JWT implementation.

## Design

### Release identity verification

The CD workflow will use `docker buildx imagetools inspect --format '{{json .Manifest}}'` and `jq -er` to extract `.digest`. Both commands run under `set -euo pipefail`. The step rejects any value that does not match `sha256:` followed by exactly 64 lowercase hexadecimal characters. No `unknown` fallback is allowed.

Production hook configuration is checked before a release record can be written. A release record is emitted only after the Dokploy hook accepts the handoff. Staging without a configured hook remains a clearly labeled pending/no-op state.

### Staging smoke test

The smoke job binds to the `staging` GitHub Environment and reads `DOKPLOY_APP_URL` through job-level environment configuration. It rejects a missing or malformed HTTP(S) base URL before making requests. Health checks use explicit connection and total timeouts and five attempts, with sleeps of 30, 60, 120, and 240 seconds between attempts. The job is blocking; a failed smoke check makes the staging CD run fail.

Production remains a separate manual dispatch. Production dispatch requires a numeric `staging-smoke-run-id`; the workflow includes a link to that run in the handoff payload and release summary. The production environment approver must inspect that run and confirm it is the successful staging evidence for the supplied source SHA. The repository does not claim automatic cryptographic linkage between the two runs.

### Worker monitoring

Runbooks will monitor the two queue names defined by `WORKER_QUEUE_NAMES`: `document-indexing` and `cdss-analysis`. Queue depth uses RQ's queue objects, and failed-job counts use `FailedJobRegistry` for each queue. References to `rq:queue:default` and `rq:queue:failed` are removed.

### JWKS outage handling

The documented response remains fail-closed. Operators check HMS IdP status, DNS, routing, TLS, and the JWKS endpoint; preserve cached operation while it still works; and restore the configured JWKS path. The runbook explicitly prohibits switching RS256/JWKS to HS256 during an outage because the current implementation prioritizes configured JWKS and because an algorithm change alters the trust model.

### R2 backup and outage handling

R2 remains authoritative. The application does not provide an automatic local-document fallback when the R2 backend is selected. The runbook therefore requires scheduled copies to an independent approved backup destination using timestamped/immutable backup keys, plus monthly restore tests to a separate bucket or prefix. It does not claim provider-side object versioning or non-current-version lifecycle support.

During an outage, new uploads and reads requiring R2 fail. Operators avoid destructive retries, monitor provider status, preserve queued work, and resume/retry after recovery.

### Backup and disk safety

The PostgreSQL backup section distinguishes policy from automation: an external scheduler must invoke the command. Temporary plaintext dumps are created with restrictive permissions and removed through a shell trap after encryption. Disk incidents use targeted inspection and image pruning rather than unconditional `docker system prune -f`.

## Tests

A focused contract test file will read the workflow and runbooks as text and assert:

- digest verification has no fail-open fallback and validates a full SHA-256 digest;
- the smoke job is bound to staging, validates the URL, has request timeouts, and is not advisory;
- production requires a staging smoke run ID;
- documented queue names match the worker constants;
- unsupported HMAC fallback, R2 object-versioning, local-cache fallback, and unsafe blanket-prune claims are absent.

The workflow YAML will also be parsed with PyYAML as a syntax check. Existing CI remains the final repository-wide verification.
