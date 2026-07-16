import time
from collections.abc import AsyncIterator

from hospital_ai.core.telemetry import LLM_REQUEST_DURATION, LLM_TOKEN_USAGE
from hospital_ai.services.llm.base import BaseLLM, LLMMessage, LLMResponse


class InstrumentedLLM(BaseLLM):
    """Wraps a BaseLLM to provide OpenTelemetry metrics."""

    def __init__(self, inner: BaseLLM):
        self._inner = inner

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        start_time = time.perf_counter()

        try:
            response = await self._inner.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            duration = time.perf_counter() - start_time
            LLM_REQUEST_DURATION.labels(provider=self.provider_name(), model=self.model_name()).observe(duration)

            if response.usage:
                if "prompt_tokens" in response.usage:
                    LLM_TOKEN_USAGE.labels(
                        provider=self.provider_name(), model=self.model_name(), direction="prompt"
                    ).inc(response.usage["prompt_tokens"])
                if "completion_tokens" in response.usage:
                    LLM_TOKEN_USAGE.labels(
                        provider=self.provider_name(), model=self.model_name(), direction="completion"
                    ).inc(response.usage["completion_tokens"])

            return response
        except Exception:
            # We don't record duration on failure, or maybe we should?
            raise

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        # For streaming, we might not have usage data easily, but we can measure duration.
        start_time = time.perf_counter()

        try:
            async for chunk in self._inner.stream(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield chunk
        finally:
            duration = time.perf_counter() - start_time
            LLM_REQUEST_DURATION.labels(provider=self.provider_name(), model=self.model_name()).observe(duration)

    def provider_name(self) -> str:
        return self._inner.provider_name()

    def model_name(self) -> str:
        return self._inner.model_name()
