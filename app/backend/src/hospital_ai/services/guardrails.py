import asyncio
import logging
from dataclasses import dataclass

from hospital_ai.core.config import get_settings

logger = logging.getLogger(__name__)

# Lazy imports for heavy ML dependencies (optional [guardrails] group)
try:
    from llm_guard import scan_output, scan_prompt
    from llm_guard.input_scanners import PromptInjection
    from llm_guard.output_scanners import BanTopics, Deanonymize
    from llm_guard.vault import Vault

    _LLM_GUARD_AVAILABLE = True
except ImportError:
    _LLM_GUARD_AVAILABLE = False
    logger.info("llm-guard not installed — guardrails will be disabled at runtime")


@dataclass
class GuardrailResult:
    blocked: bool
    reason: str


def fallback_input_result(retry_state) -> GuardrailResult:
    logger.warning("InputGuardrail scanner failed or timed out: %s", retry_state.outcome.exception())
    return GuardrailResult(blocked=True, reason="Safe refusal: Guardrail system unavailable or timed out")


def fallback_output_result(retry_state) -> GuardrailResult:
    logger.warning("OutputGuardrail scanner failed or timed out: %s", retry_state.outcome.exception())
    return GuardrailResult(blocked=True, reason="Safe refusal: Guardrail system unavailable or timed out")


class InputGuardrail:
    def __init__(self):
        if _LLM_GUARD_AVAILABLE:
            self.scanners = [PromptInjection(threshold=0.5)]
        else:
            self.scanners = []

    def _scan_sync(self, prompt: str) -> GuardrailResult:
        if not _LLM_GUARD_AVAILABLE:
            return GuardrailResult(blocked=False, reason="")
        sanitized_prompt, results_valid, results_score = scan_prompt(self.scanners, prompt)
        is_blocked = not all(results_valid.values())
        reason = "Prompt injection detected" if is_blocked else ""
        return GuardrailResult(blocked=is_blocked, reason=reason)

    async def scan(self, prompt: str) -> GuardrailResult:
        if get_settings().disable_guardrails or not _LLM_GUARD_AVAILABLE:
            return GuardrailResult(blocked=False, reason="")
        try:
            return await asyncio.wait_for(asyncio.to_thread(self._scan_sync, prompt), timeout=3.0)
        except Exception as e:
            logger.warning("InputGuardrail scanner timed out or failed: %s", e)
            return GuardrailResult(blocked=True, reason="Safe refusal: Guardrail system unavailable or timed out")


class OutputGuardrail:
    def __init__(self):
        if _LLM_GUARD_AVAILABLE:
            self.scanners = [BanTopics(topics=["providing medical advice"], threshold=0.5), Deanonymize(vault=Vault())]
        else:
            self.scanners = []

    def _scan_sync(self, prompt: str, output: str) -> GuardrailResult:
        if not _LLM_GUARD_AVAILABLE:
            return GuardrailResult(blocked=False, reason="")
        sanitized_output, results_valid, results_score = scan_output(self.scanners, prompt, output)
        is_blocked = not all(results_valid.values())
        reason = "Output blocked by guardrails" if is_blocked else ""
        return GuardrailResult(blocked=is_blocked, reason=reason)

    async def scan(self, prompt: str, output: str) -> GuardrailResult:
        if get_settings().disable_guardrails or not _LLM_GUARD_AVAILABLE:
            return GuardrailResult(blocked=False, reason="")
        try:
            return await asyncio.wait_for(asyncio.to_thread(self._scan_sync, prompt, output), timeout=3.0)
        except Exception as e:
            logger.warning("OutputGuardrail scanner timed out or failed: %s", e)
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
