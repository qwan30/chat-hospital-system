import pytest

class DummyResult:
    def __init__(self, passed, evidence):
        self.passed = passed
        self.evidence = evidence

class DummyHarness:
    async def run(self, scenario: str) -> DummyResult:
        return DummyResult(passed=False, evidence=f"Not implemented: {scenario}")

@pytest.fixture
def cdi_v2_harness():
    return DummyHarness()
