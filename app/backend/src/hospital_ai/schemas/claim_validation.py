from typing import Any

from pydantic import BaseModel


class SentenceValidation(BaseModel):
    sentence: str
    claims: list[Any]
    passed: bool


class ClaimResult(BaseModel):
    claim: Any
    passed: bool
    reason: str | None = None

    @classmethod
    def failed(cls, claim, reason):
        return cls(claim=claim, passed=False, reason=reason)
