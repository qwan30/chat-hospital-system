# MedQuAD GARD evaluation sample

This directory vendors five original XML documents from the official `abachaa/MedQuAD` repository. The files are committed directly so local development, CI, and VPS source deployments can use the same immutable data without a network download.

## Pinned source

- Repository: `abachaa/MedQuAD`
- Commit: `577bd37b96c02d1833b2c9eed2de9f96964e96cb`
- Upstream collection: `2_GARD_QA`
- License: CC BY 4.0
- Registry: `../sources.json`

Each local XML file preserves the exact upstream Git blob. `sources.json` records its upstream path and blob SHA together with local byte size and SHA-256.

## Intended use

The sample supports deterministic parser, ingestion, retrieval, provenance, and evaluation tests. It is intentionally small and human-reviewable.

## Limitations

- It is not the complete MedQuAD corpus.
- It is not patient data.
- It is not current clinical guidance.
- It is not representative enough for model training or clinical-accuracy claims.
- It must not be used as evidence for diagnosis, treatment, or other production clinical decisions.

Run the offline integrity check from the repository root:

```bash
python app/backend/scripts/validate_vendored_public_data.py
```

The validator reads only committed files and never downloads or repairs data.
