# ADR-006: Require citations for clinical answers

## Metadata
- **ID:** ADR-006
- **Status:** Accepted
- **Decided by:** System Architect / Tech Lead
- **Date:** 2026-04-27
- **Last Updated:** 2026-06-07

## Context
When doctors and nurses use the AI assistant to retrieve information about a patient, they make high-stakes clinical decisions (e.g., prescribing medications, checking for allergies). Hallucinations or incorrect answers from the AI without evidence are unacceptable in a clinical environment. Clinicians must be able to instantly check the source document, page, or database row where the AI retrieved its facts.

## Decision
We enforce a strict design rule: every clinical answer returned by the system must include precise source citations (e.g., document name, page number, or database record timestamp). If the local LLM cannot find sufficient evidence in the retrieved context to answer a query, it must issue a safe refusal instead of guessing.

## Alternatives Considered
- **Standard Chatbot Responses (No citations):** Excluded as it creates severe medical liability risks and fails to build trust with clinical staff.
- **Providing Raw Documents Only:** Doctors would have to read whole PDFs themselves, negating the productivity benefit of having an AI assistant.

## Consequences
- **Pros:**
  - Builds clinician trust and ensures medical safety by enabling quick manual verification.
  - Reduces the risk of hallucinations since the LLM is instructed to only use the provided context.
  - Align with healthcare compliance guidelines.
- **Cons:**
  - Slightly increases response latency due to the extra step of parsing, formatting, and rendering citation components in the UI.
  - Requires strict system prompt design to ensure the model does not generate claims without citations.
