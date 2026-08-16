# Product

## Register

product

## Users

Hospital staff working inside a single institution's knowledge assistant:

- **Medical records technicians / OCR reviewers** correcting extracted clinical text (lab panels, discharge summaries) against scanned document pages, page by page, revision by revision.
- **Clinicians and nurses** asking permission-scoped questions about protocols, patients, and lab results under time pressure.
- **Reviewers/approvers** validating a corrected revision before it is indexed for retrieval.
- **Admins and security auditors** verifying permissions and audit trails.

They work in dense, task-focused sessions; accuracy and traceability outrank aesthetics on every screen.

## Product Purpose

An AI-powered hospital knowledge assistant: ingests clinical documents (OCR), lets staff correct and approve revisions with full audit history, and serves permission-filtered RAG answers with citations. Success = a reviewer can trust that what the system retrieved and displayed is exactly what was approved — zero unauthorized chunks reaching the LLM, every correction visible and attributable.

## Brand Personality

Precise, calm, trustworthy. Clinical-tool energy: quiet chrome, loud signal. Three words: **exact, accountable, unhurried**.

## Anti-references

- Consumer chat-app bling: bouncing avatars, gradient message bubbles, typewriter flourishes on clinical data.
- Marketing-page scaffolding (hero metrics, eyebrow-everything) leaking into app surfaces.
- Modal-first flows for work that belongs inline in the document workspace.
- Decorative motion that does not convey state.

## Design Principles

1. **Safety over speed.** Dangerous values (lab numbers, drug names, dosages) must be visually loud; ambiguity is a defect.
2. **Trust through evidence.** Confidence scores, citations, revision lineage, and diffs are always visible where the data is shown.
3. **The tool disappears into the task.** Density is a feature; every pixel serves the correction or the question being answered.
4. **Consistency is a virtue.** Same button, badge, and status vocabulary screen to screen.

## Accessibility & Inclusion

WCAG 2.1 AA target; axe-core runs in Playwright e2e. Body text ≥4.5:1 contrast in both themes, keyboard paths for every workspace action, `prefers-reduced-motion` respected (crossfade/instant alternatives). Color is never the only signal — diff states pair color with +/− text markers.
