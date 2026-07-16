"""Patient permission authorization service.
Dịch vụ kiểm tra và quản lý quyền truy cập dữ liệu bệnh nhân (patient scopes & RBAC).
"""

import logging
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.errors import PermissionDeniedError
from hospital_ai.core.security import PATIENT_READ_SCOPES, PATIENT_UPLOAD_SCOPES
from hospital_ai.db.models import PatientPermission, User
from hospital_ai.services.audit import AuditService

logger = logging.getLogger(__name__)

ACTIVE_PATIENT_PERMISSION_SQL = """
select 1
from patient_permissions pp
where pp.user_id = :user_id
  and pp.patient_id = :patient_id
  and pp.scope in :accepted_scopes
  and pp.deleted_at is null
  and (pp.expires_at is null or pp.expires_at > now())
""".strip()


def active_patient_permission_filters(
    *,
    user_id: uuid.UUID,
    patient_id: Any,
    accepted_scopes: Iterable[str],
    now: datetime | None = None,
):
    """Tạo bộ điều kiện lọc SQLAlchemy kiểm tra quyền truy cập đang có hiệu lực đối với bệnh nhân cụ thể."""
    active_at = now or datetime.now(UTC)
    return (
        PatientPermission.user_id == user_id,
        PatientPermission.patient_id == patient_id,
        PatientPermission.scope.in_(tuple(sorted(set(accepted_scopes)))),
        PatientPermission.deleted_at.is_(None),
        or_(PatientPermission.expires_at.is_(None), PatientPermission.expires_at > active_at),
    )


def active_patient_permission_exists(
    *,
    user_id: uuid.UUID,
    patient_id: Any,
    accepted_scopes: Iterable[str],
    now: datetime | None = None,
):
    """Tạo mệnh đề `EXISTS` trong SQL để xác định xem người dùng có quyền hợp lệ hay không."""
    return exists().where(
        *active_patient_permission_filters(
            user_id=user_id,
            patient_id=patient_id,
            accepted_scopes=accepted_scopes,
            now=now,
        )
    )


class PermissionService:
    """Service to verify and require patient-level access permissions.
    Dịch vụ kiểm định quyền hạn truy cập theo phạm vi bệnh nhân và ghi lại nhật ký kiểm tra (audit log).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Khởi tạo PermissionService với phiên kết nối cơ sở dữ liệu AsyncSession."""
        self.session = session

    async def has_patient_scope(
        self,
        *,
        user_id: uuid.UUID,
        patient_id: uuid.UUID,
        accepted_scopes: Iterable[str],
    ) -> bool:
        """Check if user has any of the accepted scopes for a patient (via local DB or HMS check).
        Kiểm tra người dùng có một trong các phạm vi (scopes) cho phép hay không (qua DB cục bộ hoặc REST API của HMS).
        """
        # Check permissions with HMS first if sync integration is active
        from hospital_ai.core.config import get_settings

        settings = get_settings()
        if settings.hms_sync_enabled:
            from hospital_ai.services.hms_connector import HmsApiClient

            hms_client = HmsApiClient(settings)
            try:
                hms_perms = await hms_client.check_clinician_permissions(str(patient_id), str(user_id))
                if hms_perms.get("has_access") or hms_perms.get("hasAccess"):
                    hms_scopes = hms_perms.get("scopes", ["read"])
                    if any(scope in accepted_scopes for scope in hms_scopes):
                        return True
            except Exception:
                logger.warning(
                    "HMS permission check failed for user=%s patient=[REDACTED]",
                    user_id,
                    exc_info=True,
                )

        stmt = select(
            active_patient_permission_exists(
                user_id=user_id,
                patient_id=patient_id,
                accepted_scopes=accepted_scopes,
            )
        )
        result = await self.session.execute(stmt)
        return bool(result.scalar())

    async def require_patient_scope(
        self,
        *,
        user: User,
        patient_id: uuid.UUID,
        accepted_scopes: Iterable[str],
        action: str,
        object_type: str = "patient",
        object_id: uuid.UUID | None = None,
        trace_id: str,
        ip_address: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Enforce that user has required patient scope; otherwise audit failure and raise PermissionDeniedError.
        Bắt buộc người dùng phải có quyền truy cập; nếu không có hoặc đã hết hạn, ghi nhật ký
        từ chối và ném lỗi PermissionDeniedError.
        """
        accepted: set[str] = set(accepted_scopes)
        if await self.has_patient_scope(
            user_id=user.id,
            patient_id=patient_id,
            accepted_scopes=accepted,
        ):
            return

        # Check if there is an expired permission
        stmt_expired = select(PatientPermission).where(
            PatientPermission.user_id == user.id,
            PatientPermission.patient_id == patient_id,
            PatientPermission.scope.in_(accepted),
            PatientPermission.expires_at <= datetime.now(UTC),
            PatientPermission.deleted_at.is_(None),
        )
        result_expired = await self.session.execute(stmt_expired)
        expired_perms = result_expired.scalars().all()
        if expired_perms:
            await AuditService(self.session).record(
                actor_user_id=user.id,
                action="access_permission.expired",
                object_type="patient_permission",
                object_id=expired_perms[0].id,
                patient_id=patient_id,
                outcome="failed",
                trace_id=trace_id,
                ip_address=ip_address,
                metadata={
                    "expired_at": expired_perms[0].expires_at.isoformat() if expired_perms[0].expires_at else None,
                    "scope": expired_perms[0].scope,
                },
            )

        await AuditService(self.session).record(
            actor_user_id=user.id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            patient_id=patient_id,
            outcome="denied",
            trace_id=trace_id,
            ip_address=ip_address,
            metadata={"required_scopes": sorted(accepted), **(metadata or {})},
        )
        await self.session.commit()
        raise PermissionDeniedError("User is not authorized for this patient.")

    async def require_read(
        self,
        *,
        user: User,
        patient_id: uuid.UUID,
        action: str,
        trace_id: str,
        object_type: str = "patient",
        object_id: uuid.UUID | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Enforce `PATIENT_READ_SCOPES` for reading patient records.
        Bắt buộc quyền đọc (`PATIENT_READ_SCOPES`) đối với hồ sơ bệnh nhân.
        """
        await self.require_patient_scope(
            user=user,
            patient_id=patient_id,
            accepted_scopes=PATIENT_READ_SCOPES,
            action=action,
            object_type=object_type,
            object_id=object_id,
            trace_id=trace_id,
            ip_address=ip_address,
        )

    async def require_upload_or_admin_role(
        self,
        *,
        user: User,
        patient_id: uuid.UUID,
        action: str,
        trace_id: str,
        object_type: str = "document",
        object_id: uuid.UUID | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Enforce role (`records_staff` or `admin`) and `PATIENT_UPLOAD_SCOPES`.
        Bắt buộc vai trò nhân viên hồ sơ (`records_staff` hoặc `admin`) và quyền tải lên (`PATIENT_UPLOAD_SCOPES`).
        """
        if user.role not in {"records_staff", "admin"}:
            await AuditService(self.session).record(
                actor_user_id=user.id,
                action=action,
                object_type=object_type,
                object_id=object_id,
                patient_id=patient_id,
                outcome="denied",
                trace_id=trace_id,
                ip_address=ip_address,
                metadata={"reason": "role_not_allowed", "role": user.role},
            )
            await self.session.commit()
            raise PermissionDeniedError("Only records staff or admins can upload documents.")

        await self.require_patient_scope(
            user=user,
            patient_id=patient_id,
            accepted_scopes=PATIENT_UPLOAD_SCOPES,
            action=action,
            object_type=object_type,
            object_id=object_id,
            trace_id=trace_id,
            ip_address=ip_address,
        )
