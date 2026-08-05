from __future__ import annotations

import uuid
from pydantic import BaseModel, ConfigDict, Field

class UploadSessionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    patient_id: uuid.UUID
    filename: str
    expected_size: int
    expected_sha256: str
    claimed_mime_type: str

class UploadSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    document_id: uuid.UUID
    upload_id: uuid.UUID
    object_key: str
    presigned_url: str | None = None
    required_headers: dict[str, str] = Field(default_factory=dict)
    state: str

class UploadFinalizeResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    document_id: uuid.UUID
    state: str

    @classmethod
    def from_row(cls, row: any) -> UploadFinalizeResult: # type: ignore
        return cls(id=row.id, document_id=row.document_id, state=row.state)
