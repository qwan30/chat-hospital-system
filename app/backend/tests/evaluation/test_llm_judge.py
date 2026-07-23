from __future__ import annotations

from unittest.mock import MagicMock, patch
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
                    "parts": [
                        {
                            "text": '{"faithfulness": 0.95, "relevance": 0.92, "reasoning": "High alignment"}'
                        }
                    ]
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
