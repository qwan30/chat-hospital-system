"""Unified Clinical Corpus V3 definitions, split isolation, and loader."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, root_validator

from hospital_ai.evaluation.benchmark import EvidenceLocator, ExpectedFact


class CorpusV3ValidationError(Exception):
    """Raised when Corpus V3 rules or split isolation guarantees are violated."""


class SourceObjectRef(BaseModel):
    source_path: str
    source_sha256: str
    rendering_hash: Optional[str] = None
    mime_type: str = "application/pdf"

    model_config = ConfigDict(frozen=True)


class ArtifactRef(BaseModel):
    artifact_id: str
    sha256: str
    path: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class ExpectedGraph(BaseModel):
    required_nodes: tuple[str, ...] = ()
    required_edges: tuple[tuple[str, str, str], ...] = ()
    evidence: tuple[EvidenceLocator, ...] = ()

    model_config = ConfigDict(frozen=True)


class ExpectedTimelineEvent(BaseModel):
    event_id: str
    event_type: str
    clinical_date: Optional[str] = None
    evidence_locators: tuple[EvidenceLocator, ...] = ()
    superseded: bool = False

    model_config = ConfigDict(frozen=True)


class EvalCaseV3(BaseModel):
    case_id: str
    question: str
    category: str
    answer_policy: str = "answer"
    expected_facts: tuple[ExpectedFact, ...] = ()
    allowed_evidence: tuple[EvidenceLocator, ...] = ()
    forbidden_evidence: tuple[EvidenceLocator, ...] = ()
    absence_terms: tuple[str, ...] = ()
    absence_checked_evidence: tuple[EvidenceLocator, ...] = ()
    graph: Optional[ExpectedGraph] = None
    timeline_expectations: tuple[ExpectedTimelineEvent, ...] = ()

    model_config = ConfigDict(frozen=True)


class PermissionScenario(BaseModel):
    scenario_id: str
    actor_role: str
    allowed_patient_ids: tuple[str, ...] = ()
    expected_outcome: Literal["allow", "refuse", "unauthorized"] = "allow"

    model_config = ConfigDict(frozen=True)


class UnifiedCorpusItemV3(BaseModel):
    corpus_item_id: str
    patient_surrogate_id: str
    document_family_id: str
    split: Literal["train", "qualification", "development", "sentinel", "holdout"]
    source_objects: tuple[SourceObjectRef, ...]
    canonical_transcript: ArtifactRef
    ocr_outputs: tuple[ArtifactRef, ...] = ()
    approved_revision_ids: tuple[UUID, ...] = ()
    structured_facts: tuple[ExpectedFact, ...] = ()
    graph: Optional[ExpectedGraph] = None
    timeline: tuple[ExpectedTimelineEvent, ...] = ()
    questions: tuple[EvalCaseV3, ...] = ()
    permissions: tuple[PermissionScenario, ...] = ()

    model_config = ConfigDict(frozen=True)


class UnifiedCorpusV3(BaseModel):
    schema_version: Literal["3.0"] = "3.0"
    corpus_id: Literal["hospital-ai-unified-clinical-corpus-v3"] = "hospital-ai-unified-clinical-corpus-v3"
    items: tuple[UnifiedCorpusItemV3, ...] = ()

    @root_validator(skip_on_failure=True)
    def _enforce_split_isolation(cls, values: dict) -> dict:
        items = values.get("items") or ()
        seen_patient_splits: dict[str, set[str]] = defaultdict(set)
        seen_family_splits: dict[str, set[str]] = defaultdict(set)
        seen_rendering_splits: dict[str, set[str]] = defaultdict(set)

        for item in items:
            seen_patient_splits[item.patient_surrogate_id].add(item.split)
            seen_family_splits[item.document_family_id].add(item.split)
            for src in item.source_objects:
                if src.rendering_hash:
                    seen_rendering_splits[src.rendering_hash].add(item.split)

        for pid, splits in seen_patient_splits.items():
            if len(splits) > 1:
                raise CorpusV3ValidationError(
                    f"split leakage: patient_surrogate_id '{pid}' appears across splits {sorted(splits)}"
                )
        for fid, splits in seen_family_splits.items():
            if len(splits) > 1:
                raise CorpusV3ValidationError(
                    f"split leakage: document_family_id '{fid}' appears across splits {sorted(splits)}"
                )
        for rhash, splits in seen_rendering_splits.items():
            if len(splits) > 1:
                raise CorpusV3ValidationError(
                    f"split leakage: rendering_hash '{rhash}' appears across splits {sorted(splits)}"
                )
        return values

    model_config = ConfigDict(frozen=True)


def load_corpus_v3(manifest_path: Path) -> UnifiedCorpusV3:
    """Load and validate a Unified Corpus V3 JSON manifest from disk."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return UnifiedCorpusV3.parse_obj(data)
