from pydantic import BaseModel, Field


class IdempotencyHeaders(BaseModel):
    idempotency_key: str = Field(..., alias="Idempotency-Key")
