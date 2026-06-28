# Synthetic RAG Eval Report

This report uses synthetic/de-identified local data and deterministic providers. It is portfolio evidence, not clinical validation.

## Summary

- `total_cases`: 33
- `passed_cases`: 33
- `pass_rate`: 1.0
- `citation_validity_rate`: 1.0
- `safe_refusal_rate`: 1.0
- `unauthorized_chunks_to_llm`: 0

## Cases

### factual_alice_diabetes - PASS

- Expected: Alice's diabetes medication (Metformin) is retrieved and cited.
- Observed: Based on the authorized evidence, Alice Synthetic has type 2 diabetes. Prescribed Metformin 500mg daily [E1].
- Metadata: `{"citations": ["E1"]}`

### factual_alice_bp - PASS

- Expected: Alice's blood pressure (140/90) is retrieved and cited.
- Observed: Based on the authorized evidence, Patient Alice has hypertension. Blood pressure is 140/90. Take Lisinopril 10mg [E1].
- Metadata: `{"citations": ["E1"]}`

### factual_alice_lisinopril - PASS

- Expected: Alice's Lisinopril dose (10mg) is retrieved and cited.
- Observed: Based on the authorized evidence, Patient Alice has hypertension. Blood pressure is 140/90. Take Lisinopril 10mg [E1].
- Metadata: `{"citations": ["E1"]}`

### factual_alice_allergy - PASS

- Expected: Alice's penicillin allergy is retrieved and cited.
- Observed: Based on the authorized evidence, Alice Synthetic has a documented allergy to penicillin [E1].
- Metadata: `{"citations": ["E1"]}`

### factual_alice_surgery - PASS

- Expected: Alice's knee surgery is retrieved and cited.
- Observed: Based on the authorized evidence, Alice had a left knee arthroscopy in 2024 [E1].
- Metadata: `{"citations": ["E1"]}`

### factual_bob_cancer - PASS

- Expected: Bob's cancer stage (stage II) is retrieved and cited.
- Observed: Based on the authorized evidence, Bob Synthetic has lung cancer stage II. Oncology chemotherapy is scheduled [E1].
- Metadata: `{"citations": ["E1"]}`

### factual_bob_surgery - PASS

- Expected: Bob's surgery (appendectomy) is retrieved and cited.
- Observed: Based on the authorized evidence, Bob underwent appendectomy surgery. Post-op recovery normal without complication [E1].
- Metadata: `{"citations": ["E1"]}`

### factual_bob_allergy - PASS

- Expected: Bob's sulfa allergy is retrieved and cited.
- Observed: Based on the authorized evidence, Bob Synthetic has a documented allergy to sulfa drugs [E1].
- Metadata: `{"citations": ["E1"]}`

### factual_bob_aspirin - PASS

- Expected: Bob's aspirin dose (81mg) is retrieved and cited.
- Observed: Based on the authorized evidence, Bob is taking Aspirin 81mg daily [E1].
- Metadata: `{"citations": ["E1"]}`

### factual_bob_gabapentin - PASS

- Expected: Bob's Gabapentin dose (300mg) is retrieved and cited.
- Observed: Based on the authorized evidence, Bob has chronic back pain. Prescribed Gabapentin 300mg dose [E1].
- Metadata: `{"citations": ["E1"]}`

### multihop_alice_meds - PASS

- Expected: Decompose QA pipeline aggregates Alice's medications.
- Observed: pipeline=decompose_qa, answer=Based on the authorized evidence, Patient Alice has hypertension. Blood pressure is 140/90. Take Lisinopril 10mg [E1].
- Metadata: `{"pipeline": "decompose_qa"}`

### multihop_alice_allergy_surgery - PASS

- Expected: Decompose QA pipeline aggregates Alice's allergies and surgeries.
- Observed: pipeline=decompose_qa, answer=Based on the authorized evidence, Alice Synthetic has a documented allergy to penicillin [E1].
- Metadata: `{"pipeline": "decompose_qa"}`

### multihop_bob_cancer_surgery - PASS

- Expected: Decompose QA pipeline aggregates Bob's cancer and surgery.
- Observed: pipeline=decompose_qa, answer=Based on the authorized evidence, Bob Synthetic has lung cancer stage II. Oncology chemotherapy is scheduled [E1].
- Metadata: `{"pipeline": "decompose_qa"}`

### multihop_bob_meds - PASS

- Expected: Decompose QA pipeline aggregates Bob's medications.
- Observed: pipeline=decompose_qa, answer=Based on the authorized evidence, Bob has chronic back pain. Prescribed Gabapentin 300mg dose [E1].
- Metadata: `{"pipeline": "decompose_qa"}`

### multihop_alice_summary - PASS

- Expected: Patient summary pipeline generates Alice overview.
- Observed: pipeline=patient_summary, answer=Based on the authorized evidence, the record contains relevant clinical details [E1].
- Metadata: `{"pipeline": "patient_summary"}`

### multihop_bob_summary - PASS

- Expected: Patient summary pipeline generates Bob overview.
- Observed: pipeline=patient_summary, answer=Based on the authorized evidence, the record contains relevant clinical details [E1].
- Metadata: `{"pipeline": "patient_summary"}`

### perm_nurse_query_bob - PASS

- Expected: Nurse cannot access Bob's oncology chart.
- Observed: PermissionDeniedError correctly raised.
- Metadata: `{}`

### perm_pharmacist_query_bob - PASS

- Expected: Pharmacist cannot access Bob's medication chart.
- Observed: PermissionDeniedError correctly raised.
- Metadata: `{}`

### perm_unauth_doctor_query_bob - PASS

- Expected: Unauthorized doctor cannot access Bob's chart.
- Observed: PermissionDeniedError correctly raised.
- Metadata: `{}`

### perm_unauth_doctor_query_alice - PASS

- Expected: Unauthorized doctor cannot access Alice's chart.
- Observed: PermissionDeniedError correctly raised.
- Metadata: `{}`

### perm_cross_patient_leak_alice_bob - PASS

- Expected: Querying Bob's oncology details in Alice's context returns safe refusal.
- Observed: I could not find authorized evidence for this question. Please review the patient record directly or ask a records user to index the relevant document.
- Metadata: `{"citations_count": 0}`

### perm_cross_patient_leak_bob_alice - PASS

- Expected: Querying Alice's BP in Bob's context returns safe refusal.
- Observed: I could not find authorized evidence for this question. Please review the patient record directly or ask a records user to index the relevant document.
- Metadata: `{"citations_count": 0}`

### negative_alice_cardiac_arrest - PASS

- Expected: Non-existent clinical detail for Alice returns safe refusal.
- Observed: I could not find authorized evidence for this question. Please review the patient record directly or ask a records user to index the relevant document.
- Metadata: `{}`

### negative_bob_stroke - PASS

- Expected: Non-existent clinical detail for Bob returns safe refusal.
- Observed: I could not find authorized evidence for this question. Please review the patient record directly or ask a records user to index the relevant document.
- Metadata: `{}`

### negative_unindexed_topic - PASS

- Expected: Query on unindexed non-clinical topic in patient context returns safe refusal.
- Observed: I could not find authorized evidence for this question. Please review the patient record directly or ask a records user to index the relevant document.
- Metadata: `{}`

### negative_nonexistent_patient - PASS

- Expected: Query with non-existent patient ID raises permission denial.
- Observed: PermissionDeniedError correctly raised.
- Metadata: `{}`

### hms_alice_appointment_status - PASS

- Expected: HMS appointment status is cited in RAG answer.
- Observed: The appointment status is completed [E1]. Vital signs: BP 118/76, HR 70 [E1].
- Metadata: `{"citations": ["HMS appointment summary 30000000-0000-0000-0000-000000000001"]}`

### hms_alice_appointment_vitals - PASS

- Expected: HMS appointment vitals are cited in RAG answer.
- Observed: The appointment status is completed [E1]. Vital signs: BP 125/80 [E1].
- Metadata: `{"citations": ["HMS appointment summary 30000000-0000-0000-0000-000000000002"]}`

### hms_bob_appointment_status - PASS

- Expected: Bob's HMS Oncology appointment status is cited in RAG answer.
- Observed: Based on the authorized evidence, Bob Synthetic has lung cancer stage II. Oncology chemotherapy is scheduled [E1].
- Metadata: `{"citations": ["Bob Oncology Note"]}`

### hms_bob_appointment_reason - PASS

- Expected: Bob's HMS Oncology appointment reason is cited in RAG answer.
- Observed: Based on the authorized evidence, Bob Synthetic has lung cancer stage II. Oncology chemotherapy is scheduled [E1].
- Metadata: `{"citations": ["Bob Oncology Note"]}`

### general_knowledge_citation - PASS

- Expected: Approved non-PHI source answers general policy question.
- Observed: Based on the authorized evidence, Ward transfer requests should include receiving unit confirmation, attending approval, current observation needs, isolation precautions, and the latest medication administration status [E1].
- Metadata: `{"citations": ["Approved ward transfer policy"]}`

### graph_relation_scope - PASS

- Expected: Graph relation lookup returns only patient-scoped chunk context.
- Observed: 1 related chunk(s)
- Metadata: `{"entities": ["metformin", "diabetes", "insulin"]}`

### no_evidence_refusal - PASS

- Expected: No-evidence question returns safe refusal.
- Observed: I could not find authorized evidence for this question. Please review the patient record directly or ask a records user to index the relevant document.
- Metadata: `{"confidence": "low"}`
