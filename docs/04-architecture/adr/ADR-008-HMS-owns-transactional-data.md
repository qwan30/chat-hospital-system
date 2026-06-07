# ADR-008: HMS owns transactional hospital data

## Metadata
- **ID:** ADR-008
- **Status:** Accepted
- **Decided by:** System Architect / Tech Lead
- **Date:** 2026-06-07
- **Last Updated:** 2026-06-07

## Context
When integrating the AI Copilot assistant, we must define which system owns transactional hospital records (patient demography, medical history, vital signs, lab reports, role catalogs, and access policies) to avoid synchronization loops and data drift.

## Decision
We chose the Hospital Management System (HMS) as the single source of truth and absolute owner of all transactional clinical data. The AI Assistant backend is strictly read-only regarding HMS transactional tables.

## Consequences
- **Pros:**
  - Prevents data inconsistency across systems.
  - Keeps hospital data governance and security rules unified in the HMS.
  - Simplifies the AI Assistant datastore structure.
- **Cons:**
  - Requires the AI Assistant to query HMS APIs to retrieve EMR details or verify patient listings, introducing dependency on HMS API uptime.
