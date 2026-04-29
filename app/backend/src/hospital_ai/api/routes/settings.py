"""Admin settings API — runtime-configurable RAG & LLM parameters.

Allows admin users to view and modify LLM/embedding/RAG settings
without restarting the server.  Persists to an in-memory snapshot
(production would use a DB or config store).
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from hospital_ai.api.deps import get_current_user
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.db.models import User
from hospital_ai.services.llm.manager import LLMManager

router = APIRouter()


# ── Response / Request schemas ──────────────────────────────────────────


class LLMSettingsResponse(BaseModel):
    chat_provider: str
    chat_model: str
    openai_chat_model: str
    openai_base_url: str
    ollama_base_url: str
    system_prompt: str
    streaming_enabled: bool
    available_providers: List[str]


class EmbeddingSettingsResponse(BaseModel):
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    openai_embedding_model: str


class RAGSettingsResponse(BaseModel):
    retrieval_top_k: int
    evidence_threshold: float
    chunk_size: int
    chunk_overlap: int


class SettingsResponse(BaseModel):
    llm: LLMSettingsResponse
    embedding: EmbeddingSettingsResponse
    rag: RAGSettingsResponse


class SettingsUpdateRequest(BaseModel):
    chat_provider: Optional[str] = None
    chat_model: Optional[str] = None
    openai_chat_model: Optional[str] = None
    openai_base_url: Optional[str] = None
    ollama_base_url: Optional[str] = None
    system_prompt: Optional[str] = None
    streaming_enabled: Optional[bool] = None
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dimensions: Optional[int] = Field(None, ge=64, le=4096)
    openai_embedding_model: Optional[str] = None
    retrieval_top_k: Optional[int] = Field(None, ge=1, le=50)
    evidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    chunk_size: Optional[int] = Field(None, ge=64, le=4096)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=512)


# ── In-memory overrides (production: persist to DB) ──────────────────


_overrides: dict = {}


def _effective_value(field: str, settings: Settings) -> object:
    """Return the override if set, else the default from env/settings."""
    if field in _overrides:
        return _overrides[field]
    return getattr(settings, field)


# ── Routes ───────────────────────────────────────────────────────────


@router.get("", response_model=SettingsResponse)
async def get_admin_settings(
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> SettingsResponse:
    """Return the current LLM, embedding, and RAG settings."""
    manager = LLMManager(settings)

    return SettingsResponse(
        llm=LLMSettingsResponse(
            chat_provider=str(_effective_value("chat_provider", settings)),
            chat_model=str(_effective_value("chat_model", settings)),
            openai_chat_model=str(_effective_value("openai_chat_model", settings)),
            openai_base_url=str(_effective_value("openai_base_url", settings)),
            ollama_base_url=str(_effective_value("ollama_base_url", settings)),
            system_prompt=str(_effective_value("system_prompt", settings)),
            streaming_enabled=bool(_effective_value("streaming_enabled", settings)),
            available_providers=manager.list_providers(),
        ),
        embedding=EmbeddingSettingsResponse(
            embedding_provider=str(_effective_value("embedding_provider", settings)),
            embedding_model=str(_effective_value("embedding_model", settings)),
            embedding_dimensions=int(_effective_value("embedding_dimensions", settings)),  # type: ignore[arg-type]
            openai_embedding_model=str(_effective_value("openai_embedding_model", settings)),
        ),
        rag=RAGSettingsResponse(
            retrieval_top_k=int(_effective_value("retrieval_top_k", settings)),  # type: ignore[arg-type]
            evidence_threshold=float(_effective_value("evidence_threshold", settings)),  # type: ignore[arg-type]
            chunk_size=int(_effective_value("chunk_size", settings)),  # type: ignore[arg-type]
            chunk_overlap=int(_effective_value("chunk_overlap", settings)),  # type: ignore[arg-type]
        ),
    )


@router.put("", response_model=SettingsResponse)
async def update_admin_settings(
    payload: SettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> SettingsResponse:
    """Update configurable settings (admin only).

    Only non-null fields in the payload are applied as overrides.
    """
    updates = payload.dict(exclude_none=True)
    _overrides.update(updates)

    return await get_admin_settings(current_user=current_user, settings=settings)
