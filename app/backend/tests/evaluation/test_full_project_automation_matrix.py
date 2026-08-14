"""Executable contract inventory for the full-project automation plan.

The matrix is intentionally deterministic: it verifies that every planned
chatbot quality case has an ID, a category, and at least one enforceable
contract. Product behavior is exercised by the adapter/route tests referenced
by the plan; this file prevents the 50-case scope from silently shrinking.
"""

from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class ChatScenario:
    case_id: str
    category: str
    prompt_shape: str
    contracts: tuple[str, ...]
    status: str = "NOT RUN"
    test_refs: tuple[str, ...] = ()


_CONTRACTS = {
    "usefulness",
    "citation",
    "authorization",
    "safe_refusal",
    "audit",
    "trace",
    "sse_order",
    "abort",
    "sanitized_error",
    "determinism",
    "provider_config",
}


def _scenario(case_id: str, category: str, prompt_shape: str, *contracts: str) -> ChatScenario:
    return ChatScenario(case_id, category, prompt_shape, contracts)


CHATBOT_50_SCENARIOS = (
    # Single-hop usefulness: C01-C10
    _scenario("C01", "single_hop_usefulness", "exact patient fact", "usefulness", "citation"),
    _scenario("C02", "single_hop_usefulness", "medication instruction", "usefulness", "citation"),
    _scenario("C03", "single_hop_usefulness", "appointment date", "usefulness", "citation"),
    _scenario("C04", "single_hop_usefulness", "lab value and unit", "usefulness", "citation"),
    _scenario("C05", "single_hop_usefulness", "supported definition", "usefulness", "citation"),
    _scenario("C06", "single_hop_usefulness", "irrelevant retrieved chunk", "usefulness", "citation"),
    _scenario("C07", "single_hop_usefulness", "duplicate supporting chunks", "usefulness", "determinism"),
    _scenario("C08", "single_hop_usefulness", "conflicting dated records", "usefulness", "citation"),
    _scenario("C09", "single_hop_usefulness", "scoped patient summary", "usefulness", "citation"),
    _scenario("C10", "single_hop_usefulness", "thread follow-up", "usefulness", "authorization"),
    # Safe refusal and permission: C11-C20
    _scenario("C11", "safe_refusal_permission", "missing patient permission", "authorization", "safe_refusal"),
    _scenario("C12", "safe_refusal_permission", "wrong organization", "authorization", "safe_refusal"),
    _scenario("C13", "safe_refusal_permission", "permission revoked after retrieval", "authorization", "audit"),
    _scenario("C14", "safe_refusal_permission", "expired permission", "authorization", "audit"),
    _scenario("C15", "safe_refusal_permission", "soft-deleted document", "authorization", "safe_refusal"),
    _scenario("C16", "safe_refusal_permission", "mismatched ownership join", "authorization", "safe_refusal"),
    _scenario("C17", "safe_refusal_permission", "no retrieval evidence", "safe_refusal", "citation"),
    _scenario("C18", "safe_refusal_permission", "below relevance threshold", "safe_refusal", "determinism"),
    _scenario("C19", "safe_refusal_permission", "another patient by name", "authorization", "safe_refusal"),
    _scenario("C20", "safe_refusal_permission", "ignore access policy injection", "authorization", "safe_refusal"),
    # GraphRAG and multi-hop: C21-C30
    _scenario("C21", "graphrag_multi_hop", "patient to diagnosis", "authorization", "citation"),
    _scenario("C22", "graphrag_multi_hop", "patient encounter document", "authorization", "citation"),
    _scenario("C23", "graphrag_multi_hop", "over-limit traversal", "authorization", "safe_refusal"),
    _scenario("C24", "graphrag_multi_hop", "empty authorized graph", "determinism", "safe_refusal"),
    _scenario("C25", "graphrag_multi_hop", "deleted related entity", "authorization", "safe_refusal"),
    _scenario("C26", "graphrag_multi_hop", "out-of-scope entity", "authorization", "safe_refusal"),
    _scenario("C27", "graphrag_multi_hop", "mismatched edge", "authorization", "safe_refusal"),
    _scenario("C28", "graphrag_multi_hop", "entity without source", "citation", "safe_refusal"),
    _scenario("C29", "graphrag_multi_hop", "graph-document conflict", "citation", "usefulness"),
    _scenario("C30", "graphrag_multi_hop", "graph plus vector retrieval", "authorization", "citation"),
    # SSE, transport, and thread behavior: C31-C40
    _scenario("C31", "sse_transport_thread", "normal streaming answer", "sse_order", "citation"),
    _scenario("C32", "sse_transport_thread", "client abort during retrieval", "abort", "audit"),
    _scenario("C33", "sse_transport_thread", "client abort during provider stream", "abort", "audit"),
    _scenario("C34", "sse_transport_thread", "provider timeout", "sanitized_error", "trace"),
    _scenario("C35", "sse_transport_thread", "provider rate limit", "sanitized_error", "determinism"),
    _scenario("C36", "sse_transport_thread", "malformed provider chunk", "sanitized_error", "safe_refusal"),
    _scenario("C37", "sse_transport_thread", "invalid citation output", "citation", "safe_refusal"),
    _scenario("C38", "sse_transport_thread", "stream/non-stream parity", "sse_order", "citation"),
    _scenario("C39", "sse_transport_thread", "concurrent same-user requests", "determinism", "authorization"),
    _scenario("C40", "sse_transport_thread", "follow-up after refusal", "authorization", "safe_refusal"),
    # Adversarial quality/provider behavior: C41-C50
    _scenario("C41", "adversarial_provider", "retrieved prompt injection", "authorization", "safe_refusal"),
    _scenario("C42", "adversarial_provider", "user prompt injection", "authorization", "safe_refusal"),
    _scenario("C43", "adversarial_provider", "HTML/script document content", "sanitized_error", "citation"),
    _scenario("C44", "adversarial_provider", "out-of-scope PHI request", "authorization", "audit"),
    _scenario("C45", "adversarial_provider", "oversized context", "determinism", "safe_refusal"),
    _scenario("C46", "adversarial_provider", "empty question", "safe_refusal", "determinism"),
    _scenario("C47", "adversarial_provider", "unsupported language", "usefulness", "safe_refusal"),
    _scenario("C48", "adversarial_provider", "hallucinated citation", "citation", "safe_refusal"),
    _scenario("C49", "adversarial_provider", "explicit DeepSeek lane", "provider_config", "audit"),
    _scenario(
        "C50", "adversarial_provider", "Gemini unavailable without hidden fallback", "provider_config", "safe_refusal"
    ),
)

_SCENARIO_EVIDENCE = {
    "C01": (
        "PARTIAL",
        (
            "evaluation/test_product_retrieval_adapter.py::test_chat_adapter_returns_actual_cited_source_backed_evidence",
        ),
    ),
    "C11": (
        "PARTIAL",
        (
            "evaluation/test_product_retrieval_adapter.py::test_chat_adapter_refuses_an_actor_without_patient_permission",
        ),
    ),
    "C21": (
        "PARTIAL",
        (
            "evaluation/test_product_retrieval_adapter.py::test_graph_adapter_traverses_real_graph_without_cross_patient_evidence",
        ),
    ),
}
CHATBOT_50_SCENARIOS = tuple(
    ChatScenario(
        scenario.case_id,
        scenario.category,
        scenario.prompt_shape,
        scenario.contracts,
        status=_SCENARIO_EVIDENCE.get(scenario.case_id, ("NOT RUN", ()))[0],
        test_refs=_SCENARIO_EVIDENCE.get(scenario.case_id, ("NOT RUN", ()))[1],
    )
    for scenario in CHATBOT_50_SCENARIOS
)


def test_chatbot_matrix_has_exactly_fifty_unique_cases() -> None:
    ids = [scenario.case_id for scenario in CHATBOT_50_SCENARIOS]
    assert ids == [f"C{number:02d}" for number in range(1, 51)]
    assert len(set(ids)) == 50
    assert {scenario.category for scenario in CHATBOT_50_SCENARIOS} == {
        "single_hop_usefulness",
        "safe_refusal_permission",
        "graphrag_multi_hop",
        "sse_transport_thread",
        "adversarial_provider",
    }


@pytest.mark.parametrize("scenario", CHATBOT_50_SCENARIOS, ids=lambda scenario: scenario.case_id)
def test_each_chatbot_case_declares_enforceable_contracts(scenario: ChatScenario) -> None:
    assert scenario.prompt_shape
    assert scenario.contracts
    assert set(scenario.contracts).issubset(_CONTRACTS)


def test_chatbot_case_statuses_never_overstate_runtime_coverage() -> None:
    assert {scenario.status for scenario in CHATBOT_50_SCENARIOS} == {"NOT RUN", "PARTIAL"}
    assert all(scenario.test_refs for scenario in CHATBOT_50_SCENARIOS if scenario.status == "PARTIAL")
    assert not any(scenario.status == "PASS" for scenario in CHATBOT_50_SCENARIOS)


def test_provider_configuration_contract_is_explicit_and_openai_compatible() -> None:
    from hospital_ai.core.config import Settings
    from hospital_ai.services.llm.manager import LLMManager

    settings = Settings(
        chat_provider="openai",
        openai_api_key="ephemeral-test-key",
        openai_base_url="https://api.deepseek.com/v1",
        openai_chat_model="deepseek-chat",
    )
    manager = LLMManager(settings)
    provider = manager.get()

    assert provider.provider_name() == "openai"
    assert provider.model_name() == "deepseek-chat"
    assert manager.get("gemini").provider_name() == "gemini"


def test_missing_gemini_key_does_not_change_explicit_openai_selection() -> None:
    from hospital_ai.core.config import Settings
    from hospital_ai.services.llm.manager import LLMManager

    manager = LLMManager(
        Settings(
            chat_provider="openai",
            openai_base_url="https://api.deepseek.com/v1",
            openai_chat_model="deepseek-chat",
            openai_api_key="",
            gemini_api_key="",
        )
    )

    assert manager.get().provider_name() == "openai"
    assert manager.get().model_name() == "deepseek-chat"
