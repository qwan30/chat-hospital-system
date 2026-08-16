"""Unit tests for Unified Corpus V3 contract and split isolation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError

from hospital_ai.evaluation.benchmark import EvidenceLocator, ExpectedFact
from hospital_ai.evaluation.corpus_v3 import (
    CorpusV3ValidationError,
    EvalCaseV3,
    ExpectedGraph,
    ExpectedTimelineEvent,
    PermissionScenario,
    UnifiedCorpusItemV3,
    UnifiedCorpusV3,
    load_corpus_v3,
)


def _sample_item(
    item_id: str = "item-001",
    patient_id: str = "patient-alpha",
    family_id: str = "family-100",
    split: str = "train",
    sha256: str = "a" * 64,
) -> dict[str, Any]:
    rev_id = UUID("11111111-1111-1111-1111-111111111111")
    locator = EvidenceLocator(source_path="patients_documents/doc.pdf", page_number=1)
    fact = ExpectedFact(
        fact_id="fact-1",
        statement="Patient takes metformin",
        evidence=(locator,),
        verification_terms=("metformin",),
    )
    graph = ExpectedGraph(
        required_nodes=("metformin",),
        required_edges=(("patient", "takes", "metformin"),),
        evidence=(locator,),
    )
    timeline_ev = ExpectedTimelineEvent(
        event_id="ev-1",
        event_type="medication",
        clinical_date="2025-01-01",
        evidence_locators=(locator,),
    )
    case = EvalCaseV3(
        case_id=f"case-{item_id}",
        question="What medication is the patient taking?",
        category="single_hop",
        answer_policy="answer",
        expected_facts=(fact,),
        allowed_evidence=(locator,),
    )
    perm = PermissionScenario(
        scenario_id=f"perm-{item_id}",
        actor_role="doctor",
        allowed_patient_ids=(patient_id,),
        expected_outcome="allow",
    )
    return {
        "corpus_item_id": item_id,
        "patient_surrogate_id": patient_id,
        "document_family_id": family_id,
        "split": split,
        "source_objects": [
            {
                "source_path": f"patients_documents/{item_id}.pdf",
                "source_sha256": sha256,
                "rendering_hash": sha256,
            }
        ],
        "canonical_transcript": {"artifact_id": f"trans-{item_id}", "sha256": "b" * 64},
        "ocr_outputs": [{"artifact_id": f"ocr-{item_id}", "sha256": "c" * 64}],
        "approved_revision_ids": [str(rev_id)],
        "structured_facts": [fact.dict()],
        "graph": graph.dict(),
        "timeline": [timeline_ev.dict()],
        "questions": [case.dict()],
        "permissions": [perm.dict()],
    }


def test_unified_corpus_item_v3_instantiates_and_validates() -> None:
    data = _sample_item()
    item = UnifiedCorpusItemV3.parse_obj(data)
    assert item.corpus_item_id == "item-001"
    assert item.split == "train"
    assert len(item.source_objects) == 1
    assert len(item.approved_revision_ids) == 1


def test_unified_corpus_v3_requires_exact_corpus_id() -> None:
    data1 = _sample_item("1", "p1", "f1", "train", "a" * 64)
    corpus = UnifiedCorpusV3(
        corpus_id="hospital-ai-unified-clinical-corpus-v3",
        items=(UnifiedCorpusItemV3.parse_obj(data1),),
    )
    assert corpus.corpus_id == "hospital-ai-unified-clinical-corpus-v3"

    with pytest.raises(ValidationError):
        UnifiedCorpusV3(
            corpus_id="invalid-corpus-id",
            items=(UnifiedCorpusItemV3.parse_obj(data1),),
        )


def test_split_isolation_patient_leakage_raises() -> None:
    data1 = _sample_item("1", "patient-leak", "f1", "train", "1" * 64)
    data2 = _sample_item("2", "patient-leak", "f2", "holdout", "2" * 64)
    with pytest.raises(CorpusV3ValidationError, match="split leakage"):
        UnifiedCorpusV3(
            corpus_id="hospital-ai-unified-clinical-corpus-v3",
            items=(UnifiedCorpusItemV3.parse_obj(data1), UnifiedCorpusItemV3.parse_obj(data2)),
        )


def test_split_isolation_document_family_leakage_raises() -> None:
    data1 = _sample_item("1", "p1", "family-leak", "train", "1" * 64)
    data2 = _sample_item("2", "p2", "family-leak", "sentinel", "2" * 64)
    with pytest.raises(CorpusV3ValidationError, match="split leakage"):
        UnifiedCorpusV3(
            corpus_id="hospital-ai-unified-clinical-corpus-v3",
            items=(UnifiedCorpusItemV3.parse_obj(data1), UnifiedCorpusItemV3.parse_obj(data2)),
        )


def test_split_isolation_rendering_hash_leakage_raises() -> None:
    data1 = _sample_item("1", "p1", "f1", "development", "f" * 64)
    data2 = _sample_item("2", "p2", "f2", "qualification", "f" * 64)
    with pytest.raises(CorpusV3ValidationError, match="split leakage"):
        UnifiedCorpusV3(
            corpus_id="hospital-ai-unified-clinical-corpus-v3",
            items=(UnifiedCorpusItemV3.parse_obj(data1), UnifiedCorpusItemV3.parse_obj(data2)),
        )


def test_load_smoke_manifest(tmp_path: Path) -> None:
    data1 = _sample_item("1", "p1", "f1", "train", "1" * 64)
    data2 = _sample_item("2", "p2", "f2", "qualification", "2" * 64)
    payload = {
        "schema_version": "3.0",
        "corpus_id": "hospital-ai-unified-clinical-corpus-v3",
        "items": [data1, data2],
    }
    path = tmp_path / "smoke.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    corpus = load_corpus_v3(path)
    assert len(corpus.items) == 2
    assert corpus.items[0].split == "train"
    assert corpus.items[1].split == "qualification"
