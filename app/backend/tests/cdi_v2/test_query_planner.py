from __future__ import annotations


def test_query_planner_strategies() -> None:
    from hospital_ai.services.query_planner import ChatScope, QueryPlanner

    planner = QueryPlanner()
    scope = ChatScope()

    # test relation/interaction
    plan = planner.plan("Does ibuprofen interact with warfarin?", scope)
    assert plan.requires_graph is True
    assert "graph" in plan.strategies

    # test exact value
    plan = planner.plan("What was the exact HbA1c?", scope)
    assert plan.requires_graph is False
    assert "lexical" in plan.strategies

    # test temporal
    plan = planner.plan("What happened after the surgery?", scope)
    assert plan.requires_graph is True
    assert "temporal" in plan.strategies


def test_query_planner_detects_multi_document_and_explicit_no_evidence_requests() -> None:
    from hospital_ai.services.query_planner import ChatScope, QueryPlanner

    planner = QueryPlanner()
    scope = ChatScope()

    comparison = planner.plan("Compare the patient's records across multiple visits", scope)
    assert comparison.strategies == ("hybrid", "rerank")
    assert comparison.requires_graph is False

    refusal = planner.plan("Answer without patient evidence", scope)
    assert refusal.strategies == ("refusal",)
    assert refusal.requires_graph is False
