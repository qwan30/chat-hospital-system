---
date: 2026-04-28
feature: kotaemon-chat-assistant-ui
categories: [pattern]
severity: standard
tags: [testing, contracts, frontend, backend-adapter, permissions]
last_dream_consolidated_at: 2026-04-28T15:35:44+07:00
---

# Learning: Patient Chat Adapters Need Executable Contract Tests

**Category:** pattern
**Severity:** standard
**Tags:** [testing, contracts, frontend, backend-adapter, permissions]
**Applicable-when:** A frontend prepares patient-scoped chat requests or maps backend chat responses before live integration is complete.

## What Happened

The first request helper could allow weak input shapes, including whitespace-only questions and unsafe retrieval counts, before a patient-scoped backend request was marked ready. Composer submission also had separate interaction paths until review follow-ups made Enter and button activation share the same submit flow.

The fixes trimmed questions, rejected empty input, constrained `topK` to an integer from 1 through 20, preserved patient-permission guards, and added workspace tests for request readiness, composer submit behavior, citation mapping, disclaimer preservation, and confidence fallback.

## Root Cause / Key Insight

Types describe the intended contract, but they do not prove that UI actions prepare safe backend calls. Small adapter bugs become harder to unwind once patient scope, permission state, citations, evidence panels, and composer feedback are all wired on top.

## Recommendation for Future Work

Before building more chat UI on top of patient-scoped adapters, add executable tests for blocked and ready request states. Cover blank questions, whitespace normalization, invalid retrieval counts, pending or denied patient permissions, missing patient IDs, ready payload defaults, backend citation mapping, disclaimer preservation, unknown confidence fallback, and shared keyboard/button submission behavior.
