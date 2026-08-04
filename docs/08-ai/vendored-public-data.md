# Vendored Public Medical Data

## Purpose

The project keeps a small, licensed public medical evaluation sample directly in Git. This makes local development, CI, VPS source deployments, and backend container images use the same immutable files without downloading a dataset during GitHub Actions or application startup.

## Current source

| Field | Value |
|---|---|
| Dataset | MedQuAD GARD evaluation sample |
| Upstream repository | `abachaa/MedQuAD` |
| Pinned commit | `577bd37b96c02d1833b2c9eed2de9f96964e96cb` |
| License | CC BY 4.0 |
| Committed sample | 5 original XML documents |
| Registry | `app/backend/data/public/sources.json` |
| Data location | `app/backend/data/public/medquad/sample/` |

Every XML is copied byte-for-byte from the pinned upstream commit. The registry records its upstream path and Git blob SHA, plus its local byte size and SHA-256.

## What happens in each environment

### Developer machine

A normal clone or pull includes the five XML documents because they are tracked by Git. No dataset bootstrap command is required.

```bash
git clone <repository>
python app/backend/scripts/validate_vendored_public_data.py
```

### GitHub Actions

`actions/checkout` receives the same tracked files. The workflow hashes and tests those files; it does not call Hugging Face, `curl`, `wget`, or another dataset source.

The runner still contains a temporary checkout while the job runs. That is only a disposable copy of repository content, not the authoritative dataset store and not a deployment mechanism.

### VPS source deployment

A VPS that deploys with `git clone` or `git pull` receives the committed XML automatically:

```text
/srv/chat-hospital-system/
└── app/backend/data/public/medquad/sample/
```

The data remains on the VPS filesystem for as long as that working tree remains.

### Docker deployment

The backend image explicitly copies `data/public/` to `/app/data/public/`. The backend `.dockerignore` keeps the rest of `data/` outside the build context while re-including only `data/public/**`.

Therefore a deployment that pulls the built backend image receives the vendored public sample, but does not receive the synthetic patient corpus, uploads, runtime storage, or other backend data directories.

The container contract is enforced by `tests/data_sources/test_vendored_public_data.py`.

## Validation

Run:

```bash
python app/backend/scripts/validate_vendored_public_data.py
```

The validator fails closed when:

- the registry is malformed;
- a file is missing;
- a path is absolute or escapes the backend data root;
- byte size differs;
- SHA-256 differs;
- required license or provenance fields are invalid.

It never downloads, repairs, or silently replaces data.

## Application boundary

The MedQuAD sample is registered as `public_evaluation_dataset`. It is separate from:

- the 100-patient synthetic corpus;
- nursing guidelines and drug matrix that remain quarantined;
- user uploads and HMS runtime data;
- production clinical knowledge.

It may support parser, retrieval, provenance, and evaluation tests. It must not be treated as patient records, current medical guidance, or sufficient evidence for diagnosis or treatment.

## Adding future data

A new public source requires all of the following before merge:

1. redistribution license and attribution;
2. pinned upstream revision and file identity;
3. exact size and SHA-256;
4. privacy and PHI review;
5. documented intended use and limitations;
6. repository-size review;
7. offline tests proving the source does not weaken patient-data or quarantine boundaries.

Large public corpora should not be committed merely because they are downloadable. When repository growth becomes operationally expensive, use versioned object storage or a data registry rather than Git history.
