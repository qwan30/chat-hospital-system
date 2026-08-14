# Backend-Issued Demo Authentication Design

**Date:** 2026-08-14  
**Branch:** `feat/demo-auth-token-endpoint`

## Problem

The login page renders a `Demo Role` tab that currently calls
`SessionProvider.signIn()`. That path derives static bearer values such as
`dev-doctor` in the browser and puts them into the in-memory API client. A
deployment can therefore render a successful-looking session while every
protected API rejects the static token with HTTP 401.

The existing `Real Login` path remains the primary credential flow. This
change only replaces the production-facing Demo Role authentication path and
makes its availability authoritative from the backend.

## Goals and non-goals

Goals:

- Keep the current two-tab login layout and one-click role selection.
- Add a backend `POST /auth/demo` contract that accepts only an allowlisted
  demo role and returns a backend-signed, short-lived JWT.
- Add a public `GET /auth/demo/status` contract so the frontend hides Demo Role
  when the backend has demo authentication disabled or cannot issue tokens.
- Keep demo tokens in frontend memory only.
- Limit demo issuance to the known synthetic seeded users and preserve the
  existing database RBAC and patient-scope checks.
- Add regression tests for disabled mode, invalid roles, token claims,
  expiry/validation, frontend requests, and the visible login flow.

Non-goals:

- Replacing HMS/OIDC authentication for real staff.
- Persisting demo credentials or bearer tokens in browser storage.
- Making the existing local static-token compatibility path a production auth
  mechanism.
- Adding real patient data or widening any patient permission scope.

## Architecture

```text
LoginPage
   │ GET /auth/demo/status
   │
   ├── enabled=false or unavailable → render Real Login only
   │
   └── enabled=true
         │ POST /auth/demo { role: "cardiologist" }
         ▼
   Backend allowlist → synthetic User row → HS256 demo JWT
         │
         ▼
   AuthProvider memory token → GET /auth/me → SessionProvider
         │
         ▼
   Existing API bearer + RBAC + patient permission enforcement
```

The backend owns the allowlist from frontend role IDs to the seeded synthetic
user emails. The request cannot select an arbitrary email, user ID, scope, or
workspace. A demo token contains `demo=true`, the selected canonical user
claims, issuer, issued-at time, and an expiration bounded by configuration.
The existing `get_current_user` dependency validates normal JWTs first and
then validates demo JWTs only when `demo_mode` and the demo signing secret are
configured. Both paths still resolve an active local `User`, so the existing
RBAC and ABAC checks remain authoritative.

The frontend receives the selected persona separately from the canonical
backend role so `hospitalist` can continue to use the existing portfolio
persona UI while the backend enforces the seeded doctor's actual permissions.
The bearer remains memory-only through the existing `api-client` contract.

## Configuration

Backend settings:

- `HOSPITAL_AI_DEMO_MODE` controls whether demo auth is offered.
- `HOSPITAL_AI_DEMO_JWT_SECRET` is a backend-only HS256 signing secret. It has
  no committed production value; the endpoint is unavailable if it is empty.
- `HOSPITAL_AI_DEMO_TOKEN_TTL_MINUTES` bounds the demo JWT lifetime and defaults
  to 30 minutes.
- `HOSPITAL_AI_DEMO_JWT_ISSUER` identifies demo-issued tokens and defaults to
  `hospital-ai-demo`.

The status endpoint reports enabled only when both `demo_mode` and the signing
secret are present. Production operators can therefore disable the UI and
endpoint with one environment setting and cannot accidentally enable issuing
tokens without a secret.

## Error behavior

- Invalid role: HTTP 422 from schema validation.
- Demo mode disabled: HTTP 403 with a stable non-secret detail message.
- Demo mode enabled but signing secret missing: HTTP 503; the status endpoint
  reports disabled.
- Allowlisted synthetic user missing or inactive: HTTP 503; do not disclose
  user details.
- Expired, malformed, or demo-disabled bearer: HTTP 401 through the existing
  auth dependency.
- Frontend status/network failure: hide Demo Role and leave Real Login usable.
- Frontend demo login failure: show the backend-safe error and do not navigate.

## Verification

- Backend unit tests exercise settings/status, role allowlisting, JWT claims,
  disabled mode, missing secret, invalid/expired token, and active-user lookup.
- Frontend unit tests exercise status gating, demo POST payload, memory-only
  token handling, verification, failure state, and persona propagation.
- Playwright auth-flow tests stub only the public status and demo auth contract,
  click the real UI controls, and assert the dashboard navigation. Existing
  business-flow seed helpers remain test-only compatibility fixtures and are
  not used by the production login path.
- Run backend tests/lint/format, frontend Vitest/typecheck/lint, diff checks,
  GitNexus `detect_changes`, and the repository CI checks before merge.
