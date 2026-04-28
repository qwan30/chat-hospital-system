---
date: 2026-04-28
feature: kotaemon-chat-assistant-ui
categories: [failure]
severity: standard
tags: [frontend, citations, evidence, permissions, phi, rag]
last_dream_consolidated_at: 2026-04-28T15:35:44+07:00
---

# Learning: Citation UI Must Preserve Evidence Fidelity

**Category:** failure
**Severity:** standard
**Tags:** [frontend, citations, evidence, permissions, phi, rag]
**Applicable-when:** A frontend maps backend RAG citations into chips, source panels, evidence drawers, or answer annotations.

## What Happened

The backend chat contract carried evidence detail such as document ID, page, chunk ID, score, content excerpt, and metadata, but the first UI adapter thinned that response into display-oriented citation fields. The evidence panel still depended on sample data, so citation chips and evidence inspection could drift apart.

Review kept this at P2 because Phase 1 was still sample-heavy and no direct security leak was found. The follow-up added a backend-response artifact model that returns both the assistant message and matching evidence sources from the same response. The adapter now preserves backend evidence fields and links each citation to an evidence source generated from the same backend payload.

## Root Cause / Key Insight

Citation rendering is part of the evidence boundary, not just visual decoration. If the frontend drops document, page, chunk, score, content, metadata, or permission-state details, users can no longer inspect what the answer was grounded on, and later permission-aware evidence wiring has less data to enforce or explain safe behavior.

## Recommendation for Future Work

Keep citation chips and evidence panels fed by the same backend response mapping. Do not collapse evidence into labels until after the inspectable source model has preserved document identity, page or chunk identity, score, excerpt, metadata, and permission state. Add adapter tests that prove citation IDs resolve to evidence sources from the same response and that patient-linked evidence remains visibly gated until permission allows it.
