from __future__ import annotations
from dataclasses import dataclass


class ChatScope:
    pass


@dataclass
class RetrievalPlan:
    strategies: tuple[str, ...]
    scope: ChatScope
    requires_graph: bool


@dataclass
class QueryFeatures:
    no_patient_evidence: bool = False
    temporal: bool = False
    relation_or_interaction: bool = False
    exact_value_or_code: bool = False
    multi_document: bool = False


def classify_query(question: str) -> QueryFeatures:
    question = question.lower()
    return QueryFeatures(
        no_patient_evidence=False,
        temporal="after" in question or "before" in question or "when" in question,
        relation_or_interaction="interact" in question or "cause" in question,
        exact_value_or_code="exact" in question or "value" in question or "code" in question,
        multi_document=False,
    )


class QueryPlanner:
    def plan(self, question: str, scope: ChatScope) -> RetrievalPlan:
        features = classify_query(question)
        if features.no_patient_evidence:
            return RetrievalPlan(("refusal",), scope, requires_graph=False)
        if features.temporal:
            return RetrievalPlan(("temporal", "graph", "lexical"), scope, requires_graph=True)
        if features.relation_or_interaction:
            return RetrievalPlan(("graph", "hybrid"), scope, requires_graph=True)
        if features.exact_value_or_code:
            return RetrievalPlan(("lexical",), scope, requires_graph=False)
        if features.multi_document:
            return RetrievalPlan(("hybrid", "rerank"), scope, requires_graph=False)
        return RetrievalPlan(("hybrid",), scope, requires_graph=False)
