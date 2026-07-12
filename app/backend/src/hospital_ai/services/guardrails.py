import asyncio
import logging
from dataclasses import dataclass

from llm_guard import scan_output, scan_prompt
from llm_guard.input_scanners import PromptInjection
from llm_guard.output_scanners import BanTopics, Deanonymize
from llm_guard.vault import Vault
from tenacity import retry, stop_after_attempt

from hospital_ai.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class GuardrailResult:
    blocked: bool
    reason: str


def fallback_input_result(retry_state) -> GuardrailResult:
    logger.warning(f"InputGuardrail scanner failed or timed out: {retry_state.outcome.exception()}")
    return GuardrailResult(blocked=True, reason="Safe refusal: Guardrail system unavailable or timed out")


def fallback_output_result(retry_state) -> GuardrailResult:
    logger.warning(f"OutputGuardrail scanner failed or timed out: {retry_state.outcome.exception()}")
    return GuardrailResult(blocked=True, reason="Safe refusal: Guardrail system unavailable or timed out")


class InputGuardrail:
    def __init__(self):
        self.scanners = [PromptInjection(threshold=0.5)]

    @retry(stop=stop_after_attempt(2), retry_error_callback=fallback_input_result)
    def _scan_sync(self, prompt: str) -> GuardrailResult:
        sanitized_prompt, results_valid, results_score = scan_prompt(self.scanners, prompt)

        is_blocked = not all(results_valid.values())
        reason = "Prompt injection detected" if is_blocked else ""
        return GuardrailResult(blocked=is_blocked, reason=reason)

    async def scan(self, prompt: str) -> GuardrailResult:
        if get_settings().disable_guardrails:
            return GuardrailResult(blocked=False, reason="")
        try:
            return await asyncio.wait_for(asyncio.to_thread(self._scan_sync, prompt), timeout=3.0)
        except asyncio.TimeoutError:
            logger.warning("InputGuardrail scanner timed out")
            return GuardrailResult(blocked=True, reason="Safe refusal: Guardrail system unavailable or timed out")


class OutputGuardrail:
    def __init__(self):
        self.scanners = [BanTopics(topics=["providing medical advice"], threshold=0.5), Deanonymize(vault=Vault())]

    @retry(stop=stop_after_attempt(2), retry_error_callback=fallback_output_result)
    def _scan_sync(self, prompt: str, output: str) -> GuardrailResult:
        sanitized_output, results_valid, results_score = scan_output(self.scanners, prompt, output)

        is_blocked = not all(results_valid.values())
        reason = "Output blocked by guardrails" if is_blocked else ""
        return GuardrailResult(blocked=is_blocked, reason=reason)

    async def scan(self, prompt: str, output: str) -> GuardrailResult:
        if get_settings().disable_guardrails:
            return GuardrailResult(blocked=False, reason="")
        try:
            return await asyncio.wait_for(asyncio.to_thread(self._scan_sync, prompt, output), timeout=3.0)
        except asyncio.TimeoutError:
            logger.warning("OutputGuardrail scanner timed out")
            return GuardrailResult(blocked=True, reason="Safe refusal: Guardrail system unavailable or timed out")


_input_guardrail_instance = None
_output_guardrail_instance = None


def get_input_guardrail() -> InputGuardrail:
    global _input_guardrail_instance
    if _input_guardrail_instance is None:
        _input_guardrail_instance = InputGuardrail()
    return _input_guardrail_instance


def get_output_guardrail() -> OutputGuardrail:
    global _output_guardrail_instance
    if _output_guardrail_instance is None:
        _output_guardrail_instance = OutputGuardrail()
    return _output_guardrail_instance
