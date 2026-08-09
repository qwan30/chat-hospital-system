# Patient Overview Counts Task Report

Date: 2026-08-09

## Scope

- `app/backend/src/hospital_ai/api/routes/patients.py`
- `app/backend/tests/test_patient_bff.py`

## Root cause

`get_patient_overview` used local fallback counts based on document counts:

- medications: `hms_medical_record`
- labs: `hms_lab_result`

The medication and lab tab routes do not use those document counts. They derive visible items from ready indexed chunk evidence:

- medications: `prescription` and `discharge_summary`
- labs: `lab_result` and `hms_lab_result`

That let overview report smaller counts than the authorized tab routes for the same patient-scoped local evidence.

## TDD evidence

### RED

Initial command:

```powershell
python -m pytest tests/test_patient_bff.py
```

Result:

- blocked by environment mismatch, not by product behavior
- system `python` was `3.9.13` and failed importing `str | None` type syntax

Corrected command:

```powershell
& '.venv\Scripts\python.exe' -m pytest tests/test_patient_bff.py
```

Result:

- `2 failed, 5 passed`
- failing assertions reproduced the defect:
  - overview medication count was `0` while medication tab returned `3`
  - overview lab count was `1` while lab tab returned `3`

### GREEN

After extracting shared loaders and switching overview fallback to those loaders:

```powershell
& '.venv\Scripts\python.exe' -m pytest tests/test_patient_bff.py
```

Result:

- `7 passed`

## Additional verification

GitNexus pre-edit impact:

- `get_patient_overview` upstream impact: `LOW`, `0` indexed direct callers
- `get_patient_medications` upstream impact: `LOW`, `0` indexed direct callers
- `get_patient_labs` upstream impact: `LOW`, `0` indexed direct callers

Regression route tests:

```powershell
& '.venv\Scripts\python.exe' -m pytest tests/test_patients.py
```

Result:

- `17 passed`

Targeted lint:

```powershell
& '.venv\Scripts\python.exe' -m ruff check src/hospital_ai/api/routes/patients.py tests/test_patient_bff.py
```

Result:

- all checks passed

Targeted format check:

```powershell
& '.venv\Scripts\python.exe' -m ruff format --check src/hospital_ai/api/routes/patients.py tests/test_patient_bff.py
```

Result after formatting:

- both files already formatted

GitNexus staged change detection:

- command shape: `detect_changes(scope="staged")`
- summary: `changed_files=3`, `changed_count=9`, `affected_count=15`, `risk_level=high`
- manual review note: the high risk came from whole-file symbol attribution in `patients.py` and line-shift attribution in `test_patient_bff.py`; the actual behavioral diff is limited to:
  - overview fallback medication/lab count computation
  - shared medication/lab loaders reused by the existing tab routes
  - focused BFF parity tests
  - this task report

## Test changes

- removed one stale assertion in the summary-pipeline overview test that depended on the old broken fallback contract
- added focused overview-vs-tab parity tests for:
  - medication items from ready indexed prescription/discharge metadata
  - lab items from ready indexed lab metadata with duplicate suppression matching the lab tab route

## Implementation summary

- added `_load_patient_medications(...)`
- added `_load_patient_labs(...)`
- reused those loaders in:
  - `get_patient_overview` local fallback counts
  - `get_patient_medications`
  - `get_patient_labs`

This preserves:

- existing permission checks
- existing response shapes
- audit behavior
- live HMS snapshot precedence
- patient scoping
