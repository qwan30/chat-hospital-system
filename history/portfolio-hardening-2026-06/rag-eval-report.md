# Synthetic RAG Eval Report

This report uses synthetic/de-identified local data and deterministic providers. It is portfolio evidence, not clinical validation.

## Summary

- `total_cases`: 6
- `passed_cases`: 6
- `pass_rate`: 1.0
- `citation_validity_rate`: 1.0
- `safe_refusal_rate`: 1.0
- `unauthorized_chunks_to_llm`: 0

## Cases

### no_evidence_refusal - PASS

- Expected: No-evidence question returns safe refusal.
- Observed: I could not find authorized evidence for this question. Please review the patient record directly or ask a records user to index the relevant document.
- Metadata: `{"confidence": "low"}`

### cited_patient_answer - PASS

- Expected: Answer cites retrieved patient evidence.
- Observed: Based on the authorized evidence, Alice Synthetic has a documented allergy to penicillin [E1].
- Metadata: `{"citations": ["E1"]}`

### denied_patient_refusal - PASS

- Expected: Unauthorized patient request is denied before retrieval/generation.
- Observed: PermissionDeniedError raised before answer generation.
- Metadata: `{"ai_query_status": "denied"}`

### hms_appointment_evidence - PASS

- Expected: HMS appointment evidence is citeable in patient answer.
- Observed: The appointment status is completed [E1]. Vital signs: BP 118/76, HR 70 [E1].
- Metadata: `{"citations": ["HMS appointment summary 30000000-0000-0000-0000-000000000001"]}`

### general_knowledge_citation - PASS

- Expected: Approved non-PHI source answers general policy question.
- Observed: Based on the authorized evidence, Ward transfer requests should include receiving unit confirmation, attending approval, current observation needs, isolation precautions, and the latest medication administration status [E1].
- Metadata: `{"citations": ["Approved ward transfer policy"]}`

### graph_relation_scope - PASS

- Expected: Graph relation lookup returns only patient-scoped chunk context.
- Observed: 1 related chunk(s)
- Metadata: `{"entities": ["metformin", "diabetes", "insulin"]}`
