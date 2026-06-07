# BR-001: Patient Question with Cited Answer

## Metadata
- **ID:** BR-001
- **Status:** approved
- **Owner:** Product Owner
- **Stakeholders:** Doctor, Nurse, QA Lead
- **Priority:** Must
- **Target Quarter:** MVP

## Background
Hospital staff frequently need to look up patient-specific information across structured records, documents, and historical notes. Manual lookup takes 10–15 minutes per query. Staff need a fast, reliable way to ask natural language questions and receive answers backed by verifiable sources.

## Goal
Authorized users can ask patient-related questions and receive AI-generated answers with citations to source documents, tables, pages, or chunks.

## Success Metrics
- Answer includes source document/table/page/chunk citation: ≥95% of answers when evidence exists
- Response latency: <30 sec on MVP dataset
- Safe refusal rate when no evidence: ≥90%

## In Scope
- Natural language question input with patient context
- RAG-based retrieval from structured data and vector chunks
- Citation metadata preservation through retrieval and generation
- Safe refusal when evidence is insufficient
- Streaming answer delivery

## Out of Scope
- Replacing clinical judgment with AI output
- Cross-patient queries (each query is scoped to one patient)
- General medical knowledge not tied to patient records

## Related Use Cases
- UC-001: Ask Patient Question
- UC-005: View Citations/Source Page

## Constraints
- **Technical:** Must run on 16GB RAM with quantized LLM
- **Privacy:** Patient data never sent to external LLM
- **Regulatory:** AI output is assistive only; clinical staff verify decisions

## Open Questions
- [ ] What is the minimum citation quality for MVP acceptance?
- [ ] Should general hospital knowledge questions (no patient context) be supported in MVP?

## History
- v1 (2026-04-27, Original): Initial draft in flat BRD
- v2 (2026-06-07, Agent): Extracted to individual BR file with expanded metrics
