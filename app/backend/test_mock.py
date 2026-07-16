import asyncio
from unittest.mock import patch, MagicMock

class GuardrailsSim:
    _LLM_GUARD_AVAILABLE = False
    disable_guardrails = False
    
    def _scan_sync(self, prompt):
        if not self._LLM_GUARD_AVAILABLE:
            return "blocked"
        return self.scan_prompt(prompt)
        
    async def scan(self, prompt):
        if self.disable_guardrails or not self._LLM_GUARD_AVAILABLE:
            return "blocked early"
        return await asyncio.wait_for(asyncio.to_thread(self._scan_sync, prompt), timeout=3.0)

GuardrailsSim.scan_prompt = MagicMock()

async def run_test():
    with patch("__main__.GuardrailsSim._LLM_GUARD_AVAILABLE", True):
        with patch("__main__.GuardrailsSim.scan_prompt") as mock_scan:
            g = GuardrailsSim()
            res = await g.scan("hello")
            print("res:", res)
            print("called:", mock_scan.call_count)

asyncio.run(run_test())
