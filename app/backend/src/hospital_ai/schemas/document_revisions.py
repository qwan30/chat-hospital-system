from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DraftPageWrite(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    text: str
    parent_revision_id: uuid.UUID
    edit_reason: str = ""


class DraftPageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    page_revision_id: uuid.UUID
    lock_version: int
    page_number: int
    text: str
    status: str


class RevisionSetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    revision_set_id: uuid.UUID
    document_id: uuid.UUID
    revision_number: int
    status: str
    created_by_user_id: uuid.UUID
    created_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    approved_by_user_id: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None


class ApproveRevisionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    demo_mode: bool = False


class RejectRevisionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    reason: str = ""


class RestoreRevisionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    revision_id: uuid.UUID
    reason: str = ""


class GenerationAcceptedRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    generation_id: uuid.UUID
    state: str
