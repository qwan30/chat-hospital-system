# Approach — Codebase Audit 2026-05

_Populated during Phase 2 (`khuym:planning`) after discovery._

## Review Tracks

| Track | Lead concern | Severity escalation triggers |
|---|---|---|
| Security | Auth, PHI leakage, permissions, secrets | Any unauthorized chunk reaching LLM = P1 |
| Bugs & edge cases | Null paths, aborts, error swallowing | Crash or data corruption = P1 |
| Structure | Dead code, circular deps, layering | Circular dep in core flow = P2 |
| RAG / clinical safety | Retrieval fidelity, citation integrity | Citation points to non-existent evidence = P1 |
| Testing gaps | Missing permission / leakage tests | Zero coverage on permission branch = P1 |

## Finding Template

```
### [TRACK-###] title
- Severity: P1 | P2 | P3
- Symbols: `module.symbol` (+ `gitnexus_context` link)
- Impact (`gitnexus_impact` direction=upstream): d=1 / d=2 / d=3 summary, risk level
- Evidence: file:line or spike ref
- Proposed fix: minimal upstream change description
- Regression test: path + behavior name
```

## Execution Rules

1. `gitnexus_impact` before every edit — record output in bead.
2. Regression test written **before** fix for P1 security/RAG findings.
3. `gitnexus_detect_changes({scope:"staged"})` before every commit.
4. HIGH/CRITICAL risk → stop and confirm with user before proceeding.
5. Minimal upstream fix preferred over downstream workaround.

## Findings

(empty — to be filled)
