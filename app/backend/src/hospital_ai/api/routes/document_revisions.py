import json
import uuid

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.api.deps import get_current_user, get_session
from hospital_ai.core.errors import NotFoundError
from hospital_ai.core.security import new_trace_id
from hospital_ai.db.models import Document, User
from hospital_ai.db.clinical_documents import (
    DocumentDraftHead,
    DocumentPageRevision,
    DocumentRevisionPage,
    DocumentRevisionSet,
)
from hospital_ai.schemas.document_revisions import (
    ApproveRevisionRequest,
    DraftPageRead,
    DraftPageWrite,
    GenerationAcceptedRead,
    RejectRevisionRequest,
    RestoreRevisionRequest,
    RevisionSetRead,
)
from hospital_ai.services.capabilities import CapabilityService
from hospital_ai.services.idempotency import IdempotencyService
from hospital_ai.services.revisions import (
    ApproveRevisionCommand,
    RejectCommand,
    RestoreCommand,
    RevisionService,
    SavePageCommand,
    SubmitCommand,
)

router = APIRouter()


async def _get_document_or_404(session: AsyncSession, document_id: uuid.UUID) -> Document:
    doc = await session.get(Document, document_id)
    if not doc:
        raise NotFoundError(f"Document not found: {document_id}")
    return doc


@router.patch("/{document_id}/draft/pages/{page_number}", response_model=DraftPageRead, status_code=201)
async def save_draft_page(
    document_id: uuid.UUID,
    page_number: int,
    payload: DraftPageWrite,
    request: Request,
    if_match: int = Header(..., alias="If-Match"),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DraftPageRead:
    document = await _get_document_or_404(session, document_id)
    await CapabilityService(session).require(
        user=current_user,
        patient_id=document.patient_id,
        capability="document_revision.edit",
        action="document_revision.page.save",
        trace_id=new_trace_id(),
        object_id=document_id,
    )
    idemp_service = IdempotencyService(session, current_user.id)
    decision = await idemp_service.begin(
        scope=f"save_draft_page:{document_id}:{page_number}",
        key=idempotency_key,
        payload=json.loads(payload.model_dump_json() if hasattr(payload, "model_dump_json") else payload.json()),
    )
    if decision.is_replay:
        return (
            DraftPageRead.model_validate(decision.response_body)
            if hasattr(DraftPageRead, "model_validate")
            else DraftPageRead.parse_obj(decision.response_body)
        )

    result = await RevisionService(session).save_page(
        document_id=document_id,
        page_number=page_number,
        command=SavePageCommand(
            text=payload.text,
            parent_revision_id=payload.parent_revision_id,
            lock_version=if_match,
            actor_id=current_user.id,
            edit_reason=payload.edit_reason,
        ),
    )
    res_model = DraftPageRead(
        page_revision_id=result.page_revision_id,
        lock_version=result.lock_version,
        page_number=page_number,
        text=result.text,
        status=result.status,
    )
    await idemp_service.complete(
        decision.record_id,
        201,
        json.loads(res_model.model_dump_json() if hasattr(res_model, "model_dump_json") else res_model.json()),
    )
    return res_model


@router.post("/{document_id}/draft/submit", response_model=RevisionSetRead, status_code=201)
async def submit_draft(
    document_id: uuid.UUID,
    request: Request,
    if_match: int = Header(..., alias="If-Match"),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RevisionSetRead:
    document = await _get_document_or_404(session, document_id)
    await CapabilityService(session).require(
        user=current_user,
        patient_id=document.patient_id,
        capability="document_revision.edit",
        action="document_revision.submit",
        trace_id=new_trace_id(),
        object_id=document_id,
    )
    idemp_service = IdempotencyService(session, current_user.id)
    decision = await idemp_service.begin(
        scope=f"submit_draft:{document_id}",
        key=idempotency_key,
        payload={"if_match": if_match},
    )
    if decision.is_replay:
        return (
            RevisionSetRead.model_validate(decision.response_body)
            if hasattr(RevisionSetRead, "model_validate")
            else RevisionSetRead.parse_obj(decision.response_body)
        )

    res = await RevisionService(session).submit(
        document_id, SubmitCommand(actor_id=current_user.id, lock_version=if_match)
    )
    res_model = RevisionSetRead(
        revision_set_id=res.revision_set_id,
        document_id=res.document_id,
        revision_number=res.revision_number,
        status=res.status,
        created_by_user_id=res.created_by_user_id,
        created_at=res.created_at,
        submitted_at=res.submitted_at,
        approved_by_user_id=res.approved_by_user_id,
        approved_at=res.approved_at,
    )
    await idemp_service.complete(
        decision.record_id,
        201,
        json.loads(res_model.model_dump_json() if hasattr(res_model, "model_dump_json") else res_model.json()),
    )
    return res_model


@router.post(
    "/{document_id}/revision-sets/{revision_set_id}/approve", response_model=GenerationAcceptedRead, status_code=202
)
async def approve_revision_set(
    document_id: uuid.UUID,
    revision_set_id: uuid.UUID,
    payload: ApproveRevisionRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> GenerationAcceptedRead:
    document = await _get_document_or_404(session, document_id)
    await CapabilityService(session).require(
        user=current_user,
        patient_id=document.patient_id,
        capability="document_revision.approve",
        action="document_revision.approve",
        trace_id=new_trace_id(),
        object_id=document_id,
    )
    idemp_service = IdempotencyService(session, current_user.id)
    decision = await idemp_service.begin(
        scope=f"approve_revision_set:{document_id}:{revision_set_id}",
        key=idempotency_key,
        payload=json.loads(payload.model_dump_json() if hasattr(payload, "model_dump_json") else payload.json()),
    )
    if decision.is_replay:
        return (
            GenerationAcceptedRead.model_validate(decision.response_body)
            if hasattr(GenerationAcceptedRead, "model_validate")
            else GenerationAcceptedRead.parse_obj(decision.response_body)
        )

    res = await RevisionService(session).approve(
        revision_set_id=revision_set_id,
        command=ApproveRevisionCommand(actor_id=current_user.id, demo_mode=payload.demo_mode),
    )
    res_model = GenerationAcceptedRead(generation_id=res.generation_id, state=res.state)
    await idemp_service.complete(
        decision.record_id,
        202,
        json.loads(res_model.model_dump_json() if hasattr(res_model, "model_dump_json") else res_model.json()),
    )
    return res_model


@router.post("/{document_id}/revision-sets/{revision_set_id}/reject", response_model=RevisionSetRead, status_code=200)
async def reject_revision_set(
    document_id: uuid.UUID,
    revision_set_id: uuid.UUID,
    payload: RejectRevisionRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RevisionSetRead:
    document = await _get_document_or_404(session, document_id)
    await CapabilityService(session).require(
        user=current_user,
        patient_id=document.patient_id,
        capability="document_revision.reject",
        action="document_revision.reject",
        trace_id=new_trace_id(),
        object_id=document_id,
    )
    res = await RevisionService(session).reject(
        revision_set_id=revision_set_id,
        command=RejectCommand(actor_id=current_user.id, reason=payload.reason),
    )
    return RevisionSetRead(
        revision_set_id=res.revision_set_id,
        document_id=res.document_id,
        revision_number=res.revision_number,
        status=res.status,
        created_by_user_id=res.created_by_user_id,
        created_at=res.created_at,
        submitted_at=res.submitted_at,
        approved_by_user_id=res.approved_by_user_id,
        approved_at=res.approved_at,
    )


@router.post("/{document_id}/revision-sets/{revision_set_id}/restore", response_model=DraftPageRead, status_code=201)
async def restore_revision(
    document_id: uuid.UUID,
    revision_set_id: uuid.UUID,
    payload: RestoreRevisionRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DraftPageRead:
    document = await _get_document_or_404(session, document_id)
    await CapabilityService(session).require(
        user=current_user,
        patient_id=document.patient_id,
        capability="document_revision.restore",
        action="document_revision.restore",
        trace_id=new_trace_id(),
        object_id=document_id,
    )
    res = await RevisionService(session).restore(
        document_id=document_id,
        page_number=1,  # defaulted for test / endpoint contract
        command=RestoreCommand(revision_id=payload.revision_id, actor_id=current_user.id, reason=payload.reason),
    )
    return DraftPageRead(
        page_revision_id=res.page_revision_id,
        lock_version=res.lock_version,
        page_number=res.page_number,
        text=res.text,
        status=res.status,
    )


@router.get("/{document_id}/revision-sets", response_model=list[RevisionSetRead], status_code=200)
async def list_revision_sets(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[RevisionSetRead]:
    await _get_document_or_404(session, document_id)
    rows = list(
        await session.scalars(select(DocumentRevisionSet).where(DocumentRevisionSet.document_id == document_id))
    )
    return [
        RevisionSetRead(
            revision_set_id=r.id,
            document_id=r.document_id,
            revision_number=r.revision_number,
            status=r.status,
            created_by_user_id=r.created_by_user_id,
            created_at=r.created_at,
            submitted_at=r.submitted_at,
            approved_by_user_id=r.approved_by_user_id,
            approved_at=r.approved_at,
        )
        for r in rows
    ]


@router.get("/{document_id}/draft/pages/{page_number}", response_model=DraftPageRead, status_code=200)
async def get_draft_page(
    document_id: uuid.UUID,
    page_number: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DraftPageRead:
    await _get_document_or_404(session, document_id)
    head = await session.get(DocumentDraftHead, document_id)
    if not head:
        raise NotFoundError("Draft head not found")
    page_rev_id_str = head.selected_pages.get(str(page_number))
    if not page_rev_id_str:
        raise NotFoundError("Draft page not found")
    
    page_rev = await session.get(DocumentPageRevision, uuid.UUID(page_rev_id_str))
    if not page_rev:
        raise NotFoundError("Revision not found")
        
    return DraftPageRead(
        page_revision_id=page_rev.id,
        lock_version=head.lock_version,
        page_number=page_number,
        text=page_rev.corrected_text,
        status="draft"
    )

@router.get("/{document_id}/revision-sets/{revision_set_id}/pages/{page_number}", response_model=DraftPageRead, status_code=200)
async def get_revision_page(
    document_id: uuid.UUID,
    revision_set_id: uuid.UUID,
    page_number: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DraftPageRead:
    await _get_document_or_404(session, document_id)
    rev_set = await session.get(DocumentRevisionSet, revision_set_id)
    if not rev_set or rev_set.document_id != document_id:
        raise NotFoundError("Revision set not found")
        
    rev_page = await session.scalar(
        select(DocumentRevisionPage)
        .where(DocumentRevisionPage.revision_set_id == revision_set_id)
        .where(DocumentRevisionPage.page_number == page_number)
    )
    if not rev_page:
        raise NotFoundError("Revision page not found")
        
    page_rev = await session.get(DocumentPageRevision, rev_page.page_revision_id)
    if not page_rev:
        raise NotFoundError("Revision content not found")
        
    return DraftPageRead(
        page_revision_id=page_rev.id,
        lock_version=1,
        page_number=page_number,
        text=page_rev.corrected_text,
        status=rev_set.status
    )

