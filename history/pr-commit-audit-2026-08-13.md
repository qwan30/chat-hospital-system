# PR and commit audit — 2026-08-13

## Scope and evidence boundary

This audit compares the live GitHub PR state and recent `main` commits with the
local checkout. Remote state was queried on 2026-08-13 for
`qwan30/chat-hospital-system`; the authoritative source snapshot is
`main@467dbc3259c8f0ccb79162e7f097ef0ffb6112f4`.

The local checkout already contained unrelated dirty screenshots, temporary CI
directories, synthetic browser fixtures, and a documentation plan. Those files
were preserved. The audit changed only `README.md` and this history record.

## Mainline finding

The first-parent history of `main` contains PR #90 (`eaf8c9b`) followed by PR
#104 (`467dbc3`). GitHub reports PRs #91–#103 as `MERGED`, but none of their
reported merge SHAs is an ancestor of `main`.

| PR | GitHub state | Head SHA | Reported merge SHA | Ancestor of `main`? | Scope |
|---:|---|---|---|---|---|
| #90 | MERGED | `d5e56d02c613464e092ef0684827256348f855a6` | `eaf8c9b79855f276d7e02d0f379a3998d47e12e5` | Yes | CDI V2 lineage, immutable upload/revision foundation, capabilities, idempotency |
| #91 | MERGED | `b73762f36408af111345c95c8004e834a057845c` | `fa8069ebf8b0f2f6502d570cf724f4b838ab0e87` | No | OCR extraction and index generations |
| #92 | MERGED | `b9ddab00eb1dab043cfb14e582fb90eab21b8c58` | `96daa7003f1293af25f5d7b2fccd76fcf877e122` | No | Active-generation retrieval, graph/timeline filters, claim validation |
| #93 | MERGED | `86f07ba4ecee68304569dc8afe936ea1be7de41d` | `4c04e22a8f020a28825b7b19b9e07fcec10fc115` | No | Validated SSE persistence and interruption state |
| #94 | MERGED | `5407963d9351971c29916528def9b82907ef5b7b` | `384187c081f8fe5fb22c9c336529c21d5f3375c3` | No | Immutable upload and OCR review workspace |
| #95 | MERGED | `c4830cd7c946bef7c91aa4d365978f47654584c0` | `d96c08a89e8a6f4d3a7a498e119c3f02e7a245d7` | No | Graph, timeline, chat, citation, and evidence provenance UI |
| #96 | MERGED | `fa1a4033c8e741ffe233dfcb47c6306de77763ab` | `e3f5a832fc30689475bbeed851407903991ea8db` | No | Corpus V3, evaluation adapters, release evidence, normative gates |
| #97 | MERGED | `cc2be61a1d20e66c8d763cf6f36c6514504ef0a2` | `697c6f066b59f316b5f95cc69507b5ef67c00edc` | No | Backend quality, migration, authorization, finalization, and OCR hardening |
| #98 | MERGED | `29191683fa64c38acb8d6fc3125b5f49400cfb5d` | `0ce7df386967cd00b738768d943c1a313459c18a` | No | Atomic generation activation, backfill parity, active evidence, authorized claims |
| #99 | MERGED | `a314a52d790986035f7e9095e990f4a4661eff5e` | `6ed79e6eb8a64005ea83f7d0deb604dc89eef617` | No | Migration and test hardening |
| #100 | MERGED | `34df06c36ea5c5415604e1d0735af6027e30eb85` | `fa7ab1b9bc5e1d13909b49c1c3b9cc4af2f5f71c` | No | Cross-path active evidence scope |
| #101 | MERGED | `952a89465a12d4d86e53d50c4d8d071e3f6ebbf4` | `e9d6cae342dbafa7a65c5197759488b38ea91ca1` | No | Artifact-backed evaluation and release hardening |
| #102 | MERGED | `40a6ea48dbfa8162948ae55c9fc076e346e0644d` | `a2c75df8d66d17f5b9707285a9bc70d5e44f40df` | No | Authenticated browser integration and CI/runtime hardening |
| #103 | MERGED | `292329b52d6581005ed01f94d85113144726b734` | `adb6cda62babd429b0dd4ba32dd905605fec4f6b` | No | Final browser, SSE, pgvector, and draft payload contracts |
| #104 | MERGED | `715430ecdaf8724a87299408d1a4fcb5d798f160` | `467dbc3259c8f0ccb79162e7f097ef0ffb6112f4` | Yes | Full-project E2E regression fixes and HMS path hardening |

The tree check matches the ancestry check: `main` contains
`document_revisions.py`, `document_uploads.py`, and
`cdi_v2_0001_add_revision_generation_schema.py`, but does not contain the
follow-on `document_generations.py`, `services/generations.py`,
`services/evidence_scope.py`, or the later document-workspace components. The
README therefore describes the CDI V2 foundation as present and the rest as an
unreconciled delivery gap.

## Recent `main` commits

PR #104 landed these recent behavior fixes on `main`: seed documents now use
ready status; streamed citations retain chunk IDs; patient overview fallback
counts match tabs; real-auth session identity and sign-out are tested; document
search uses explicit scope; browser HL7/DOCX uploads are normalized and cleaned
safely; nested document routes render; chat history has a semantic empty state;
timeline/citation E2E contracts are aligned; and dynamic HMS path segments are
allowlisted and validated in a CodeQL-visible safe branch.

The relevant tip sequence is:

```text
467dbc3  Merge pull request #104
715430e  fix(security): expose safe HMS path branch to CodeQL
6354728  fix(security): make HMS path validation CodeQL-safe
3a96740  fix(security): constrain HMS request paths
80fe285  test(e2e): correct timeline and citation contracts
a1177d5  fix(chat): use semantic history empty state
cd3c535  fix(documents): render nested document workflows
5757014  style: format chat citation contract
49182ce  test: cover DOCX ingestion safety guards
fd71089  fix: harden DOCX ingestion cleanup
8f1f86a  fix: complete HL7 and DOCX ingestion
40d946b  fix: accept browser HL7 and DOCX uploads
af444c7  test: cover document search URL transitions
35d155d  fix: bind document search to explicit scope
3fb364a  fix: align document UI readiness and search scope
e3fe5d2  test: isolate real auth provider integration
ee89712  fix: verify real auth session sign-out
9995581  fix: harden real auth session identity
36c5350  fix: align session identity and sign-out
2267fe3  fix: align patient overview fallback counts with tabs
1d5d53a  fix(chat): persist stream citation chunk ids
c678763  fix: align seed scripts with ready document status
eaf8c9b  feat(cdi): add V2 foundation and document lifecycle (#90)
```

## Current remote PR queue

The 13 open PRs are Dependabot updates only: #6, #12–#21, #32, and #33.
They cover FastAPI, NumPy, setuptools, Zod, react-day-picker, Vite React,
ESLint, eslint-plugin-react-hooks, paths-filter, Docker login/metadata,
actions/cache, and Slack action upgrades. They were not treated as product
features or merged delivery.

PR #89 is closed and should not be used as evidence that the stacked CDI V2
follow-ons are on `main`; PR #87 is also closed as a draft specification.

## Exact-SHA CI snapshot

For `main@467dbc3`, GitHub Actions run
[31666780395](https://github.com/qwan30/chat-hospital-system/actions/runs/31666780395)
on 2026-08-13 reported:

- Passed: changed-path detection, observability config, CodeQL backend and
  frontend, backend lint/tests/contracts, migrations, and frontend
  lint/tests/build/E2E.
- Failed: source-backed AI evaluation, with repeated NLP extraction errors and
  no deterministic summary artifact; Docker image build/scan/push also failed
  in the build/Trivy lane.
- Skipped: live-model AI evaluation.

This is a conditional/NO-GO release snapshot. PR #104's own validation was
stronger but separate: 670 backend tests passed with 3 skipped, 130 frontend
unit tests passed, and its isolated Chromium run recorded 150 passed and 1
skipped. Those numbers do not certify deployment or resolve the missing
stacked-PR ancestry.

## Documentation changes made

`README.md` now reflects the actual `main` tree: the CDI V2 foundation versus
the unlanded follow-ons, the 670-test/15-spec evidence, the 8082 dev port,
the current CI failures, and the improved HL7/DOCX and session/citation
descriptions. It intentionally avoids claiming generation activation,
cross-path active evidence, or the later CDI evidence UI as shipped on
`main`.

## Links

- [Pull requests](https://github.com/qwan30/chat-hospital-system/pulls)
- [Current main commits](https://github.com/qwan30/chat-hospital-system/commits/main)
- [PR #90](https://github.com/qwan30/chat-hospital-system/pull/90)
- [PR #104](https://github.com/qwan30/chat-hospital-system/pull/104)
- [Exact-SHA CI run](https://github.com/qwan30/chat-hospital-system/actions/runs/31666780395)
