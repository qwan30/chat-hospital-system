import json
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_session
from hospital_ai.core.errors import ConflictError
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import User
from hospital_ai.schemas.document_generations import (
    DocumentIndexGenerationRead,
    GenerationRollbackRead,
    GenerationRollbackRequest,
)
from hospital_ai.services.capabilities import CapabilityService, load_document_generation_aggregate
from hospital_ai.services.generations import GenerationService
from hospital_ai.services.idempotency import IdempotencyService
from hospital_ai.workers import generation_jobs

router = APIRouter()


def _dump_json(obj: any) -> str:
    if hasattr(obj, "model_dump_json"):
        return obj.model_dump_json()
    return obj.json()


def _from_orm(cls: any, obj: any) -> any:
    if hasattr(cls, "model_validate"):
        return cls.model_validate(obj)
    if hasattr(cls, "from_orm"):
        return cls.from_orm(obj)
    return cls.parse_obj(obj)


def _parse_obj(cls: any, obj: any) -> any:
    if hasattr(cls, "model_validate"):
        return cls.model_validate(obj)
    return cls.parse_obj(obj)


@router.post(
    "/{document_id}/index-generations/{generation_id}/rollback", response_model=GenerationRollbackRead, status_code=200
)
async def rollback_generation(
    document_id: uuid.UUID,
    generation_id: uuid.UUID,
    payload: GenerationRollbackRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> GenerationRollbackRead:
    aggregate = await load_document_generation_aggregate(
        session,
        document_id=document_id,
        generation_id=generation_id,
        actor=current_user,
        action="document_generation.rollback",
        trace_id=new_trace_id(),
    )
    document = aggregate.document
    await CapabilityService(session).require(
        user=current_user,
        patient_id=document.patient_id,
        capability="document_revision.restore",
        action="document_generation.rollback",
        trace_id=new_trace_id(),
        object_id=document_id,
    )

    idemp = IdempotencyService(session, current_user.id)
    req_str = _dump_json(payload)
    req_dict = json.loads(req_str)
    req_dict["target_generation_id"] = str(generation_id)
    decision = await idemp.begin(f"generation.rollback.{document_id}", idempotency_key, req_dict)
    if decision.is_in_progress:
        raise ConflictError("Request is already in progress; retry later.")
    if decision.is_replay:
        return _parse_obj(GenerationRollbackRead, decision.response_body)

    displaced_id = document.active_index_generation_id
    if not displaced_id or displaced_id != payload.expected_active_generation_id:
        await idemp.abort(decision.record_id)
        raise HTTPException(status_code=409, detail="Stale active pointer for rollback.")

    try:
        res = await GenerationService(session).rollback(
            document_id=document_id,
            target_generation_id=generation_id,
            actor_id=current_user.id,
            expected_active_generation_id=payload.expected_active_generation_id,
            reason=payload.reason,
            commit=False,
        )
    except ConflictError as exc:
        await idemp.abort(decision.record_id)
        raise HTTPException(status_code=409, detail=exc.message) from exc
    except ValueError as exc:
        await idemp.abort(decision.record_id)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response_model = GenerationRollbackRead(
        document_id=document_id,
        active_index_generation_id=res.active_generation_id,
        approved_revision_set_id=res.approved_revision_set_id,
        displaced_generation_id=displaced_id,
        target_generation_state="active",
        displaced_generation_state="superseded",
    )

    await idemp.complete(
        decision.record_id,
        200,
        json.loads(_dump_json(response_model)),
    )
    await session.commit()
    return response_model


@router.post(
    "/{document_id}/index-generations/{generation_id}/retry",
    response_model=DocumentIndexGenerationRead,
    status_code=202,
)
async def retry_generation(
    document_id: uuid.UUID,
    generation_id: uuid.UUID,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentIndexGenerationRead:
    aggregate = await load_document_generation_aggregate(
        session,
        document_id=document_id,
        generation_id=generation_id,
        actor=current_user,
        action="document_generation.retry",
        trace_id=new_trace_id(),
    )
    document = aggregate.document
    await CapabilityService(session).require(
        user=current_user,
        patient_id=document.patient_id,
        capability="document_revision.restore",
        action="document_generation.retry",
        trace_id=new_trace_id(),
        object_id=document_id,
    )

    idemp = IdempotencyService(session, current_user.id)
    decision = await idemp.begin(
        f"generation.retry.{document_id}:{generation_id}",
        idempotency_key,
        {"document_id": str(document_id), "generation_id": str(generation_id)},
    )
    if decision.is_in_progress:
        raise ConflictError("Request is already in progress; retry later.")
    if decision.is_replay:
        return _parse_obj(DocumentIndexGenerationRead, decision.response_body)

    try:
        new_gen = await GenerationService(session).retry(
            document_id=document_id,
            generation_id=generation_id,
            actor_id=current_user.id,
            commit=False,
        )
    except Exception:
        await idemp.abort(decision.record_id)
        raise

    response_model = _from_orm(DocumentIndexGenerationRead, new_gen)
    await idemp.complete(decision.record_id, 202, json.loads(_dump_json(response_model)))
    await session.commit()
    generation_jobs.enqueue_build_generation_job(new_gen.id)
    return response_model
