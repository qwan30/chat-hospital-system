import uuid
from typing import Iterable, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.models import ChatThread, ChatThreadParticipant, User
from hospital_ai.schemas.chat_threads import ChatThreadCreate, ChatThreadUpdate
from hospital_ai.services.audit import AuditService
from hospital_ai.services.permissions import PermissionService, active_patient_permission_exists


class ChatThreadService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_thread(
        self,
        *,
        user: User,
        payload: ChatThreadCreate,
        trace_id: str,
        ip_address: Optional[str] = None,
    ) -> ChatThread:
        if payload.scope == "patient-linked":
            await PermissionService(self.session).require_read(
                user=user,
                patient_id=payload.patient_id,
                action="chat_thread.create",
                trace_id=trace_id,
                object_type="chat_thread",
                ip_address=ip_address,
            )

        thread = ChatThread(
            title=payload.title,
            scope=payload.scope,
            visibility=payload.visibility,
            status="active",
            owner_user_id=user.id,
            patient_id=payload.patient_id,
            created_trace_id=trace_id,
        )
        self.session.add(thread)
        await self.session.flush()

        self.session.add(
            ChatThreadParticipant(
                thread_id=thread.id,
                user_id=user.id,
                access_level="owner",
                can_share=True,
                added_by_user_id=user.id,
                created_trace_id=trace_id,
            )
        )
        await AuditService(self.session).record(
            actor_user_id=user.id,
            action="chat_thread.create",
            object_type="chat_thread",
            object_id=thread.id,
            patient_id=thread.patient_id,
            outcome="allowed",
            trace_id=trace_id,
            ip_address=ip_address,
            metadata={"scope": thread.scope, "visibility": thread.visibility},
        )
        await self.session.commit()
        await self.session.refresh(thread)
        return thread

    async def list_threads(self, *, user: User) -> list[ChatThread]:
        permission_exists = active_patient_permission_exists(
            user_id=user.id,
            patient_id=ChatThread.patient_id,
            accepted_scopes=PATIENT_READ_SCOPES,
        )
        stmt = (
            select(ChatThread)
            .join(ChatThreadParticipant)
            .where(
                ChatThread.deleted_at.is_(None),
                ChatThreadParticipant.deleted_at.is_(None),
                ChatThreadParticipant.user_id == user.id,
                or_(ChatThread.scope == "general", permission_exists),
            )
            .order_by(ChatThread.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_thread(
        self,
        *,
        user: User,
        thread_id: uuid.UUID,
        trace_id: str,
        ip_address: Optional[str] = None,
    ) -> ChatThread:
        thread = await self._get_accessible_thread(
            user=user,
            thread_id=thread_id,
            allowed_access=("owner", "write", "read"),
            action="chat_thread.read",
            trace_id=trace_id,
            ip_address=ip_address,
            with_detail=True,
        )
        await self._require_patient_read_if_needed(
            user=user,
            thread=thread,
            action="chat_thread.read",
            trace_id=trace_id,
            ip_address=ip_address,
        )
        await AuditService(self.session).record(
            actor_user_id=user.id,
            action="chat_thread.read",
            object_type="chat_thread",
            object_id=thread.id,
            patient_id=thread.patient_id,
            outcome="allowed",
            trace_id=trace_id,
            ip_address=ip_address,
        )
        await self.session.commit()
        return thread

    async def update_thread(
        self,
        *,
        user: User,
        thread_id: uuid.UUID,
        payload: ChatThreadUpdate,
        trace_id: str,
        ip_address: Optional[str] = None,
    ) -> ChatThread:
        changes = payload.dict(exclude_unset=True)
        if not changes:
            return await self.get_thread(
                user=user,
                thread_id=thread_id,
                trace_id=trace_id,
                ip_address=ip_address,
            )

        owner_only_fields = {"visibility", "status"}
        allowed_access = ("owner",) if owner_only_fields.intersection(changes) else ("owner", "write")
        thread = await self._get_accessible_thread(
            user=user,
            thread_id=thread_id,
            allowed_access=allowed_access,
            action="chat_thread.update",
            trace_id=trace_id,
            ip_address=ip_address,
        )
        await self._require_patient_read_if_needed(
            user=user,
            thread=thread,
            action="chat_thread.update",
            trace_id=trace_id,
            ip_address=ip_address,
        )

        for field, value in changes.items():
            setattr(thread, field, value)

        await AuditService(self.session).record(
            actor_user_id=user.id,
            action="chat_thread.update",
            object_type="chat_thread",
            object_id=thread.id,
            patient_id=thread.patient_id,
            outcome="allowed",
            trace_id=trace_id,
            ip_address=ip_address,
            metadata={"fields": sorted(changes.keys())},
        )
        await self.session.commit()
        await self.session.refresh(thread)
        return thread

    async def archive_thread(
        self,
        *,
        user: User,
        thread_id: uuid.UUID,
        trace_id: str,
        ip_address: Optional[str] = None,
    ) -> ChatThread:
        thread = await self._get_accessible_thread(
            user=user,
            thread_id=thread_id,
            allowed_access=("owner",),
            action="chat_thread.archive",
            trace_id=trace_id,
            ip_address=ip_address,
        )
        await self._require_patient_read_if_needed(
            user=user,
            thread=thread,
            action="chat_thread.archive",
            trace_id=trace_id,
            ip_address=ip_address,
        )
        thread.status = "archived"
        await AuditService(self.session).record(
            actor_user_id=user.id,
            action="chat_thread.archive",
            object_type="chat_thread",
            object_id=thread.id,
            patient_id=thread.patient_id,
            outcome="allowed",
            trace_id=trace_id,
            ip_address=ip_address,
        )
        await self.session.commit()
        await self.session.refresh(thread)
        return thread

    async def _get_accessible_thread(
        self,
        *,
        user: User,
        thread_id: uuid.UUID,
        allowed_access: Iterable[str],
        action: str,
        trace_id: str,
        ip_address: Optional[str],
        with_detail: bool = False,
    ) -> ChatThread:
        stmt = (
            select(ChatThread)
            .join(ChatThreadParticipant)
            .where(
                ChatThread.id == thread_id,
                ChatThread.deleted_at.is_(None),
                ChatThreadParticipant.user_id == user.id,
                ChatThreadParticipant.deleted_at.is_(None),
                ChatThreadParticipant.access_level.in_(tuple(allowed_access)),
            )
        )
        if with_detail:
            stmt = stmt.options(
                selectinload(ChatThread.participants),
                selectinload(ChatThread.messages),
            )
        result = await self.session.execute(stmt)
        thread = result.scalar_one_or_none()
        if thread is not None:
            return thread

        await AuditService(self.session).record(
            actor_user_id=user.id,
            action=action,
            object_type="chat_thread",
            object_id=thread_id,
            outcome="denied",
            trace_id=trace_id,
            ip_address=ip_address,
            metadata={"reason": "thread_access_denied", "required_access": list(allowed_access)},
        )
        await self.session.commit()
        raise PermissionDeniedError("User is not authorized for this chat thread.")

    async def _require_patient_read_if_needed(
        self,
        *,
        user: User,
        thread: ChatThread,
        action: str,
        trace_id: str,
        ip_address: Optional[str],
    ) -> None:
        if thread.scope != "patient-linked":
            return
        await PermissionService(self.session).require_read(
            user=user,
            patient_id=thread.patient_id,
            action=action,
            trace_id=trace_id,
            object_type="chat_thread",
            object_id=thread.id,
            ip_address=ip_address,
        )
