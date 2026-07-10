"""Admin settings API — runtime-configurable RAG & LLM parameters.

Allows admin users to view and modify LLM/embedding/RAG settings
without restarting the server.  Persists overrides to the ``system_settings``
database table so they survive restarts.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_request_ip
from hospital_ai.core.config import Settings, get_settings
from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import User
from hospital_ai.db.session import get_session
from hospital_ai.db.settings_store import effective_value, get_all_overrides, upsert_many
from hospital_ai.services.audit import AuditService
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
    available_providers: list[str]


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
    streaming_enabled: bool | None = None
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dimensions: int | None = Field(None, ge=64, le=4096)
    openai_embedding_model: Optional[str] = None
    retrieval_top_k: int | None = Field(None, ge=1, le=50)
    evidence_threshold: float | None = Field(None, ge=0.0, le=1.0)
    chunk_size: int | None = Field(None, ge=64, le=4096)
    chunk_overlap: int | None = Field(None, ge=0, le=512)


# ── Routes ───────────────────────────────────────────────────────────


@router.get("", response_model=SettingsResponse)
async def get_admin_settings(
    request: Request,
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> SettingsResponse:
    """Return the current LLM, embedding, and RAG settings."""
    await _require_settings_role(
        request=request,
        session=session,
        current_user=current_user,
        action="settings.read",
        allowed_roles={"admin", "security"},
    )
    overrides = await get_all_overrides(session)
    manager = LLMManager(settings)

    def _ev(key: str) -> object:
        return effective_value(key, overrides, settings)

    return SettingsResponse(
        llm=LLMSettingsResponse(
            chat_provider=str(_ev("chat_provider")),
            chat_model=str(_ev("chat_model")),
            openai_chat_model=str(_ev("openai_chat_model")),
            openai_base_url=str(_ev("openai_base_url")),
            ollama_base_url=str(_ev("ollama_base_url")),
            system_prompt=str(_ev("system_prompt")),
            streaming_enabled=bool(_ev("streaming_enabled")),
            available_providers=manager.list_providers(),
        ),
        embedding=EmbeddingSettingsResponse(
            embedding_provider=str(_ev("embedding_provider")),
            embedding_model=str(_ev("embedding_model")),
            embedding_dimensions=int(_ev("embedding_dimensions")),  # type: ignore[arg-type]
            openai_embedding_model=str(_ev("openai_embedding_model")),
        ),
        rag=RAGSettingsResponse(
            retrieval_top_k=int(_ev("retrieval_top_k")),  # type: ignore[arg-type]
            evidence_threshold=float(_ev("evidence_threshold")),  # type: ignore[arg-type]
            chunk_size=int(_ev("chunk_size")),  # type: ignore[arg-type]
            chunk_overlap=int(_ev("chunk_overlap")),  # type: ignore[arg-type]
        ),
    )


@router.put("", response_model=SettingsResponse)
async def update_admin_settings(
    payload: SettingsUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> SettingsResponse:
    """Update configurable settings (admin only).

    Only non-null fields in the payload are applied as overrides.
    Changes are persisted to the ``system_settings`` database table.
    """
    await _require_settings_role(
        request=request,
        session=session,
        current_user=current_user,
        action="settings.update",
        allowed_roles={"admin"},
    )
    updates = payload.dict(exclude_none=True)
    if updates:
        await upsert_many(session, updates, user_id=current_user.id)

    return await get_admin_settings(
        request=request,
        current_user=current_user,
        settings=settings,
        session=session,
    )


async def _require_settings_role(
    *,
    request: Request,
    session: AsyncSession,
    current_user: User,
    action: str,
    allowed_roles: set[str],
) -> None:
    trace_id = new_trace_id()
    if current_user.role in allowed_roles:
        await AuditService(session).record(
            actor_user_id=current_user.id,
            action=action,
            object_type="system_setting",
            outcome="allowed",
            trace_id=trace_id,
            ip_address=get_request_ip(request),
            metadata={"role": current_user.role},
        )
        await session.commit()
        return
    await AuditService(session).record(
        actor_user_id=current_user.id,
        action=action,
        object_type="system_setting",
        outcome="denied",
        trace_id=trace_id,
        ip_address=get_request_ip(request),
        metadata={"role": current_user.role, "allowed_roles": sorted(allowed_roles)},
    )
    await session.commit()
    raise PermissionDeniedError("User is not authorized to manage system settings.")
