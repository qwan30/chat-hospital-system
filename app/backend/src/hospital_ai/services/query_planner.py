from __future__ import annotations

import re
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
    question = question.casefold()
    return QueryFeatures(
        no_patient_evidence=bool(
            re.search(r"\bwithout\s+(?:patient\s+)?evidence\b|\bno\s+patient\s+evidence\b", question)
        ),
        temporal=bool(re.search(r"\b(after|before|when|during|timeline|history)\b", question)),
        relation_or_interaction=bool(
            re.search(r"\b(interact|interaction|cause|caused|relationship|related)\b", question)
        ),
        exact_value_or_code=bool(re.search(r"\b(exact|value|code|dose|number|date)\b", question)),
        multi_document=bool(re.search(r"\b(compare|between|across|multiple|both|each|trend)\b", question)),
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
