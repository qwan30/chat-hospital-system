import asyncio
import logging
from dataclasses import dataclass

from hospital_ai.core.config import get_settings

logger = logging.getLogger(__name__)

# Lazy imports for heavy ML dependencies (optional [guardrails] group)
try:
    from llm_guard import scan_output, scan_prompt
    from llm_guard.input_scanners import PromptInjection
    from llm_guard.output_scanners import Deanonymize
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
            return await asyncio.wait_for(
                asyncio.to_thread(self._scan_sync, prompt), timeout=get_settings().guardrail_timeout_seconds
            )
        except Exception as e:
            logger.warning("InputGuardrail scanner timed out or failed: %s", e)
            return GuardrailResult(blocked=True, reason="Safe refusal: Guardrail system unavailable or timed out")


class OutputGuardrail:
    """Scans generated answers before they reach the caller.

    `BanTopics(topics=["providing medical advice"], threshold=0.5)` used to lead
    this list and was removed after measurement, not on preference. It is a
    zero-shot topic classifier, so it scores *subject matter* rather than
    *speech act* -- and this assistant's entire purpose is to answer clinical
    questions from retrieved evidence. Measured scores on the real model:

        threshold 0.5   cited answer 1.000 (blocked) | unsafe advice 1.000 (blocked)
        threshold 0.85  cited answer 0.000 (allowed) | unsafe advice 0.000 (allowed)

    Identical scores for a properly-cited chart lookup and for "You should take
    500mg of paracetamol twice daily" -- the scanner cannot separate them at any
    threshold, so it was a blunt on/off switch carrying no safety signal. In the
    0.5 configuration it refused essentially every substantive clinical question
    on both /chat and /chat/stream; in the 0.85 configuration it would have
    passed the unsafe string too, which is worse than removal because it looks
    like a control.

    Grounding is enforced instead by citation validation, which is measurable
    and layered: services/reasoning.py rejects hallucinated evidence IDs, and
    services/chat.py plus api/routes/chat_stream.py independently reject answers
    with zero citations or IDs outside the retrieved set. The stream buffers the
    full answer before emitting any token, so those checks cannot be outrun.

    Deanonymize stays: it is the PHI leg of this scanner.
    """

    def __init__(self):
        if _LLM_GUARD_AVAILABLE:
            self.scanners = [Deanonymize(vault=Vault())]
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
            return await asyncio.wait_for(
                asyncio.to_thread(self._scan_sync, prompt, output),
                timeout=get_settings().guardrail_timeout_seconds,
            )
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


def warm_up_guardrails() -> bool:
    """Load the scanner models before the first real request.

    The guardrails are singletons that lazily construct their ML scanners, and
    the prompt-injection model takes ~5s to load from disk the first time. That
    exceeds the 3s scan timeout, and because the guardrail fails closed, the
    very first question after every server start was refused with a "security
    policy violation" -- even though the scanner ultimately judged it safe.

    Warming up on startup keeps the timeout (and the fail-closed posture) intact
    while removing the cold-start penalty. Returns True if the models are ready.
    """
    if not _LLM_GUARD_AVAILABLE or get_settings().disable_guardrails:
        return False
    try:
        # Constructing the singletons loads the models; a trivial scan forces
        # the tokenizer and pipeline to initialise too.
        get_input_guardrail()._scan_sync("warmup")
        get_output_guardrail()
        logger.info("Guardrail scanners warmed up")
        return True
    except Exception:
        # Never block startup on warm-up: the scan path still works (just cold),
        # and its own timeout plus fail-closed behaviour remain in force.
        logger.warning("Guardrail warm-up failed; first request may be slower", exc_info=True)
        return False


def get_output_guardrail() -> OutputGuardrail:
    global _output_guardrail_instance
    if _output_guardrail_instance is None:
        _output_guardrail_instance = OutputGuardrail()
    return _output_guardrail_instance
