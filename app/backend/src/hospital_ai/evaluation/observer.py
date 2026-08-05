"""Internal-only observation contracts for deterministic RAG certification."""
from __future__ import annotations


from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, Protocol
from uuid import UUID

if TYPE_CHECKING:
    from hospital_ai.services.retrieval import RetrievedChunk

EvaluationMode = Literal["rag_off", "hybrid_graph_off", "hybrid_graph_on"]


class GraphCertificationError(RuntimeError):
    """Raised when a required Graph RAG traversal cannot be certified."""


class EvidenceBindingError(ValueError):
    """Raised when logical benchmark evidence cannot resolve to indexed chunks."""


@dataclass(frozen=True)
class EvaluationControls:
    mode: EvaluationMode
    graph_required: bool
    run_id: str

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id must not be blank")
        if self.graph_required and self.mode != "hybrid_graph_on":
            raise ValueError("graph_required is valid only for hybrid_graph_on")

    @classmethod
    def rag_off(cls, run_id: str, *, graph_required: bool = False) -> EvaluationControls:
        return cls("rag_off", graph_required, run_id)

    @classmethod
    def hybrid_graph_off(cls, run_id: str, *, graph_required: bool = False) -> EvaluationControls:
        return cls("hybrid_graph_off", graph_required, run_id)

    @classmethod
    def hybrid_graph_on(cls, run_id: str, *, graph_required: bool = False) -> EvaluationControls:
        return cls("hybrid_graph_on", graph_required, run_id)


@dataclass(frozen=True)
class EvaluationSnapshot:
    candidate_chunk_ids: tuple[UUID, ...]
    authorized_chunk_ids: tuple[UUID, ...]
    selected_chunk_ids: tuple[UUID, ...]
    generator_context_chunk_ids: tuple[UUID, ...]
    graph_expanded_chunk_ids: tuple[UUID, ...]
    cited_chunk_ids: tuple[UUID, ...]
    selected_evidence_ids: tuple[UUID, ...]
    cited_evidence_ids: tuple[UUID, ...]
    graph_ran: bool

    @property
    def selected_context(self) -> tuple[UUID, ...]:
        return self.selected_chunk_ids


class EvaluationObserver(Protocol):
    def record_candidates(self, chunks: Sequence[RetrievedChunk]) -> None: ...

    def record_authorized_candidates(self, chunks: Sequence[RetrievedChunk]) -> None: ...

    def record_selected_context(self, chunks: Sequence[RetrievedChunk]) -> None: ...

    def record_generator_context(self, chunks: Sequence[RetrievedChunk]) -> None: ...

    def record_graph_execution(self) -> None: ...

    def record_graph_expanded(self, chunks: Sequence[RetrievedChunk]) -> None: ...

    def record_cited_chunks(self, chunks: Sequence[RetrievedChunk]) -> None: ...


def bind_indexed_evidence(evidence_ids: Sequence[UUID], chunk_ids: Sequence[UUID]) -> Mapping[UUID, UUID]:
    """Create a fail-closed chunk-to-logical-evidence binding."""
    if len(evidence_ids) != len(chunk_ids):
        raise EvidenceBindingError("Logical evidence remains unresolved in the indexed corpus")
    result: dict[UUID, UUID] = {}
    for evidence_id, chunk_id in zip(evidence_ids, chunk_ids, strict=True):
        existing = result.get(chunk_id)
        if existing is not None and existing != evidence_id:
            raise EvidenceBindingError("Indexed chunk maps to multiple logical evidence IDs")
        result[chunk_id] = evidence_id
    return MappingProxyType(result)


@dataclass
class InMemoryEvaluationObserver:
    logical_evidence_by_chunk: Mapping[UUID, UUID] = field(default_factory=dict)
    require_indexed: bool = False
    _candidates: list[UUID] = field(default_factory=list, init=False)
    _authorized: list[UUID] = field(default_factory=list, init=False)
    _selected: list[UUID] = field(default_factory=list, init=False)
    _generator_context: list[UUID] = field(default_factory=list, init=False)
    _graph_expanded: list[UUID] = field(default_factory=list, init=False)
    _cited: list[UUID] = field(default_factory=list, init=False)
    _graph_ran: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.logical_evidence_by_chunk = MappingProxyType(dict(self.logical_evidence_by_chunk))

    def record_candidates(self, chunks: Sequence[RetrievedChunk]) -> None:
        self._append_unique(self._candidates, chunks)

    def record_authorized_candidates(self, chunks: Sequence[RetrievedChunk]) -> None:
        self._append_unique(self._authorized, chunks)

    def record_selected_context(self, chunks: Sequence[RetrievedChunk]) -> None:
        self._require_bindings(chunks)
        self._selected = [chunk.chunk_id for chunk in chunks]

    def record_generator_context(self, chunks: Sequence[RetrievedChunk]) -> None:
        self._require_bindings(chunks)
        self._generator_context = [chunk.chunk_id for chunk in chunks]

    def record_graph_execution(self) -> None:
        self._graph_ran = True

    def record_graph_expanded(self, chunks: Sequence[RetrievedChunk]) -> None:
        self._append_unique(self._graph_expanded, chunks)

    def record_cited_chunks(self, chunks: Sequence[RetrievedChunk]) -> None:
        self._require_bindings(chunks)
        self._cited = [chunk.chunk_id for chunk in chunks]

    def snapshot(self) -> EvaluationSnapshot:
        return EvaluationSnapshot(
            candidate_chunk_ids=tuple(self._candidates),
            authorized_chunk_ids=tuple(self._authorized),
            selected_chunk_ids=tuple(self._selected),
            generator_context_chunk_ids=tuple(self._generator_context),
            graph_expanded_chunk_ids=tuple(self._graph_expanded),
            cited_chunk_ids=tuple(self._cited),
            selected_evidence_ids=self._logical_ids(self._selected),
            cited_evidence_ids=self._logical_ids(self._cited),
            graph_ran=self._graph_ran,
        )

    @staticmethod
    def _append_unique(target: list[UUID], chunks: Sequence[RetrievedChunk]) -> None:
        seen = set(target)
        for chunk in chunks:
            if chunk.chunk_id not in seen:
                target.append(chunk.chunk_id)
                seen.add(chunk.chunk_id)

    def _require_bindings(self, chunks: Sequence[RetrievedChunk]) -> None:
        if not self.require_indexed:
            return
        missing = [chunk.chunk_id for chunk in chunks if chunk.chunk_id not in self.logical_evidence_by_chunk]
        if missing:
            raise EvidenceBindingError(f"Selected indexed chunk has no logical evidence binding: {missing[0]}")

    def _logical_ids(self, chunk_ids: Sequence[UUID]) -> tuple[UUID, ...]:
        return tuple(
            self.logical_evidence_by_chunk[value] for value in chunk_ids if value in self.logical_evidence_by_chunk
        )
