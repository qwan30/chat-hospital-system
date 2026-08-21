# Project Rules

These project-local reminders are loaded by `.codex/hooks/session_start.py` and support the repository `AGENTS.md` instructions.

## Privacy and Safety

- Use synthetic or de-identified hospital data only.
- Do not paste, generate, commit, or log real patient identifiers, raw PHI, secrets, API keys, private keys, or production credentials.
- Permission filters must run before retrieval context reaches any LLM or summarization step.
- Tests that touch RAG, OCR, patient scope, role scope, or citation behavior should prioritize leakage prevention.

## Frontend Workflow

- Frontend work lives in `app/frontend`.
- Prefer `npm run typecheck`, `npm run lint`, and `npm run build` from `app/frontend` for validation.
- Keep shadcn-style primitives in `app/frontend/src/components/ui`; compose feature components outside that folder.

## Documentation Workflow

- Preserve numeric doc prefixes in `docs/`.
- New docs use lowercase filenames with underscores.
- Link changes back to the relevant requirement or test case from `docs/` when practical.

## Deterministic Quality Gates (Zero-Tolerance)

- Before finishing any task, run `python app/backend/scripts/verify_deterministic_gates.py` and ensure Exit Code 0.
- All core functions must maintain CRAP Score <= 35 and 100% Mutation Kill Rate on domain logic.
- Frontend must pass `bun run typecheck`, `bun run lint`, and `bun run test`.

