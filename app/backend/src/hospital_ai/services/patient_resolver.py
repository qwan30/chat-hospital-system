from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from hospital_ai.core.security import PATIENT_READ_SCOPES
from hospital_ai.db.models import Patient, User
from hospital_ai.services.permissions import PermissionService


def remove_accents(input_str: str) -> str:
    """Normalize and strip diacritics / accents for robust matching in Vietnamese/English."""
    if not input_str:
        return ""
    # Map special Vietnamese letters like đ/Đ
    s = input_str.replace("đ", "d").replace("Đ", "D")
    nfkd_form = unicodedata.normalize("NFKD", s)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()


@dataclass
class ResolvedPatient:
    id: uuid.UUID
    mrn: str
    full_name: str
    dob: Optional[str] = None
    department: Optional[str] = None
    status: str = "active"


@dataclass
class PatientResolutionResult:
    status: str  # "single_match" | "multiple_matches" | "no_match" | "unauthorized"
    patients: list[ResolvedPatient] = field(default_factory=list)
    matched_term: Optional[str] = None
    raw_query: str = ""


class PatientResolver:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def resolve(self, query: str, user: Optional[User] = None) -> PatientResolutionResult:
        if not query or not query.strip():
            return PatientResolutionResult(status="no_match", raw_query=query or "")

        cleaned_query = query.strip()
        norm_query = remove_accents(cleaned_query)

        # 1. Check for MRN pattern (e.g. MRN-0015, MRN-0001, or MRN1234)
        mrn_matches = re.findall(r"\bMRN-?[0-9A-Z]+\b", cleaned_query, re.IGNORECASE)
        for mrn in mrn_matches:
            # Normalize to database format if needed
            stmt = select(Patient).where(
                Patient.deleted_at.is_(None),
                or_(
                    Patient.mrn.ilike(mrn),
                    Patient.mrn.ilike(mrn.replace("-", "")),
                    Patient.mrn.ilike(f"MRN-{mrn.replace('MRN', '').replace('-', '')}"),
                ),
            )
            result = await self.session.execute(stmt)
            matched_patients = list(result.scalars().all())
            if matched_patients:
                return await self._build_result(matched_patients, mrn, cleaned_query, user)

        # 2. Query all active patients and match by normalized full name
        stmt = select(Patient).where(Patient.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        all_patients = list(result.scalars().all())

        matched_patients: list[Patient] = []
        matched_name = ""

        # Check for full name substring matches
        for p in all_patients:
            p_norm_name = remove_accents(p.full_name)
            p_norm_mrn = remove_accents(p.mrn)

            # Check if patient's name is mentioned in the query
            if (len(p_norm_name) >= 3 and p_norm_name in norm_query) or (p_norm_mrn in norm_query):
                matched_patients.append(p)
                matched_name = p.full_name

        if not matched_patients:
            # Check individual name tokens for 2+ word names
            for p in all_patients:
                tokens = [t for t in remove_accents(p.full_name).split() if len(t) > 1]
                if len(tokens) >= 2 and all(token in norm_query for token in tokens):
                    if p not in matched_patients:
                        matched_patients.append(p)
                        matched_name = p.full_name

        if not matched_patients:
            return PatientResolutionResult(status="no_match", raw_query=cleaned_query)

        return await self._build_result(matched_patients, matched_name, cleaned_query, user)

    async def _build_result(
        self,
        patients: list[Patient],
        matched_term: str,
        raw_query: str,
        user: Optional[User] = None,
    ) -> PatientResolutionResult:
        perm_service = PermissionService(self.session)
        authorized_patients: list[Patient] = []

        for p in patients:
            if user is None:
                authorized_patients.append(p)
            else:
                has_access = await perm_service.has_patient_scope(
                    user_id=user.id,
                    patient_id=p.id,
                    accepted_scopes=PATIENT_READ_SCOPES,
                )
                if has_access:
                    authorized_patients.append(p)

        if user is not None and len(patients) > 0 and len(authorized_patients) == 0:
            return PatientResolutionResult(
                status="unauthorized",
                matched_term=matched_term,
                raw_query=raw_query,
            )

        resolved_list = [
            ResolvedPatient(
                id=p.id,
                mrn=p.mrn,
                full_name=p.full_name,
                dob=p.dob.isoformat() if p.dob else None,
                department=p.department,
                status=p.status,
            )
            for p in authorized_patients
        ]

        if len(resolved_list) == 1:
            return PatientResolutionResult(
                status="single_match",
                patients=resolved_list,
                matched_term=matched_term,
                raw_query=raw_query,
            )
        elif len(resolved_list) > 1:
            return PatientResolutionResult(
                status="multiple_matches",
                patients=resolved_list,
                matched_term=matched_term,
                raw_query=raw_query,
            )
        else:
            return PatientResolutionResult(status="no_match", raw_query=raw_query)
