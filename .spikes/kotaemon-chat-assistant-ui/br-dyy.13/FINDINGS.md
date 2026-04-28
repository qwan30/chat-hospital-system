# Spike Findings: br-dyy.13

**Question:** Can shared-thread affordances stay honest without backend persistence?

**Result:** YES

## Evidence

- The Phase 1 contract explicitly separates visible shared-thread affordances from real persistence.
- Current backend discovery found no conversation/thread model beyond individual `AiQuery` records.
- The UI can safely show local/sample conversations if the provenance is visible and controls do not claim cross-user persistence.
- Phase 2 is already dedicated to making shared chat threads real and safe.

## Constraints For Beads

- Conversation sidebar can show local/sample thread states and share/rename/delete affordances.
- UI copy must not say the thread is truly shared or persisted until backend APIs exist.
- Any patient-linked sample evidence must remain synthetic and marked local/mock.
- Real shared-thread storage, audit behavior, and access checks remain Phase 2.

## Impact

Phase 1 can include shared-thread affordances as UI contract work. Beads must preserve explicit mock/local labels and avoid implementing backend persistence in this phase.
