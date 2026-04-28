---
date: 2026-04-28
feature: kotaemon-chat-assistant-ui
categories: [pattern]
severity: standard
tags: [frontend, chat, state, shared-threads, react, permissions]
last_dream_consolidated_at: 2026-04-28T15:35:44+07:00
---

# Learning: Shared Chat Workspaces Need One Active State Model

**Category:** pattern
**Severity:** standard
**Tags:** [frontend, chat, state, shared-threads, react, permissions]
**Applicable-when:** A chat UI has thread selection, patient context, transcript, evidence, composer readiness, or sharing indicators that should change together.

## What Happened

Phase 1 initially made the chat workspace look connected, but separate regions still owned or read separate active state. The sidebar could choose a thread while the transcript, patient context gate, evidence panel, and composer were still tied to sample state or local component state. Review captured this as a P2 because the UI could imply a shared active thread while showing evidence and patient scope from a different thread.

The follow-up centralized the active workspace model in `AssistantShell`. Child components now receive explicit props for the active thread, active patient context, and derived evidence instead of reading `sampleWorkspaceState` directly. A workspace wiring check now fails if disconnected state ownership is reintroduced.

## Root Cause / Key Insight

Collaborative chat is not only a layout problem. Once a screen combines shared threads, patient-linked context, evidence panels, and composer readiness, "active thread" becomes a product invariant. If regions compute it independently, the app can display a believable but wrong conversation state.

## Recommendation for Future Work

Keep one parent-owned active workspace model before adding persistence or backend thread APIs. Thread selection should update the transcript, patient context gate, evidence panel, composer scope label, and sharing controls from the same state. Add a lightweight integration test that changes the active thread and verifies every dependent region updates together.
