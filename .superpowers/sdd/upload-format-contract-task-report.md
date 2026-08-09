# Upload format contract task report

## Scope delivered

- Added the standard DOCX OpenXML MIME type to the route allow-list already
  supported by the existing DOCX loader.
- Added `normalize_upload_mime_type`: only a filename ending in `.hl7` plus a
  known HL7 textual MIME type or browser `application/octet-stream` is stored
  as `text/plain`.
- Added `.hl7` to `TextLoader`'s UTF-8 extension set.
- Kept generic binary uploads fail-closed; `application/octet-stream` is not a
  globally allowed MIME type and DICOM behavior is unchanged.

## TDD evidence

- RED with the project Python 3.11 virtual environment: the route-normalizer
  import was absent, `TextLoader` rejected `.hl7`, and browser-style HL7 upload
  raised `Unsupported file type: application/octet-stream`; a non-HL7 binary
  rejection already passed.
- GREEN contract tests: browser `.hl7` upload reaches `ready` with one page and
  normalized `text/plain`; HL7 loader routing, DOCX MIME normalization, and
  arbitrary octet-stream rejection pass.

## Validation

- `app/backend/.venv/Scripts/python.exe -m pytest tests/test_documents.py tests/api/test_documents.py tests/workers/test_documents_pipeline.py` — 25 passed.
- Focused contract selection — 4 passed.
- Ruff check and format check for all owned files passed.
- GitNexus impact before edits: `upload_document` LOW (no indexed callers) and
  `TextLoader` LOW (one direct caller). Staged change detection and diff check
  run before commit.

## Environment note

- The shell `python` resolves to Python 3.9 and global Python 3.12 contains an
  incompatible Pydantic major version. Backend checks used the repository's
  `.venv` Python 3.11 environment, matching the project dependencies.

## Review follow-up

- Independent review found that allowing DOCX only at the API boundary was
  insufficient: the active worker sent DOCX bytes to PyMuPDF. It also found
  that missing HL7 content types were accidentally treated as browser octet
  streams.
- The worker now routes `.docx` sources through `DocxLoader` using a temporary
  file for both local and object storage. `DocxLoader` has a standard-library
  OOXML ZIP/XML fallback when optional `python-docx` is absent, so the accepted
  MIME reaches `ready` in the repository environment without a dependency or
  lockfile change.
- A missing/blank content type is fail-closed before HL7 normalization; only an
  explicitly supplied allowed HL7 MIME or browser octet-stream on `.hl7` is
  accepted.
- Follow-up validation: 27 document/API/worker tests passed; Ruff check and
  format check passed for the expanded five-file production/test scope.

## Safety follow-up

- Final review found two DOCX safety issues. The worker now records the temp
  path before storage I/O and unlinks it in `finally`, including a read/write
  failure path.
- The standard-library OOXML fallback now caps `word/document.xml` at 8 MiB
  using ZIP metadata plus a bounded stream read before XML parsing. Oversized
  parts fail closed rather than allocating unbounded text.
- Added tests for temporary-file cleanup after a simulated object-storage read
  failure and for an oversized compressed OOXML document part.
- Final focused validation: 29 document/API/worker tests passed; Ruff check
  and format check passed.

## Coverage follow-up

- Added direct tests for a temporary-file write failure (in addition to a
  storage-read failure) and for the bounded stream-read guard when ZIP metadata
  is within the size cap but the decompressed stream exceeds it.
- The four DOCX safety regressions pass independently before the final full
  document/API/worker validation.
