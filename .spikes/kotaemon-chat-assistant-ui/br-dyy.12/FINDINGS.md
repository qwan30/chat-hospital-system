# Spike Findings: br-dyy.12

**Question:** Can Kotaemon chat UI translate to the current React/Next shell without Gradio?

**Result:** YES

## Evidence

- Kotaemon's relevant Phase 1 behavior is structural: conversation control panel, central chat area, prompt composer, citation/source interactions, and right-side info panel.
- The local Kotaemon implementation is Python/Gradio, so direct code import is not practical.
- The current frontend already has Next.js, React, Tailwind, shadcn-style primitives, and Lucide. Those are enough for a React rebuild of the Phase 1 workspace.
- Direct reuse should be limited to concepts, spacing/layout references, CSS ideas, and compatible static assets such as icons after checking format/licensing.

## Constraints For Beads

- Do not embed Gradio or copy Python UI code.
- Translate only the Phase 1 workspace: sidebar, transcript, composer, citations, evidence panel.
- Defer Kotaemon knowledge-base management, upload/indexing, settings, and admin surfaces.

## Impact

Phase 1 can proceed with a React/Tailwind implementation. The relevant beads should continue to say "translate" or "model after" Kotaemon rather than "copy frontend code directly."
