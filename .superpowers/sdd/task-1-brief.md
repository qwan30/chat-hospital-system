# Task 1 — Global skill suite

Create branch-owned reusable skills under `.agents/skills/`:

1. `ai-product-evaluation`: generic AI product evaluation lifecycle, baseline-first gates, deterministic versus live evaluation lanes, report integrity.
2. `ai-eval-dataset-governance`: corpus inventory, source hashing, provenance, duplicate policy, immutable ground truth, review status, and public/private boundaries.
3. `healthcare-rag-graph-ocr-evaluation`: healthcare-specific OCR, CSV, RAG, Graph RAG, citation, authorization, PHI, and sync/SSE evaluation gates.

Each package must contain `SKILL.md`, `agents/openai.yaml`, and only focused `references/` or `scripts/` needed to use it. Use `skill-creator` conventions: imperative instructions, concise trigger descriptions, no README/changelog.

Create a PowerShell installer in `.agents/skills/ai-product-evaluation/scripts/` that is idempotent and creates directory junctions from each tracked source package to these user-global destinations:

- `C:\Users\NITRO\.agents\skills\<skill>`
- `C:\Users\NITRO\.claude\skills\<skill>`
- `C:\Users\NITRO\.gemini\skills\<skill>`
- `C:\Users\NITRO\.gemini\antigravity\skills\<skill>`

Never modify `C:\Users\NITRO\.codex\skills`; Codex discovers the `.agents` global root.

Add tests or a dry-run validation that proves target validation, existing-compatible junction handling, and refusal to replace a non-junction directory. Validate each package using the bundled `quick_validate.py`.

Do not touch user-owned dirty files. Use test-first for new script behavior. Commit only Task 1 files. Write the detailed report to `.superpowers/sdd/task-1-report.md` and return status, commit SHA, test command/results, and concerns.
