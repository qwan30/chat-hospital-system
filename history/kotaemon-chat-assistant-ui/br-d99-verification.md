# br-d99 Verification

**Bead:** br-d99
**Title:** Resolve Review P2: Make composer submit path explicit and safe
**Date:** 2026-04-28

## Result

PASS. The chat composer now has one controlled submit path for Enter and the send button, and that path validates backend readiness before preparing a patient chat request.

## What Changed

- Converted `ChatComposer` to a controlled input with local empty-question rejection.
- Added native form `onSubmit` handling with `event.preventDefault()`.
- Changed the send button to `type="submit"` so button and keyboard activation share the same path.
- Added disabled/loading-ready props and an `aria-live` status line for blocked, ready, and error feedback.
- Wired `AssistantShell` to call `prepareVerifiedBackendChatRequest` and store either a blocked reason or backend-ready request shape.
- Extended `npm run test:workspace` to guard the composer submit contract and readiness states.

## Verification

| Check | Result |
|---|---|
| `npm.cmd run test:workspace` | Passed, 14/14 checks. |
| `npm.cmd run typecheck` | Passed. |
| `npm.cmd run lint` | Passed. |
| `npm.cmd run build` | Passed. |
| Playwright on `http://localhost:3015/` | Passed: empty submit shows local rejection, Enter submit on general/pending/denied scopes shows blocked backend reasons, allowed patient scope plus send button shows backend-ready status, console errors 0. |

## Acceptance Criteria

- [x] Enter key and send button follow the same submit path.
- [x] Native form reload is prevented.
- [x] Empty or whitespace-only questions are blocked.
- [x] General/documented-gap and pending/denied patient states show clear blocked reasons.
- [x] Allowed patient context creates a backend-ready request shape only after validation.
- [x] Component/integration checks cover keyboard submit, button activation, disabled/loading state, blocked readiness reasons, success shape, and rejected submit/error state.
