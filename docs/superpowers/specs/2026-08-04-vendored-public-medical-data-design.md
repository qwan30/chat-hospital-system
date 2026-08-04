# Vendored Public Medical Data Design

## Status

Approved for implementation on 2026-08-04.

## Goal

Add a compact, legally reusable public medical dataset directly to the repository so local development, CI, Docker builds, and VPS deployments can use the same immutable files without downloading data at runtime or inside GitHub Actions.

## Scope

This change will:

1. Vendor the compact MedQuAD LiveQA judged-set archive into `app/backend/data/public/medquad/`.
2. Record source identity, upstream revision, license, size, and SHA-256 in a machine-readable registry.
3. Add offline validation code and tests for registry schema, artifact presence, hash, size, and license metadata.
4. Keep GitHub Actions offline with respect to external datasets: workflows may validate vendored files but must not download them.
5. Replace misleading MIMIC/Hugging Face scripts with accurately named synthetic/offline tooling.
6. Document how the committed dataset reaches a VPS through clone, pull, or the Docker build context.

The full 47,457-pair MedQuAD collection is intentionally outside this first implementation. The vendored artifact is the smaller official LiveQA judged set so repository growth remains controlled while the provenance and validation architecture is established.

## Source and licensing

The first source is the official `abachaa/MedQuAD` repository artifact `QA-TestSet-LiveQA-Med-Qrels-2479-Answers.zip`. The upstream project describes MedQuAD as medical question-answer pairs created from NIH websites and licenses it under CC BY 4.0.

The registry must contain:

- stable source identifier;
- upstream repository and file path;
- pinned upstream blob SHA;
- retrieved date;
- license identifier and attribution;
- vendored relative path;
- byte size;
- SHA-256 digest;
- intended use and explicit clinical limitations.

## Repository layout

```text
app/backend/data/public/
├── sources.json
└── medquad/
    ├── README.md
    ├── LICENSE.txt
    └── QA-TestSet-LiveQA-Med-Qrels-2479-Answers.zip

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

The vendored archive is part of Git history. Therefore:

- a developer receives it on clone or pull;
- a GitHub-hosted runner receives it through `actions/checkout`;
- a VPS receives it through clone or pull;
- a Docker image receives it only when the Docker build copies the data path;
- no runtime downloader is required;
- no GitHub Actions step may fetch the dataset from Hugging Face, GitHub, or another external host.

The application must address the file by repository-relative path resolved from the backend data root. Validation must be offline and deterministic.

## Integrity and failure behavior

Validation is fail-closed. It must fail when:

- the registry is malformed;
- the artifact is missing;
- size or SHA-256 differs;
- a path escapes the configured data root;
- the license metadata is missing;
- a workflow introduces a command that downloads external dataset content.

The validator must not repair, download, or silently replace an artifact.

## Legacy cleanup

`seed_mimic.py` contains only hand-authored synthetic notes. It will be replaced by `seed_mock_clinical_notes.py`, and patient names, MRN prefixes, console messages, and comments will no longer claim MIMIC provenance.

`download_hf_notes.py` will be removed. It currently changes MACCROBAT semantics by forcing every record to `Discharge summary` and naming the output `NOTEEVENTS.csv`. No replacement network downloader will be added because the chosen architecture vendors approved data directly.

## Testing

Tests will cover:

1. valid registry loading;
2. path containment;
3. exact vendored artifact hash and size;
4. explicit CC BY 4.0 attribution and intended-use limitations;
5. validator success against the repository data root;
6. validator failure against missing or modified artifacts;
7. absence of external dataset download commands in GitHub Actions;
8. absence of misleading MIMIC/Hugging Face downloader scripts.

## Deployment implications

The dataset is small enough to travel with source control. Future additions require an explicit size review and registry entry. Large corpora must not be added automatically merely because they are public; repository size, redistribution terms, privacy, and operational value must be reviewed first.

## Non-goals

- Treating MedQuAD as patient records or clinical ground truth.
- Training a production clinical model from this artifact.
- Downloading datasets during CI, application startup, or VPS deployment.
- Adding gated, DUA-controlled, or patient-identifiable data.
- Vendoring the complete MedQuAD collection in this first branch.
