"""Trình hỗ trợ khởi tạo dữ liệu mẫu (Seeding Synthetic Data) cho môi trường phát triển và kiểm thử.

Tạo các người dùng, bệnh nhân và phân quyền truy cập ban đầu trong CSDL
để phục vụ việc kiểm thử tính năng chat AI, kiểm soát truy cập và tuân thủ HIPAA.
"""

import uuid
from collections.abc import Iterable
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.db.models import Patient, PatientPermission, User

# Các UUID cố định (Static UUIDs) dùng cho người dùng mẫu trong môi trường Dev/Test
DOCTOR_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
RECORDS_ID = uuid.UUID("10000000-0000-0000-0000-000000000002")
SECURITY_ID = uuid.UUID("10000000-0000-0000-0000-000000000003")
ADMIN_ID = uuid.UUID("10000000-0000-0000-0000-000000000004")

PATIENT_ALICE_ID = uuid.UUID("20000000-0000-0000-0000-000000000001")
PATIENT_BOB_ID = uuid.UUID("20000000-0000-0000-0000-000000000002")
PATIENT_ELEANOR_ID = uuid.UUID("20000000-0000-0000-0000-000000000003")

# Dummy patient ID for public institutional documents
HOSPITAL_PUBLIC_ID = uuid.UUID("40000000-0000-0000-0000-000000000001")



async def seed_synthetic_data(session: AsyncSession) -> None:
    """Khởi tạo và ghi vào CSDL tập dữ liệu giả lập (synthetic data) nếu chưa tồn tại.

    Bao gồm các bác sĩ, nhân viên y tế, bệnh nhân mẫu (như Alice, Bob, Eleanor) và
    các quyền hạn tương ứng phục vụ cho kiểm thử tính năng RAG/PHI.
    """
    users = [
        User(
            id=DOCTOR_ID,
            email="doctor@example.test",
            full_name="Dr. Dev Doctor",
            department="Internal Medicine",
            role="doctor",
        ),
        User(
            id=RECORDS_ID,
            email="records@example.test",
            full_name="Riley Records",
            department="Medical Records",
            role="records_staff",
        ),
        User(
            id=SECURITY_ID,
            email="security@example.test",
            full_name="Sam Security",
            department="Compliance",
            role="security",
        ),
        User(
            id=ADMIN_ID,
            email="admin@example.test",
            full_name="Alex Admin",
            department="IT",
            role="admin",
        ),
    ]
    patients = [
        Patient(
            id=PATIENT_ALICE_ID,
            mrn="MRN-0001",
            full_name="Alice Synthetic",
            dob=date(1978, 5, 17),
            department="Internal Medicine",
        ),
        Patient(
            id=PATIENT_BOB_ID,
            mrn="MRN-0002",
            full_name="Bob Synthetic",
            dob=date(1969, 9, 9),
            department="Cardiology",
        ),
        Patient(
            id=PATIENT_ELEANOR_ID,
            mrn="MRN-0003",
            full_name="Eleanor Vance",
            dob=date(1951, 3, 14),
            department="Cardiology",
        ),
        Patient(
            id=HOSPITAL_PUBLIC_ID,
            mrn="SYS-PUBLIC",
            full_name="Hospital Public Knowledge Base",
            dob=date(1900, 1, 1),
            department="Hospital",
        ),
    ]
    permissions = [
        PatientPermission(user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID, scope="read"),
        PatientPermission(user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID, scope="summary"),
        PatientPermission(user_id=DOCTOR_ID, patient_id=PATIENT_ALICE_ID, scope="medication"),
        PatientPermission(user_id=RECORDS_ID, patient_id=PATIENT_ALICE_ID, scope="upload"),
        PatientPermission(user_id=ADMIN_ID, patient_id=PATIENT_ALICE_ID, scope="admin"),
        PatientPermission(user_id=DOCTOR_ID, patient_id=PATIENT_ELEANOR_ID, scope="read"),
        PatientPermission(user_id=DOCTOR_ID, patient_id=PATIENT_ELEANOR_ID, scope="summary"),
        PatientPermission(user_id=DOCTOR_ID, patient_id=PATIENT_ELEANOR_ID, scope="medication"),
        PatientPermission(user_id=RECORDS_ID, patient_id=PATIENT_ELEANOR_ID, scope="upload"),
        PatientPermission(user_id=ADMIN_ID, patient_id=PATIENT_ELEANOR_ID, scope="admin"),
    ]

    await _add_missing_by_id(session, User, users)
    await _add_missing_by_id(session, Patient, patients)
    await _add_missing_permissions(session, permissions)
    await session.commit()


async def _add_missing_by_id(session: AsyncSession, model: type, rows: Iterable[object]) -> None:
    """Hàm hỗ trợ chèn các bản ghi vào CSDL nếu ID chưa tồn tại."""
    for row in rows:
        exists = await session.get(model, row.id)
        if exists is None:
            session.add(row)


async def _add_missing_permissions(session: AsyncSession, rows: Iterable[PatientPermission]) -> None:
    """Hàm hỗ trợ chèn các phân quyền bệnh nhân nếu bộ `(user_id, patient_id, scope)` chưa tồn tại."""
    for row in rows:
        result = await session.execute(
            select(PatientPermission).where(
                PatientPermission.user_id == row.user_id,
                PatientPermission.patient_id == row.patient_id,
                PatientPermission.scope == row.scope,
            )
        )
        if result.scalar_one_or_none() is None:
            session.add(row)
