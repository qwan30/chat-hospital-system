from __future__ import annotations
from typing import Optional
"""Gemini and Local LLM Judge engine with API Key Rotation for Chat Evaluation Harness."""


import json
import os
import re
from collections.abc import Sequence

import httpx
from pydantic import BaseModel, Field

from hospital_ai.evaluation.phi_redactor import redact_patient_phi


def _load_env_gemini_keys() -> list[str]:
    raw = os.getenv("GEMINI_API_KEYS", "")
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    single_key = os.getenv("GEMINI_API_KEY")
    if single_key and single_key not in keys:
        keys.insert(0, single_key)
    return keys


class LLMJudgeScore(BaseModel):
    """Evaluation output score from LLM Judge."""

    faithfulness: float = Field(ge=0.0, le=1.0, description="Faithfulness of answer to context")
    relevance: float = Field(ge=0.0, le=1.0, description="Relevance of answer to question")
    reasoning: str = Field(description="Explanation of evaluation score")


class LLMJudge:
    """LLM Judge evaluator supporting Gemini, Local Ollama, and Stub modes."""

    def __init__(
        self,
        provider: str = "stub",
        api_keys: Optional[Sequence[str]] = None,
        model: str = "gemini-2.0-flash",
        base_url: Optional[str] = None,
    ) -> None:
        self.provider = provider.lower()
        self.model = model
        self.base_url = base_url or "http://localhost:11434"

        # Assemble API key pool for Gemini
        if api_keys is not None:
            self.api_keys = list(api_keys)
        else:
            self.api_keys = _load_env_gemini_keys()

        self._key_index = 0

    def _get_current_key(self) -> str:
        if not self.api_keys:
            return ""
        return self.api_keys[self._key_index % len(self.api_keys)]

    def _rotate_key(self) -> str:
        if not self.api_keys:
            return ""
        self._key_index = (self._key_index + 1) % len(self.api_keys)
        return self.api_keys[self._key_index]

    def evaluate(
        self,
        question: str,
        context: str,
        answer: str,
        verification_terms: tuple[str, ...] = (),
    ) -> LLMJudgeScore:
        """Evaluate chatbot answer against question and context."""
        # 1. Redact HIPAA PHI from input context and question before building prompt
        redacted_context = redact_patient_phi(context)
        redacted_question = redact_patient_phi(question)

        # 2. Stub or fallback provider
        if self.provider == "stub" or not self.api_keys:
            return self._evaluate_stub(redacted_question, redacted_context, answer, verification_terms)

        # 3. Gemini provider with key rotation
        if self.provider == "gemini":
            return self._evaluate_gemini(redacted_question, redacted_context, answer, verification_terms)

        # 4. Local provider (Ollama or local OpenAI-compatible endpoint)
        if self.provider == "local":
            return self._evaluate_local(redacted_question, redacted_context, answer, verification_terms)

        # Default fallback
        return self._evaluate_stub(redacted_question, redacted_context, answer, verification_terms)

    def _evaluate_stub(
        self,
        question: str,
        context: str,
        answer: str,
        verification_terms: tuple[str, ...],
    ) -> LLMJudgeScore:
        """Evaluate using deterministic verification terms matching."""
        if not verification_terms:
            return LLMJudgeScore(
                faithfulness=1.0,
                relevance=1.0,
                reasoning="Fallback verification terms matching (no terms required)",
            )

        matched = sum(1 for term in verification_terms if term.casefold() in answer.casefold())
        total = len(verification_terms)
        score_val = matched / total if total > 0 else 1.0

        return LLMJudgeScore(
            faithfulness=score_val,
            relevance=score_val,
            reasoning=f"Fallback verification terms matching ({matched}/{total} terms matched)",
        )

    def _evaluate_gemini(
        self,
        question: str,
        context: str,
        answer: str,
        verification_terms: tuple[str, ...],
    ) -> LLMJudgeScore:
        """Evaluate using Gemini API with key rotation on 429 rate limit."""
        prompt = (
            "You are a strict medical AI evaluation judge. "
            "Evaluate the chatbot answer based on the provided clinical context and user question.\n\n"
            f"Question:\n{question}\n\n"
            f"Context:\n{context}\n\n"
            f"Answer:\n{answer}\n\n"
            "Return ONLY a JSON object matching this schema:\n"
            "{\n"
            '  "faithfulness": <float 0.0 to 1.0 - degree to which answer is grounded in context>,\n'
            '  "relevance": <float 0.0 to 1.0 - degree to which answer directly addresses question>,\n'
            '  "reasoning": "<brief justification>"\n'
            "}"
        )

        attempts = 0
        max_attempts = len(self.api_keys)

        while attempts < max_attempts:
            key = self._get_current_key()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={key}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.0},
            }

            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.post(url, json=payload)

                if resp.status_code == 429:
                    self._rotate_key()
                    attempts += 1
                    continue

                resp.raise_for_status()
                data = resp.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                score = self._parse_json_score(text)
                if score is not None:
                    return score

                # If JSON parsing failed, fallback
                break

            except httpx.HTTPError:
                self._rotate_key()
                attempts += 1
            except Exception:
                break

        # Fallback if all Gemini API attempts failed
        return self._evaluate_stub(question, context, answer, verification_terms)

    def _evaluate_local(
        self,
        question: str,
        context: str,
        answer: str,
        verification_terms: tuple[str, ...],
    ) -> LLMJudgeScore:
        """Evaluate using Local Ollama LLM endpoint."""
        prompt = (
            "You are a strict medical AI evaluation judge. "
            "Evaluate the chatbot answer based on the provided clinical context and user question.\n\n"
            f"Question:\n{question}\n\n"
            f"Context:\n{context}\n\n"
            f"Answer:\n{answer}\n\n"
            "Return ONLY a JSON object with keys faithfulness (0.0-1.0), relevance (0.0-1.0), and reasoning."
        )

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model if self.model != "gemini-2.0-flash" else "llama3",
            "prompt": prompt,
            "stream": False,
        }

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                text = data.get("response", "")
                score = self._parse_json_score(text)
                if score is not None:
                    return score
        except Exception:
            pass

        return self._evaluate_stub(question, context, answer, verification_terms)

    def _parse_json_score(self, text: str) -> Optional[LLMJudgeScore]:
        """Extract and parse LLMJudgeScore from model response text."""
        try:
            # Strip markdown code fences if present
            cleaned = text.strip()
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
            else:
                json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if json_match:
                    cleaned = json_match.group(0)

            data = json.loads(cleaned)
            return LLMJudgeScore(
                faithfulness=float(data.get("faithfulness", 0.0)),
                relevance=float(data.get("relevance", 0.0)),
                reasoning=str(data.get("reasoning", "Parsed from LLM response")),
            )
        except Exception:
            return None
