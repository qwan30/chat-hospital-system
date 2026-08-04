# Vendored Public Medical Data Design

## Status

Approved for implementation on 2026-08-04 and refined during the TDD RED phase after GitHub rejected cross-repository reuse of the upstream ZIP blob.

## Goal

Add a compact, legally reusable public medical dataset directly to the repository so local development, CI, Docker builds, and VPS source deployments use the same immutable files without downloading data at runtime or inside GitHub Actions.

## Scope

This change will:

1. Vendor five original MedQuAD GARD XML documents under `app/backend/data/public/medquad/sample/`.
2. Preserve each selected upstream file byte-for-byte and pin the MedQuAD upstream commit.
3. Record source identity, upstream blob identity, license, exact byte size, and SHA-256 in a machine-readable registry.
4. Add offline validation code and tests for registry schema, path containment, artifact presence, hashes, sizes, and license metadata.
5. Keep GitHub Actions offline with respect to external datasets: workflows may validate vendored files but must not download them.
6. Replace misleading MIMIC/Hugging Face scripts with accurately named synthetic/offline tooling.
7. Document how committed data reaches a VPS through clone/pull and how Docker build rules affect inclusion.

The full 47,457-pair MedQuAD collection and the separate LiveQA ZIP are outside this first implementation. A readable five-document sample establishes provenance, redistribution, integrity, and deployment controls without unnecessary repository growth.

## Source and licensing

The source is the official `abachaa/MedQuAD` repository pinned at commit `577bd37b96c02d1833b2c9eed2de9f96964e96cb`. The selected XML documents come from `2_GARD_QA/` and remain unmodified. The upstream project describes MedQuAD as medical question-answer pairs created from trusted NIH websites and licenses it under CC BY 4.0.

The selected upstream files are:

- `2_GARD_QA/0003206.xml`
- `2_GARD_QA/0003638.xml`
- `2_GARD_QA/0004425.xml`
- `2_GARD_QA/0004873.xml`
- `2_GARD_QA/0005459.xml`

The registry must contain:

- stable source identifier;
- upstream repository and pinned commit;
- upstream path and blob SHA for every artifact;
- retrieval date;
- license identifier and attribution;
- vendored relative path;
- exact byte size;
- lowercase SHA-256 digest;
- intended use and explicit clinical limitations.

## Repository layout

```text
app/backend/data/public/
├── sources.json
└── medquad/
    ├── README.md
    ├── LICENSE.txt
    └── sample/
        └── 2_GARD_QA/
            ├── 0003206.xml
            ├── 0003638.xml
            ├── 0004425.xml
            ├── 0004873.xml
            └── 0005459.xml

app/backend/src/hospital_ai/data_sources/
├── __init__.py
└── registry.py

app/backend/scripts/
├── validate_vendored_public_data.py
└── seed_mock_clinical_notes.py

app/backend/tests/data_sources/
└── test_vendored_public_data.py
```

## Runtime model

The vendored XML files are part of Git history. Therefore:

- a developer receives them on clone or pull;
- a GitHub-hosted runner receives them through `actions/checkout`;
- a VPS source deployment receives them through clone or pull;
- a Docker image receives them only when the Docker build copies the backend data path;
- no runtime downloader is required;
- no GitHub Actions step may fetch the dataset from Hugging Face, GitHub, or another external host.

The application addresses each file by a repository-relative path resolved from the backend data root. Validation is offline and deterministic.

## Integrity and failure behavior

Validation is fail-closed. It must fail when:

- the registry is malformed;
- an artifact is missing;
- size or SHA-256 differs;
- a path is absolute or escapes the configured data root;
- license or attribution metadata is missing;
- a workflow introduces an external dataset download command.

The validator must not repair, download, or silently replace an artifact.

## Legacy cleanup

`seed_mimic.py` contains only hand-authored synthetic notes. It will be replaced by `seed_mock_clinical_notes.py`, and patient names, MRN prefixes, console messages, and comments will no longer claim MIMIC provenance.

`download_hf_notes.py` will be removed. It changes MACCROBAT semantics by forcing every record to `Discharge summary` and naming the output `NOTEEVENTS.csv`. No replacement network downloader will be added because approved public data is committed directly.

## Testing

Tests cover:

1. valid registry loading;
2. path containment;
3. exact hash and size for all five XML files;
4. explicit CC BY 4.0 attribution and evaluation-only limitations;
5. validator success against the repository data root;
6. validator failure against missing or modified artifacts;
7. absence of external dataset download commands in GitHub Actions;
8. absence of misleading MIMIC/Hugging Face downloader scripts.

## Deployment implications

The selected data is small enough to travel with source control. Future additions require an explicit size, license, provenance, privacy, and operational-value review. Public availability alone is not sufficient justification for vendoring a corpus.

## Non-goals

- Treating MedQuAD as patient records or current clinical truth.
- Training or validating a production clinical decision system from five sample files.
- Downloading datasets during CI, application startup, or VPS deployment.
- Adding gated, DUA-controlled, or patient-identifiable data.
- Vendoring the complete MedQuAD collection in this branch.
