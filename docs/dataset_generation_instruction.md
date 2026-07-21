# Specification & AI Instruction Manual for Generating English HMS Datasets

This document serves as a comprehensive specification and instruction set for generating the complete, realistic clinical and system datasets for the **AI-Powered Hospital Knowledge Assistant (HOSP-AI-001)**.

Following the project direction, **all clinical documents, guidelines, and safety databases must be generated in English** to align with the core MVP scope defined in [project-foundation.md](file:///d:/projects/chatbot-hospital-system/docs/00-overview/project-foundation.md#L90) and ensure maximum retrieval and reasoning accuracy.

---

## 1. Overview of Data Gaps & Target Roles

The database currently lacks actual physical files (PDFs, XLSX, CSVs) for system ingestion, relying instead on database memory seeding. To test the system end-to-end (file upload $\rightarrow$ OCR parsing $\rightarrow$ chunking/embedding $\rightarrow$ Graph RAG), we need the following files generated and placed in the correct directories:

| Role & Scopes | Document / Dataset Need | File Format | File Quantity | Pages/Records per File | Standard / Rules |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cardiologist** / **Hospitalist**<br>(`cardiology_guidelines`, `diagnoses`, `imaging`) | **Clinical Records & Summaries** | `.pdf` or `.docx` | **100 files** (1 per patient) | 2–4 pages | Must follow the SOAP format (Subjective, Objective, Assessment, Plan). Must include stable MRNs (MRN-0001 to MRN-0100). |
| **Nurse** / **RN**<br>(`hospital_guidelines`, `care_plan`) | **Nursing Care Plans & General Guidelines** | `.pdf` or `.md` | **5 files** | 5–10 pages | Nursing protocols, SBAR communication formats, wound care, and daily vital tracking procedures. |
| **Pharmacist**<br>(`medication_safety`, `renal_labs`) | **Drug-Drug & Drug-Allergy Interaction Matrix** | `.csv` or `.xlsx` | **1 file** | ~500 rows | Structured matrix listing active drug interactions, contraindications, and allergy triggers. |
| **Lab Staff**<br>(`labs`, `renal_labs`) | **Structured Lab Trend Sheets** | `.xlsx` or `.csv` | **100 files** (1 per patient) | 1 sheet per patient | Lab panel trend data (BNP, Creatinine, eGFR, AST, ALT, Glucose, HbA1c) over a 6-month period. |
| **Security** / **Compliance**<br>(`audit_logs`, `access_requests`) | **System Event Logs** | `.jsonl` or `.csv` | **1 file** | ~10,000 logs | Mock audit trails of sensitive patient views, access overrides, and security violations. |

---

## 2. Technical File Specifications & Metadata Requirements

To ensure these files parse correctly via the LightRAG parsing engines (native, MinerU, Docling) and link successfully to database schemas, they must conform to the following structures:

### A. Patient Clinical Records (PDF/DOCX)
*   **Target Directory:** `app/backend/data/patients_documents/`
*   **Naming Convention:** `patient_[MRN]_[doc_type].pdf` (e.g., `patient_MRN0001_clinical_note.pdf`)
*   **Header Section Requirements:**
    *   **Patient Name:** Full English synthetic name (e.g., Eleanor Vance, Bob Synthetic)
    *   **MRN (Medical Record Number):** Match EMR database MRNs (`MRN-0001` through `MRN-0100`)
    *   **Date of Birth (DOB):** YYYY-MM-DD
    *   **Encounter Date:** YYYY-MM-DD (between 2023-01-01 and 2026-06-01)
    *   **Attending Provider:** Match seeded doctor names (e.g., `BS. Tran Van Minh`, `BS. Nguyen Thi Lan`, `BS. Le Hoang Phuc`)
*   **Body Content Requirements:**
    *   Must use clinical abbreviations (e.g., BP, HR, RR, SpO2, eGFR, BID, QID, PRN).
    *   Clinical notes must be written in **SOAP** format.
    *   Discharge summaries must clearly delineate: "Reason for Admission", "Hospital Course", "Discharge Medications", "Allergies", and "Follow-up Plan".

### B. Lab Trend Spreadsheets (XLSX)
*   **Target Directory:** `app/backend/data/patients_labs/`
*   **Naming Convention:** `patient_[MRN]_labs.xlsx`
*   **Structure:**
    *   **Sheet 1: Demographic Info** (Patient Name, MRN, DOB, Gender).
    *   **Sheet 2: Lab Results** (A tabular format with columns):
        *   `Date` (YYYY-MM-DD)
        *   `Analyte` (e.g., Creatinine, Glucose, HbA1c, BNP, AST, ALT, Potassium, Hemoglobin)
        *   `Value` (Numeric representation)
        *   `Unit` (e.g., mg/dL, mmol/L, %, pg/mL, U/L)
        *   `Reference Range` (e.g., 0.7-1.3, <100, 3.5-5.0)
        *   `Status` (Normal | High | Low)

### C. Drug Interaction & Safety Database (CSV)
*   **Target Directory:** `app/backend/data/drugs/drug_interaction_matrix.csv`
*   **Columns Required:**
    *   `drug_a` (string, lowercase - generic name, e.g., "apixaban")
    *   `drug_b` (string, lowercase - generic name/class, e.g., "aspirin" or "nsaid")
    *   `interaction_type` (string, enum: `contraindicates` | `interacts_with` | `causes` | `mentioned_with`)
    *   `severity` (string, enum: `critical` | `high` | `medium` | `low`)
    *   `mechanism_action` (text - explanation of why they interact)
    *   `clinical_recommendation` (text - action required by clinician)

### D. System Auditing Logs (JSONL)
*   **Target Directory:** `app/backend/data/security/audit_logs.jsonl`
*   **JSON Fields Required per line:**
    *   `actor_user_id` (UUID matching seeded users)
    *   `action` (string, e.g., `chat.ask`, `document.upload`, `patient.view`)
    *   `object_type` (string, e.g., `ai_query`, `document`, `patient`)
    *   `object_id` (UUID)
    *   `patient_id` (UUID matching seeded patients)
    *   `outcome` (string, enum: `allowed` | `denied` | `failed`)
    *   `trace_id` (UUID)
    *   `ip_address` (IP string)
    *   `metadata` (JSON block containing queries, justification reasons, and error codes)

---

## 3. Ingestion Metadata Schema

When these files are uploaded or indexed, the ingestion pipeline must receive the following metadata payload to correctly seed the database model:

```json
{
  "patient_id": "UUID matching patient record",
  "uploaded_by": "UUID matching doctor/records staff",
  "title": "Document Title (e.g. Discharge Summary 2026-05)",
  "document_type": "prescription | lab_result | clinical_note | discharge_summary | imaging_report | encounter_note",
  "mime_type": "application/pdf | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | text/csv",
  "access_tags": ["cardiology", "medication", "labs", "read"]
}
```

---

## 4. Prompt Template for the Generator AI

Copy and paste the prompt below into another LLM (e.g., Claude 3.5 Sonnet, GPT-4o) to generate the complete dataset.

```markdown
You are an expert Medical Data Generator and Health Informatics Specialist.
Generate a complete dataset of clinical files in English for the chatbot-hospital-system project (HOSP-AI-001).

### Setup Requirements:
1. Generate synthetic patients with MRNs from MRN-0001 to MRN-0100.
2. Ensure patient demographics match realistic clinical profiles (e.g., Bob Synthetic, Post-CABG, MRN-0002; Eleanor Vance, AFib & CKD Stage 3, MRN-0003).
3. Use realistic dates between 2023-01-01 and 2026-06-01.

### Tasks to Perform:
Generate the raw text contents for:
1. 100 Patient Clinical Documents (PDF layouts as Markdown):
   - 25 Lab Results (tabular layout with analytes: Creatinine, HbA1c, BNP, Glucose, eGFR).
   - 20 Clinical Notes (attending SOAP notes).
   - 10 Discharge Summaries (detailed courses of treatment, medication adjustments).
   - 15 Imaging Reports (X-ray, Echocardiogram with structural finding descriptions).
   - 20 Prescriptions (drug name, dosage, frequency).
   - 10 Encounter SOAP Notes.
2. A single comprehensive CSV dataset named 'drug_interaction_matrix.csv' containing at least 200 rows of drug-drug and drug-allergy interactions (using lowercase generic drug names like 'apixaban', 'lisinopril', 'metformin', 'aspirin', 'ibuprofen'). Use columns: drug_a, drug_b, interaction_type (contraindicates|interacts_with|causes|mentioned_with), severity (critical|high|medium|low), mechanism_action, clinical_recommendation.
3. 5 General Nursing Care Guidelines (Markdown) covering SBAR, vital signs check protocol, and wound care.

### Output Constraints:
- Do NOT use diacritics. All output must be in professional clinical English.
- Delineate each file block with a clear file path header, for example:
  === FILE: app/backend/data/patients_documents/patient_MRN0002_discharge.txt ===
  [Insert content here]
- Ensure numbers, reference ranges, and clinical plans are medically plausible (e.g., do not write Metformin 500g, write Metformin 500mg BID).
```
