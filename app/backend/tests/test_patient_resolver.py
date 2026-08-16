import pytest
import uuid
from datetime import date

from hospital_ai.db.models import Patient
from hospital_ai.services.patient_resolver import PatientResolver


@pytest.fixture
async def sample_vietnamese_patient(session_and_settings):
    session, _ = session_and_settings
    p = Patient(
        id=uuid.uuid4(),
        mrn="MRN-0015",
        full_name="Bùi Đức Hùng",
        dob=date(1978, 5, 20),
        department="Cardiology 4N",
        status="active",
    )
    session.add(p)
    await session.commit()
    return p


@pytest.fixture
async def sample_multi_patients(session_and_settings):
    session, _ = session_and_settings
    # Insert 2 patients with the same name to test disambiguation
    p1 = Patient(
        id=uuid.uuid4(),
        mrn="MRN-9991",
        full_name="Nguyen Van A",
        dob=date(1985, 3, 15),
        department="Emergency",
        status="active",
    )
    p2 = Patient(
        id=uuid.uuid4(),
        mrn="MRN-9992",
        full_name="Nguyen Van A",
        dob=date(1992, 8, 10),
        department="Pediatrics",
        status="active",
    )
    session.add_all([p1, p2])
    await session.commit()
    return [p1, p2]


@pytest.mark.asyncio
async def test_resolve_seeded_mrn(session_and_settings):
    session, _ = session_and_settings
    resolver = PatientResolver(session)
    res = await resolver.resolve("What are the lab results for MRN-0001?")
    assert res.status == "single_match"
    assert len(res.patients) == 1
    assert res.patients[0].mrn == "MRN-0001"
    assert res.patients[0].full_name == "Alice Synthetic"


@pytest.mark.asyncio
async def test_resolve_seeded_patient_by_name(session_and_settings):
    session, _ = session_and_settings
    resolver = PatientResolver(session)
    res = await resolver.resolve("do you know Eleanor Vance patient?")
    assert res.status == "single_match"
    assert len(res.patients) == 1
    assert res.patients[0].mrn == "MRN-0003"
    assert res.patients[0].full_name == "Eleanor Vance"


@pytest.mark.asyncio
async def test_resolve_vietnamese_patient_accent_insensitive(
    session_and_settings, sample_vietnamese_patient
):
    session, _ = session_and_settings
    resolver = PatientResolver(session)
    # Search with no accents
    res1 = await resolver.resolve("do you know bui duc hung patient?")
    assert res1.status == "single_match"
    assert res1.patients[0].mrn == "MRN-0015"

    # Search with full accents
    res2 = await resolver.resolve("Thông tin của bệnh nhân Bùi Đức Hùng")
    assert res2.status == "single_match"
    assert res2.patients[0].mrn == "MRN-0015"


@pytest.mark.asyncio
async def test_resolve_multiple_matches_disambiguation(
    session_and_settings, sample_multi_patients
):
    session, _ = session_and_settings
    resolver = PatientResolver(session)
    res = await resolver.resolve("Show me records for Nguyen Van A")
    assert res.status == "multiple_matches"
    assert len(res.patients) == 2
    mrns = {p.mrn for p in res.patients}
    assert mrns == {"MRN-9991", "MRN-9992"}


@pytest.mark.asyncio
async def test_resolve_no_match(session_and_settings):
    session, _ = session_and_settings
    resolver = PatientResolver(session)
    res = await resolver.resolve("What is the hospital STEMI discharge protocol?")
    assert res.status == "no_match"
    assert len(res.patients) == 0
