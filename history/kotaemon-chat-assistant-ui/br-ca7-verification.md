# br-ca7 Verification

**Bead:** br-ca7
**Title:** Resolve Review P2: Preserve backend citation evidence details for source panel
**Date:** 2026-04-28

## Result

PASS. Backend chat citation mapping now preserves evidence detail for a source panel model instead of thinning citations into display-only chips.

## What Changed

- Added `BackendChatArtifacts`, which returns both an `AssistantMessage` and matching `EvidenceSource[]` from one backend response.
- Kept backend snake_case field names isolated in `api.ts`.
- Added `mapBackendCitationToEvidenceSource` to preserve document ID, document title, page, chunk ID, score, content excerpt, and metadata.
- Updated citation mapping so each citation `evidenceSourceId` points to an evidence source generated from the same backend response.
- Relaxed `EvidenceSource.metadata` to `Record<string, unknown>` so backend metadata is not dropped or lossy-cast before source-panel use.
- Extended `npm run test:workspace` to guard the backend response to message-plus-evidence adapter contract.

## Verification

| Check | Result |
|---|---|
| `npm.cmd run test:workspace` | Passed, 10/10 checks. |
| `npm.cmd run typecheck` | Passed. |
| `npm.cmd run lint` | Passed. |
| `npm.cmd run build` | Passed. |

## Acceptance Criteria

- [x] A mapped backend response can render citation chips and provide a matching evidence panel model without `sampleEvidenceSources`.
- [x] Citation `evidenceSourceId` points to an evidence source generated from the same backend response.
- [x] Page, chunk ID, score, content, document IDs, and metadata remain available in the UI model.
- [x] Backend naming stays isolated in the adapter layer, not presentation components.
