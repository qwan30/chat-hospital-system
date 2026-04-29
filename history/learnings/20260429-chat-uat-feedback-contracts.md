---
date: 2026-04-29
feature: kotaemon-chat-assistant-ui
categories: [pattern, decision, failure]
severity: critical
tags: [uat, rag, permissions, frontend, testing, windows]
last_dream_consolidated_at: 2026-04-29T01:07:29+07:00
---

# Learning: Cited RAG Answers Need Answer-Usefulness Assertions

**Category:** failure
**Severity:** critical
**Tags:** [rag, uat, testing, hms]
**Applicable-when:** Implementing any RAG, cited-answer, stub LLM, or seeded acceptance path where the user asks for specific facts.

## What Happened

The HMS appointment path could retrieve and cite authorized appointment evidence, but manual end-user UAT found the assistant answer was still generic: it referred to "relevant clinical details" instead of stating the requested appointment status and vital signs. The backend tests in `app/backend/tests/test_hms_appointment_import.py` proved the citation metadata and source lineage, but they did not require the answer text to include the user-requested facts. The follow-up changed `app/backend/src/hospital_ai/services/chat.py` so the stub answer extracts `Status` and `Vital signs` from authorized evidence, then added regression assertions for `CHECKED_IN` and `Blood pressure 128/78`.

## Root Cause / Key Insight

Citation correctness is necessary but not sufficient for product readiness. A RAG answer can be safe and traceable while still failing the user's task if the answer text does not summarize the exact facts the user requested. Stub or local LLM paths are especially vulnerable because they can satisfy citation syntax without producing useful clinical or operational content.

## Recommendation for Future Work

For every seeded RAG acceptance question, assert both evidence fidelity and answer usefulness. Require the answer to contain the key requested fields from the cited evidence, not only a valid citation ID. Keep at least one end-user browser or API UAT scenario that asks for concrete facts and fails if the response is generic.

---

# Learning: Default Lists Need Lifecycle Filters At The Source Boundary

**Category:** pattern
**Severity:** standard
**Tags:** [api, frontend, lifecycle, testing]
**Applicable-when:** Listing persisted entities that have active, archived, soft-deleted, hidden, or draft states.

## What Happened

The archive action persisted `status=archived`, but archived conversations still appeared in the default active conversation list and could remain selected after refresh. The fix filtered active threads in `ChatThreadService.list_threads` and added a defensive active-status filter in `AssistantShell` before mapping backend summaries into UI state. `test_archived_threads_are_hidden_from_default_thread_list` now protects the API behavior.

## Root Cause / Key Insight

Archive was implemented as a state transition, but the default list contract never said "active only." The UI trusted the list endpoint as the active-workflow source, so a valid archived entity looked like an active conversation. Lifecycle semantics belong at the source boundary, with adapters adding defensive filtering only as a guardrail.

## Recommendation for Future Work

When adding archive, soft-delete, publish, or visibility state, define every list endpoint's default lifecycle filter at the same time. Add a regression test that performs the lifecycle transition and then lists the default collection. Keep UI adapters defensive, but do not rely on frontend-only filtering as the source of truth.

---

# Learning: Permission Boundary Copy Must Be State-Driven

**Category:** failure
**Severity:** standard
**Tags:** [permissions, frontend, ux, phi]
**Applicable-when:** Rendering patient-linked evidence, citations, warnings, or access-state panels in a clinical or PHI-adjacent interface.

## What Happened

The evidence panel always rendered a red "Patient-linked evidence remains unavailable" warning, even when the active context had backend-allowed patient permission and HMS evidence was visible. Automated checks covered blocked and allowed patient states in `PatientContextGate`, but the source panel had static warning copy. The fix added `permissionBoundaryFor` in `EvidencePanel` so general, allowed, pending, denied, and empty states render different copy and styling.

## Root Cause / Key Insight

Permission messaging is part of the security UX contract. Static warning copy can become false as soon as evidence and permission state become live, and contradictory copy erodes trust in the evidence panel. Permission-sensitive UI needs state-derived text just like request readiness does.

## Recommendation for Future Work

When a screen shows patient-linked evidence, derive warning, allowed, pending, and denied copy from the same permission state used for backend request readiness. Add a lightweight UI contract test for each permission copy path, and include at least one browser UAT screenshot for an allowed patient context with evidence visible.

---

# Learning: Product UAT Evidence Should Be A Durable Repo Artifact

**Category:** decision
**Severity:** standard
**Tags:** [uat, review, evidence, process]
**Applicable-when:** Closing a feature where correctness depends on role behavior, browser behavior, screenshots, or cross-service API scenarios.

## What Happened

The review wave created `app/backend/scripts/uat_product_api_check.py`, API evidence JSON, browser screenshots, and `history/kotaemon-chat-assistant-ui/uat-product-test-report.md`. That made the later `fix` instruction precise: the four P2 issues were already classified with evidence, expected behavior, and target reruns. The artifacts also made it easy to update Khuym state after the fixes without relying on chat memory.

## Root Cause / Key Insight

Manual product feedback decays quickly if it lives only in conversation. Screenshots, API traces, and a severity table turn subjective UAT into a stable contract that can be fixed and rechecked. This is especially useful when a feature spans backend permissions, frontend state, browser CORS, and generated answer content.

## Recommendation for Future Work

For feature review waves, write a UAT report and evidence folder before starting fixes. Include role, action, expected result, actual result, severity, screenshot/API artifact, and rerun result. Keep the report in `history/<feature>/` so future agents can resume from evidence instead of reconstructing defects from transcript fragments.

---

# Learning: Windows Verification Needs Command-Aware Fallbacks

**Category:** failure
**Severity:** standard
**Tags:** [windows, verification, tooling]
**Applicable-when:** Running Python or Node verification in this Windows workspace, especially under sandboxed or restricted PowerShell sessions.

## What Happened

Verification hit environment-specific failures that were not code defects. PowerShell blocked `npm.ps1`, so frontend checks needed `npm.cmd`. `next build` compiled successfully but failed with `spawn EPERM` until rerun outside the sandbox. `python -m compileall` hit permission errors writing existing `__pycache__` files, but passed when `PYTHONPYCACHEPREFIX` pointed at a temporary local cache directory.

## Root Cause / Key Insight

Windows command wrappers, process-spawn policy, and Python bytecode cache writes can fail independently of source correctness. Treating these as product failures wastes time and can lead to unnecessary code edits. Verification commands need environment-aware fallbacks that preserve the same behavioral check.

## Recommendation for Future Work

On this Windows workspace, prefer `npm.cmd` over `npm` in PowerShell. If `next build` fails after compilation with `EPERM`, rerun in an environment that permits worker spawn before changing source. If `compileall` cannot write existing pycache files, set `PYTHONPYCACHEPREFIX` to a temporary directory inside the workspace and delete it after the check.
