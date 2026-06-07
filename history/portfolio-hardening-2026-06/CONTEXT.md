# Portfolio Hardening 2026-06 Context

## Objective

Upgrade the AI-Powered Hospital Knowledge Assistant into a conservative CV/demo-ready full-stack/backend AI engineering project. The work must improve real API contract reliability, permission-first security evidence, business metrics visibility, synthetic RAG proof, and portfolio packaging without claiming production deployment, HIPAA compliance, real hospital users, or measured ROI.

## Boundary

This feature starts fresh as `portfolio-hardening-2026-06`. Do not resume the parked `kotaemon-chat-assistant-ui` handoff. Preserve the old handoff for later human UAT sign-off.

Current execution focuses on the smallest high-value slice:

- frontend/backend route drift for patients, documents, audit logs, settings, and metrics;
- memory-only frontend bearer token handling while keeping API URL persistence;
- backend settings and HMS sync permission guards with denial audit evidence;
- focused tests and scripts/docs proving the changed claims.

Broader RAG eval suites, screenshots, and complete portfolio case study can build on this slice if the repo gates stay green.

## Domain Types

- CALL: FastAPI routes and frontend API client contracts.
- SEE: dashboard, documents, audit, metrics, settings, and login surfaces.
- RUN: verification, UAT/evidence, and RAG evaluation scripts.
- READ: README, evidence sheet, and portfolio case-study documentation.

## Locked Decisions

- D1: Use synthetic or de-identified data only.
- D2: Keep local/dev bearer-token auth honest; do not implement full OIDC in this feature.
- D3: Bearer tokens must remain in React memory only. API URL may be persisted for developer ergonomics.
- D4: Settings reads are allowed for admin/security; settings writes are admin-only.
- D5: HMS sync writes require records/admin role plus patient upload scope where applicable; denied attempts must create audit events.
- D6: Portfolio claims must be backed by generated or checked artifacts.

## Tooling State

- Khuym onboarding is complete for plugin `3.0.8`.
- `gkg` is unavailable on PATH; use GitNexus MCP plus direct inspection fallback.
- GitNexus repository name is `chatbot-hospital-system`; pass this repo selector because multiple repos are indexed.

## Critical Patterns Applied

- Streaming/RAG endpoints must mirror safety contracts across transports.
- RAG evidence needs full join-chain authorization before any context reaches an LLM.
- Cited RAG answers need answer-usefulness assertions, not just citation validity.
- Raw SQL permission policies need executable tests.

