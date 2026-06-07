# ADR-007: Track time saved and cost saved

## Metadata
- **ID:** ADR-007
- **Status:** Accepted
- **Decided by:** System Architect / Tech Lead
- **Date:** 2026-04-27
- **Last Updated:** 2026-06-07

## Context
Deploying an AI assistant in a hospital environment requires justifying the return on investment (ROI) to sponsors. Hospital managers need objective metrics on clinician productivity gains (e.g., hours saved per week reviewing patient histories) and operational cost reductions.

## Decision
We chose to design and implement a built-in metrics and analytics engine that automatically tracks query execution times and calculates estimated clinician time and cost savings against standard manual review baselines.

## Alternatives Considered
- **External Surveys:** Asking doctors how much time they think they saved. While useful, surveys are subjective, intermittent, and lack quantitative logging.
- **Deferring Metrics Dashboard:** Delaying metrics until post-launch. Rejected because immediate feedback on time saved is critical to secure funding for Phase 2 (Neo4j and advanced RAG features).

## Consequences
- **Pros:**
  - Provides administrators with real-time, dashboard-visualized ROI proof.
  - Automatically captures productivity statistics without requiring extra inputs from clinicians.
  - Motivates staff by showing their collective hours saved on administrative work.
- **Cons:**
  - Requires defining and storing baseline metrics (e.g., average manual search times) which are estimates rather than absolute values.
  - Introduces minor overhead to log metric events into the Postgres analytics datastore on each chat query and summary generation.
