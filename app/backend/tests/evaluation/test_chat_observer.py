from __future__ import annotations

from uuid import uuid4

import pytest


def test_evaluation_controls_are_frozen_and_validate_modes() -> None:
    from hospital_ai.evaluation.observer import EvaluationControls

    controls = EvaluationControls.hybrid_graph_on("run-c", graph_required=True)

    assert controls.mode == "hybrid_graph_on"
    assert controls.graph_required is True
    with pytest.raises(AttributeError):
        controls.mode = "rag_off"  # type: ignore[misc]
    with pytest.raises(ValueError, match="graph_required"):
        EvaluationControls.rag_off("run-a", graph_required=True)


def test_require_indexed_fails_when_selected_chunk_has_no_logical_binding() -> None:
    from hospital_ai.evaluation.observer import EvidenceBindingError, InMemoryEvaluationObserver
    from hospital_ai.services.retrieval import RetrievedChunk

    chunk = RetrievedChunk("E1", uuid4(), "record", 1, uuid4(), 0.9, "text", {})
    observer = InMemoryEvaluationObserver(require_indexed=True)

    with pytest.raises(EvidenceBindingError, match=str(chunk.chunk_id)):
        observer.record_selected_context((chunk,))


def test_observer_binds_logical_evidence_to_exact_selected_chunk() -> None:
    from hospital_ai.evaluation.observer import InMemoryEvaluationObserver
    from hospital_ai.services.retrieval import RetrievedChunk

    logical_id, chunk_id = uuid4(), uuid4()
    chunk = RetrievedChunk("E1", uuid4(), "record", 1, chunk_id, 0.9, "text", {})
    observer = InMemoryEvaluationObserver(
        logical_evidence_by_chunk={chunk_id: logical_id},
        require_indexed=True,
    )

    observer.record_selected_context((chunk,))
    observer.record_generator_context((chunk,))
    observer.record_cited_chunks((chunk,))
    snapshot = observer.snapshot()

    assert snapshot.selected_chunk_ids == (chunk_id,)
    assert snapshot.generator_context_chunk_ids == (chunk_id,)
    assert snapshot.selected_evidence_ids == (logical_id,)
    assert snapshot.cited_chunk_ids == (chunk_id,)


def test_binding_builder_rejects_unresolved_or_ambiguous_pairs() -> None:
    from hospital_ai.evaluation.observer import EvidenceBindingError, bind_indexed_evidence

    evidence_id, chunk_id = uuid4(), uuid4()
    assert bind_indexed_evidence((evidence_id,), (chunk_id,)) == {chunk_id: evidence_id}
    with pytest.raises(EvidenceBindingError, match="unresolved"):
        bind_indexed_evidence((evidence_id,), ())
    with pytest.raises(EvidenceBindingError, match="multiple logical"):
        bind_indexed_evidence((evidence_id, uuid4()), (chunk_id, chunk_id))


@pytest.mark.asyncio
async def test_reasoning_observer_records_exact_generator_context(session_and_settings, monkeypatch) -> None:
    from hospital_ai.evaluation.observer import InMemoryEvaluationObserver
    from hospital_ai.services.reasoning import SimpleQAPipeline
    from hospital_ai.services.retrieval import RetrievedChunk

    _, settings = session_and_settings
    first_id, second_id = uuid4(), uuid4()
    first = RetrievedChunk("E1", uuid4(), "first", 1, first_id, 0.9, "first fact", {})
    second = RetrievedChunk("E2", uuid4(), "second", 1, second_id, 0.8, "second fact", {})

    def rerank(_self, _question, _evidence, *, top_k):
        assert top_k == settings.retrieval_top_k
        return [second, first]

    async def generate(_self, _prompt):
        return "The second fact is supported [E2]."

    monkeypatch.setattr("hospital_ai.services.reasoning.RerankerService.rerank", rerank)
    monkeypatch.setattr("hospital_ai.services.reasoning.ChatGenerator.generate", generate)
    observer = InMemoryEvaluationObserver()

    await SimpleQAPipeline(settings).run(question="Which fact?", evidence=[first, second], evaluation_observer=observer)

    snapshot = observer.snapshot()
    assert snapshot.selected_chunk_ids == (second_id, first_id)
    assert snapshot.generator_context_chunk_ids == snapshot.selected_chunk_ids


@pytest.mark.asyncio
async def test_graph_required_failure_is_not_silently_swallowed(session_and_settings, monkeypatch) -> None:
    from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
    from hospital_ai.db.models import User
    from hospital_ai.evaluation.observer import (
        EvaluationControls,
        GraphCertificationError,
        InMemoryEvaluationObserver,
    )
    from hospital_ai.services.chat import ChatService
    from hospital_ai.services.graph_rag import ExtractedEntity
    from hospital_ai.services.retrieval import RetrievalService

    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    async def no_hits(self, **_kwargs):
        return []

    async def entities(_question):
        return [ExtractedEntity("metformin", "drug")], []

    async def failing_graph(*_args, **_kwargs):
        raise RuntimeError("graph unavailable")

    monkeypatch.setattr(RetrievalService, "hybrid_search", no_hits)
    monkeypatch.setattr("hospital_ai.services.chat.extract_entities_and_relations_nlp", entities)
    monkeypatch.setattr("hospital_ai.services.chat.find_related_entities", failing_graph)

    with pytest.raises(GraphCertificationError, match="Graph traversal failed"):
        await ChatService(session, settings).answer(
            user=doctor,
            patient_id=PATIENT_ALICE_ID,
            question="What does metformin treat?",
            top_k=1,
            trace_id="graph-required",
            ip_address="127.0.0.1",
            evaluation_controls=EvaluationControls.hybrid_graph_on("run-c", graph_required=True),
            evaluation_observer=InMemoryEvaluationObserver(),
        )


@pytest.mark.asyncio
async def test_rag_off_bypasses_retrieval_and_graph(session_and_settings, monkeypatch) -> None:
    from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
    from hospital_ai.db.models import User
    from hospital_ai.evaluation.observer import EvaluationControls, InMemoryEvaluationObserver
    from hospital_ai.services.chat import SAFE_NO_EVIDENCE_ANSWER, ChatService
    from hospital_ai.services.retrieval import RetrievalService

    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)

    async def forbidden_retrieval(self, **_kwargs):
        raise AssertionError("retrieval must not run")

    async def forbidden_graph(*_args, **_kwargs):
        raise AssertionError("graph must not run")

    monkeypatch.setattr(RetrievalService, "hybrid_search", forbidden_retrieval)
    monkeypatch.setattr("hospital_ai.services.chat.find_related_entities", forbidden_graph)
    observer = InMemoryEvaluationObserver()

    response = await ChatService(session, settings).answer(
        user=doctor,
        patient_id=PATIENT_ALICE_ID,
        question="What is in the record?",
        top_k=1,
        trace_id="rag-off",
        ip_address="127.0.0.1",
        evaluation_controls=EvaluationControls.rag_off("run-a"),
        evaluation_observer=observer,
    )

    snapshot = observer.snapshot()
    assert response.answer == SAFE_NO_EVIDENCE_ANSWER
    assert snapshot.selected_context == ()
    assert snapshot.graph_ran is False


@pytest.mark.asyncio
async def test_hybrid_graph_off_runs_hybrid_retrieval_without_graph(session_and_settings, monkeypatch) -> None:
    from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
    from hospital_ai.db.models import User
    from hospital_ai.evaluation.observer import EvaluationControls, InMemoryEvaluationObserver
    from hospital_ai.services.chat import ChatService
    from hospital_ai.services.retrieval import RetrievalService

    session, settings = session_and_settings
    doctor = await session.get(User, DOCTOR_ID)
    retrieval_modes: list[str] = []

    async def no_hits(self, **kwargs):
        retrieval_modes.append(kwargs["retrieval_mode"])
        return []

    async def forbidden_graph(*_args, **_kwargs):
        raise AssertionError("graph must not run")

    monkeypatch.setattr(RetrievalService, "hybrid_search", no_hits)
    monkeypatch.setattr("hospital_ai.services.chat.find_related_entities", forbidden_graph)
    observer = InMemoryEvaluationObserver()

    await ChatService(session, settings).answer(
        user=doctor,
        patient_id=PATIENT_ALICE_ID,
        question="What is in the record?",
        top_k=1,
        trace_id="graph-off",
        ip_address="127.0.0.1",
        evaluation_controls=EvaluationControls.hybrid_graph_off("run-b"),
        evaluation_observer=observer,
    )

    assert retrieval_modes == ["hybrid"]
    assert observer.snapshot().graph_ran is False
