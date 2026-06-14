# User Flows

> Project: HOSP-AI-001 · Version: 1.0 · Last Updated: 2026-06-14  

## 1. Doctor — Patient Round Prep

```
Login → Dashboard → Search patient (Ctrl+K) → Overview (EMR + AI summary)
  → Review medications (drug check) → Review labs (timeline)
  → Chat → "Summarize recent labs" → View cited answer → Verify source
```
**Screens:** SCR-001,003,007,009,013

## 2. Nurse — Medication Check

```
Login → Dashboard → Recent Patients → Select patient
  → Medication Review → Check AI interaction warnings
  → "Any allergies to this prescription?" → Drug check result
```
**Screens:** SCR-003,007,009,013

## 3. Pharmacist — Drug Verification

```
Login → Search patient by MRN → Medication Review
  → "Check interactions: Metformin + new Rx" → AI flags conflicts
```
**Screens:** SCR-001,008,009

## 4. Records Staff — Document Upload

```
Login → Documents Dashboard → Upload PDF
  → Select patient + document type → Monitor OCR progress
  → Review low-confidence pages → Retry if needed → Verify indexing
```
**Screens:** SCR-015,016,017

## 5. Security Officer — Audit Review

```
Login → Audit Logs → Filter (date, patient, action, outcome)
  → Inspect suspicious events → View event details → Export report
```
**Screens:** SCR-019,020

## 6. Admin — System Config

```
Login → Settings → Review health (HMS + Ollama status)
  → Configure LLM provider → Set rate limits → View metrics dashboard
```
**Screens:** SCR-025,005,018

## Change Log
| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-14 | Agent | 6 persona-based user flows covering all 14 frontend pages |
