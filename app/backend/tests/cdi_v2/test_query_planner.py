from __future__ import annotations
import pytest

def test_query_planner_strategies() -> None:
    from hospital_ai.services.query_planner import QueryPlanner, ChatScope
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
