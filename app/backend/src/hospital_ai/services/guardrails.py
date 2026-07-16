"""LLM input/output safety guardrails service.
Dịch vụ kiểm soát an toàn (guardrails) cho dữ liệu đầu vào (prompt) và đầu ra (output) của LLM trong hệ thống y tế.
"""

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
    """Kết quả kiểm tra an toàn guardrail, gồm cờ `blocked` và lý do từ chối `reason` nếu bị chặn."""
    blocked: bool
    reason: str


def fallback_input_result(retry_state) -> GuardrailResult:
    """Hàm xử lý dự phòng khi kiểm tra đầu vào thất bại hoặc quá hạn thời gian (từ chối an toàn - safe refusal)."""
    logger.warning("InputGuardrail scanner failed or timed out: %s", retry_state.outcome.exception())
    return GuardrailResult(blocked=True, reason="Safe refusal: Guardrail system unavailable or timed out")


def fallback_output_result(retry_state) -> GuardrailResult:
    """Hàm xử lý dự phòng khi kiểm tra đầu ra thất bại hoặc quá hạn thời gian."""
    logger.warning("OutputGuardrail scanner failed or timed out: %s", retry_state.outcome.exception())
    return GuardrailResult(blocked=True, reason="Safe refusal: Guardrail system unavailable or timed out")


class InputGuardrail:
    """Scans incoming user prompts for safety risks such as prompt injections.
    Bộ quét kiểm tra an toàn cho câu hỏi đầu vào của người dùng, ngăn chặn tấn công tiêm nhiễm lệnh (prompt injection).
    """

    def __init__(self):
        """Khởi tạo danh sách bộ quét (PromptInjection) nếu thư viện llm_guard khả dụng."""
        if _LLM_GUARD_AVAILABLE:
            self.scanners = [PromptInjection(threshold=0.5)]
        else:
            self.scanners = []

    def _scan_sync(self, prompt: str) -> GuardrailResult:
        """Chạy quét prompt đồng bộ (synchronous) thông qua thư viện `llm_guard`."""
        if not _LLM_GUARD_AVAILABLE:
            return GuardrailResult(blocked=False, reason="")
        sanitized_prompt, results_valid, results_score = scan_prompt(self.scanners, prompt)
        is_blocked = not all(results_valid.values())
        reason = "Prompt injection detected" if is_blocked else ""
        return GuardrailResult(blocked=is_blocked, reason=reason)

    async def scan(self, prompt: str) -> GuardrailResult:
        """Thực hiện quét prompt bất đồng bộ với giới hạn thời gian (timeout) là 3 giây để đảm bảo độ trễ."""
        if get_settings().disable_guardrails or not _LLM_GUARD_AVAILABLE:
            return GuardrailResult(blocked=False, reason="")
        try:
            return await asyncio.wait_for(asyncio.to_thread(self._scan_sync, prompt), timeout=3.0)
        except Exception as e:
            logger.warning("InputGuardrail scanner timed out or failed: %s", e)
            return GuardrailResult(blocked=True, reason="Safe refusal: Guardrail system unavailable or timed out")


class OutputGuardrail:
    """Scans LLM generation outputs for restricted topics or sensitive data leakage.
    Bộ quét kiểm tra an toàn cho câu trả lời đầu ra của LLM, ngăn rò rỉ thông tin hoặc cung cấp chẩn đoán y tế sai lệnh.
    """

    def __init__(self):
        """Khởi tạo danh sách bộ quét đầu ra (BanTopics và Deanonymize) nếu llm_guard khả dụng."""
        if _LLM_GUARD_AVAILABLE:
            self.scanners = [BanTopics(topics=["providing medical advice"], threshold=0.5), Deanonymize(vault=Vault())]
        else:
            self.scanners = []

    def _scan_sync(self, prompt: str, output: str) -> GuardrailResult:
        """Chạy quét đồng bộ câu trả lời của LLM (kiểm tra chủ đề bị cấm và lộ thông tin cá nhân)."""
        if not _LLM_GUARD_AVAILABLE:
            return GuardrailResult(blocked=False, reason="")
        sanitized_output, results_valid, results_score = scan_output(self.scanners, prompt, output)
        is_blocked = not all(results_valid.values())
        reason = "Output blocked by guardrails" if is_blocked else ""
        return GuardrailResult(blocked=is_blocked, reason=reason)

    async def scan(self, prompt: str, output: str) -> GuardrailResult:
        """Thực hiện quét đầu ra bất đồng bộ với timeout 3 giây, hoàn trả safe refusal nếu vượt thời gian hoặc lỗi."""
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
    """Trả về instance singleton của InputGuardrail."""
    global _input_guardrail_instance
    if _input_guardrail_instance is None:
        _input_guardrail_instance = InputGuardrail()
    return _input_guardrail_instance


def get_output_guardrail() -> OutputGuardrail:
    """Trả về instance singleton của OutputGuardrail."""
    global _output_guardrail_instance
    if _output_guardrail_instance is None:
        _output_guardrail_instance = OutputGuardrail()
    return _output_guardrail_instance
