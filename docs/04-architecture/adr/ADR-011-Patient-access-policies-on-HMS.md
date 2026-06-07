# ADR-011: Patient access policies source of truth resides on HMS

## Metadata
- **ID:** ADR-011
- **Status:** Accepted
- **Decided by:** System Architect / Tech Lead
- **Date:** 2026-06-07
- **Last Updated:** 2026-06-07

## Context
Patient access controls and HIPAA security rules are highly critical. Deciding whether a user has permission to view a patient's records or justify emergency overrides requires evaluating clinical relationship status. Maintaining access rules in multiple databases risks severe security policy mismatches.

## Decision
We enforce that the **HMS is the single source of truth for patient-user permissions**. Before the RAG engine retrieves clinical facts or documents, the AI Assistant calls the HMS permission validation endpoint (`/ai/patients/{id}/permissions`) to confirm scope.

## Consequences
- **Pros:**
  - Guarantees strict compliance with hospital security directives.
  - Revoking a clinician's permission on the EMR immediately propagates to the AI Copilot.
- **Cons:**
  - Every clinical search query requires a synchronous network round-trip to the HMS permission check API, introducing latency overhead.
