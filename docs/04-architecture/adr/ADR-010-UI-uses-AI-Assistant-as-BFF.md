# ADR-010: UI uses AI Assistant as a BFF

## Metadata
- **ID:** ADR-010
- **Status:** Accepted
- **Decided by:** System Architect / Tech Lead
- **Date:** 2026-06-07
- **Last Updated:** 2026-06-07

## Context
Exposing the frontend application directly to both the HMS API and the Chatbot API requires the TanStack Start UI to orchestrate complex multi-service requests (e.g. checking permissions, querying patient details, generating summaries, and writing logs). This increases UI code complexity and network latency.

## Decision
We chose the AI Assistant FastAPI backend to act as a unified **Backend-For-Frontend (BFF)** layer. The TanStack Start UI communicates exclusively with the BFF. The BFF performs all backend orchestration, queries HMS APIs, reads pgvector, and consolidates payloads.

## Consequences
- **Pros:**
  - Standardizes the API request contract for the TanStack Start UI.
  - Simplifies the UI client state management and security token handling.
  - Improves API latency by routing orchestration inside the local network.
- **Cons:**
  - FastAPI backend must serve duplicate endpoints (e.g. proxying search queries) and maintain mapping contracts for underlying HMS structures.
