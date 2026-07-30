# Full AI Evaluation Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development task-by-task.

**Goal:** Deliver source-backed AI evaluation with reusable global skills and deterministic safety gates.

**Architecture:** Keep corpus provenance, benchmark contracts, metric computation, execution, and report rendering separate. Resolve source evidence at runtime; never derive expected truth from retrieved chunks or generated answers.

**Tech Stack:** Python 3.12, Pydantic v1, pytest, FastAPI service adapters, PowerShell, GitHub Actions.

## Global Constraints

- Use only synthetic/de-identified data.
- Preserve existing user dirty files and stage only branch-owned files.
- Public guideline/drug records are quarantined from patient retrieval.
- Safety failures are hard failures; live-model judging is optional and never silently substitutes a passing score.
- Use normal branch only; do not create a worktree.
- Review each task before the next task starts.

### Task 1: Global skill suite

Create the three skill packages under `.agents/skills`, an idempotent junction installer, and validation tests. Do not modify `C:\Users\NITRO\.codex\skills`.

### Task 2: Corpus contracts and manifests

Create Pydantic contracts and deterministic source inventory for 100 PDFs, 100 patient CSVs, 200 metadata records, plus quarantined public knowledge. Add hash, duplicate, and provenance tests.

### Task 3: Source-backed benchmark

Replace generated canonical-fact cases with 300 deterministic real-source cases and a 50-case review sentinel using source locators rather than chunk UUIDs. Add validation and reviewer-status gates.

### Task 4: Evaluation engine and OCR metrics

Add corpus, OCR/CSV, retrieval, graph, chat/citation, and gate runners; write JSONL/JSON/JUnit/Markdown reports; expose the specified CLI. Add reproducible scan fixtures without external data.

### Task 5: CI and truthful product claims

Replace pass-by-construction RAG tests, remove CI continue-on-error, add deterministic PR/full lanes, and correct stale README claims.

### Task 6: P0/P1 remediation and final verification

Run the release suite; fix only confirmed P0/P1 safety, PHI, OCR-loss, citation, or sync/SSE parity defects with tests. Perform final independent security/evaluation review.
