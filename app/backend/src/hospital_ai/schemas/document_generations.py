from __future__ import annotations

import uuid
from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, constr


class GenerationRollbackRequest(BaseModel):
    expected_active_generation_id: uuid.UUID
    reason: constr(strip_whitespace=True, min_length=3, max_length=500)


class GenerationRollbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    class Config:
        orm_mode = True

    document_id: uuid.UUID
    active_index_generation_id: uuid.UUID
    approved_revision_set_id: uuid.UUID
    displaced_generation_id: uuid.UUID
    target_generation_state: Literal["active"] = "active"
    displaced_generation_state: Literal["superseded"] = "superseded"


class DocumentIndexGenerationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    class Config:
        orm_mode = True

    id: uuid.UUID
    document_id: uuid.UUID
    revision_set_id: uuid.UUID
    retry_of_generation_id: Optional[uuid.UUID] = None
    state: str
    revision_set_sha256: str
    generation_sha256: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    superseded_at: Optional[datetime] = None
    failure_code: Optional[str] = None
    failure_detail: Optional[str] = None
