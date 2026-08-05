"""Generate V3 schemas and smoke manifest."""

import json
from pathlib import Path
from uuid import uuid4

from hospital_ai.evaluation.corpus_v3 import UnifiedCorpusV3
from hospital_ai.evaluation.threshold_artifact import ThresholdArtifact

DATA_EVAL_DIR = Path("data/evaluation")
DATA_EVAL_DIR.mkdir(parents=True, exist_ok=True)

# 1. Generate Schema for Corpus V3
corpus_schema = UnifiedCorpusV3.schema()
(DATA_EVAL_DIR / "corpus-v3.schema.json").write_text(json.dumps(corpus_schema, indent=2), encoding="utf-8")

# 2. Generate Schema for Threshold Artifact
threshold_schema = ThresholdArtifact.schema()
(DATA_EVAL_DIR / "thresholds-v3.schema.json").write_text(json.dumps(threshold_schema, indent=2), encoding="utf-8")


# 3. Generate Smoke Manifest
def make_item(idx: int, split: str) -> dict:
    return {
        "corpus_item_id": f"smoke-item-{idx}",
        "patient_surrogate_id": f"smoke-patient-{idx}",
        "document_family_id": f"smoke-family-{idx}",
        "split": split,
        "source_objects": [
            {
                "source_path": f"patients_documents/smoke-{idx}.pdf",
                "source_sha256": "0" * 63 + str(idx),
                "rendering_hash": "r" * 63 + str(idx),
                "mime_type": "application/pdf",
            }
        ],
        "canonical_transcript": {"artifact_id": f"trans-{idx}", "sha256": "1" * 63 + str(idx)},
        "ocr_outputs": [],
        "approved_revision_ids": [str(uuid4())],
        "structured_facts": [],
        "graph": None,
        "timeline": [],
        "questions": [],
        "permissions": [],
    }


smoke_manifest = {
    "schema_version": "3.0",
    "corpus_id": "hospital-ai-unified-clinical-corpus-v3",
    "items": [
        make_item(1, "train"),
        make_item(2, "qualification"),
        make_item(3, "development"),
        make_item(4, "sentinel"),
        make_item(5, "holdout"),
    ],
}

# Verify it loads correctly
UnifiedCorpusV3.parse_obj(smoke_manifest)

(DATA_EVAL_DIR / "corpus-v3-smoke-manifest.json").write_text(json.dumps(smoke_manifest, indent=2), encoding="utf-8")
print("Successfully generated schemas and smoke manifest!")
