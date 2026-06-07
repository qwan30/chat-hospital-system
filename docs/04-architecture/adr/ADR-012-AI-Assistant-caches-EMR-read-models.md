# ADR-012: AI Assistant caches EMR read models

## Metadata
- **ID:** ADR-012
- **Status:** Accepted
- **Decided by:** System Architect / Tech Lead
- **Date:** 2026-06-07
- **Last Updated:** 2026-06-07

## Context
Querying the live EMR backend database for patient summaries and vector generation on every chatbot query places heavy network loads on the main hospital production databases, potentially degrading clinical system responsiveness.

## Decision
We chose to implement a **change-feed sync pipeline**. The AI Assistant caches de-identified read models of HMS patient records, encounter logs, and lab results. These cached models are updated incrementally via HMS change feed APIs (`/ai/changes`) or scheduled background batch workers.

## Consequences
- **Pros:**
  - Isolates AI query workloads from transactional medical systems.
  - Improves response times by enabling fast local pgvector joins on cached EMR tables.
- **Cons:**
  - Introduces minor data latency (up to 15 minutes sync cycle). Clinicians must be informed of the sync freshness via UI metadata timestamps.
