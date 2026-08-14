from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from hospital_ai.evaluation.llm_judge import LLMJudge, LLMJudgeScore


def test_llm_judge_stub_matching_terms():
    judge = LLMJudge(provider="stub")
    score = judge.evaluate(
        question="What is the Glucose level?",
        context="Patient Glucose is 110 mg/dL",
        answer="The patient Glucose level is 110 mg/dL.",
        verification_terms=("110 mg/dL", "Glucose"),
    )
    assert isinstance(score, LLMJudgeScore)
    assert score.faithfulness >= 0.9
    assert score.relevance >= 0.9
    assert "Fallback verification" in score.reasoning


def test_llm_judge_stub_non_matching_terms():
    judge = LLMJudge(provider="stub")
    score = judge.evaluate(
        question="What is the Glucose level?",
        context="Patient Glucose is 110 mg/dL",
        answer="The patient has normal blood pressure.",
        verification_terms=("110 mg/dL", "Glucose"),
    )
    assert isinstance(score, LLMJudgeScore)
    assert score.faithfulness == 0.0
    assert score.relevance == 0.0


def test_llm_judge_phi_redaction():
    judge = LLMJudge(provider="stub")
    with patch("hospital_ai.evaluation.llm_judge.redact_patient_phi") as mock_redact:
        mock_redact.side_effect = lambda t: t.replace("John Doe", "[PATIENT_NAME]")

        judge.evaluate(
            question="What is John Doe's diagnosis?",
            context="Patient John Doe has Diabetes.",
            answer="The patient has Diabetes.",
            verification_terms=("Diabetes",),
        )

        assert mock_redact.call_count >= 2


def test_llm_judge_key_rotation_on_429():
    keys = [
        "DUMMY_GEMINI_KEY_1",
        "DUMMY_GEMINI_KEY_2",
        "DUMMY_GEMINI_KEY_3",
        "DUMMY_GEMINI_KEY_4",
        "DUMMY_GEMINI_KEY_5",
        "DUMMY_GEMINI_KEY_6",
    ]
    judge = LLMJudge(provider="gemini", api_keys=keys)

    response_429 = MagicMock()
    response_429.status_code = 429

    response_200 = MagicMock()
    response_200.status_code = 200
    response_200.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": '{"faithfulness": 0.95, "relevance": 0.92, "reasoning": "High alignment"}'}]
                }
            }
        ]
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.side_effect = [response_429, response_200]

        score = judge.evaluate(
            question="What is the treatment?",
            context="Treatment is Insulin.",
            answer="The treatment is Insulin.",
        )

        assert score.faithfulness == 0.95
        assert score.relevance == 0.92
        assert score.reasoning == "High alignment"
        assert mock_post.call_count == 2
        # First call used keys[0]
        assert keys[0] in mock_post.call_args_list[0][0][0]
        # Second call used keys[1]
        assert keys[1] in mock_post.call_args_list[1][0][0]


def test_llm_judge_openai_compatible_provider_uses_explicit_endpoint():
    judge = LLMJudge(
        provider="openai",
        api_keys=["DUMMY_DEEPSEEK_KEY"],
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
    )
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "choices": [{"message": {"content": '{"faithfulness": 0.91, "relevance": 0.88, "reasoning": "Supported"}'}}]
    }

    with patch("httpx.Client.post", return_value=response) as mock_post:
        score = judge.evaluate(
            question="What is documented?",
            context="The synthetic record documents penicillin allergy.",
            answer="The record documents penicillin allergy.",
        )

    assert score.faithfulness == 0.91
    assert score.relevance == 0.88
    request_url = mock_post.call_args.args[0]
    request_headers = mock_post.call_args.kwargs["headers"]
    assert request_url == "https://api.deepseek.com/v1/chat/completions"
    assert request_headers == {"Authorization": "Bearer DUMMY_DEEPSEEK_KEY"}


def test_llm_judge_openai_without_key_fails_strict_live_lane():
    judge = LLMJudge(provider="openai", api_keys=[], model="deepseek-chat", strict=True)

    with pytest.raises(RuntimeError, match="credentials are missing"):
        judge.evaluate(
            question="What is documented?",
            context="The synthetic record documents penicillin allergy.",
            answer="The record documents penicillin allergy.",
            verification_terms=("penicillin",),
        )


def test_llm_judge_openai_provider_error_does_not_fallback_in_strict_lane():
    judge = LLMJudge(
        provider="openai",
        api_keys=["DUMMY_DEEPSEEK_KEY"],
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        strict=True,
    )
    response = MagicMock()
    response.raise_for_status.side_effect = httpx.HTTPError("synthetic provider failure")

    with patch("httpx.Client.post", return_value=response):
        with pytest.raises(RuntimeError, match="request failed"):
            judge.evaluate(
                question="What is documented?",
                context="Synthetic context.",
                answer="Synthetic answer.",
            )
