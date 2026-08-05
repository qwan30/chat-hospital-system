from __future__ import annotations

import base64
import uuid

import pytest
from pydantic import ValidationError

from hospital_ai.core.config import get_settings
from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID, PATIENT_BOB_ID
from hospital_ai.db.models import Document, DocumentChunk, DocumentPage, User
from hospital_ai.migrations.cdi_v2_backfill import BackfillPolicy, CdiV2Backfill


@pytest.fixture
async def session(session_and_settings):
    session, _ = session_and_settings
    return session


def test_cdi_v2_feature_flags_default_false():
    settings = get_settings()
    assert getattr(settings, "cdi_v2_dual_read", True) is False
    assert getattr(settings, "cdi_v2_active_generation_reads", True) is False
    assert getattr(settings, "cdi_v2_authoring_enabled", True) is False


@pytest.mark.asyncio
async def test_parity_verification_succeeds_on_clean_synthetic(session) -> None:
    doctor = await session.get(User, DOCTOR_ID)
    doc = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id if doctor else uuid.uuid4(),
        title="Parity Clean Synth",
        document_type="progress_note",
        storage_uri="local://test/parity_clean.pdf",
        mime_type="application/pdf",
        status="ready",
        is_synthetic=True,
        indexed_source_sha256="0011223344556677889900112233445566778899001122334455667788990011",
    )
    session.add(doc)
    await session.flush()

    page = DocumentPage(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_number=1,
        ocr_text="Clean parity text",
        ocr_confidence=1.0,
    )
    session.add(page)
    await session.flush()

    chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_id=page.id,
        patient_id=PATIENT_ALICE_ID,
        chunk_index=0,
        content="Clean parity text",
        token_count=3,
    )
    session.add(chunk)
    await session.flush()
    await session.commit()

    runner = CdiV2Backfill(session, policy=BackfillPolicy(autoapprove_synthetic=True))
    await runner.run_document(doc.id)

    parity_report = await runner.compute_parity_report([doc.id])
    assert parity_report["wrong_patient_count"] == 0
    assert parity_report["superseded_generation_count"] == 0
    assert parity_report["status"] == "passed"
    assert len(parity_report["documents"]) == 1
    artifact = parity_report["documents"][0]
    assert artifact["lexical_vector_ids"]
    assert artifact["citation_locators"]
    assert "graph_provenance" in artifact
    assert "source_hashes" in artifact
    assert "authorization_outcomes" in artifact
    assert len(parity_report["artifact_sha256"]) == 64


@pytest.mark.asyncio
async def test_parity_fails_on_wrong_patient_and_flags_remain_off(session) -> None:
    doctor = await session.get(User, DOCTOR_ID)
    doc = Document(
        id=uuid.uuid4(),
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=doctor.id if doctor else uuid.uuid4(),
        title="Parity Corrupt Synth",
        document_type="progress_note",
        storage_uri="local://test/parity_corrupt.pdf",
        mime_type="application/pdf",
        status="ready",
        is_synthetic=True,
        indexed_source_sha256="ffeebbddccaa99887766554433221100ffeebbddccaa99887766554433221100",
    )
    session.add(doc)
    await session.flush()

    page = DocumentPage(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_number=1,
        ocr_text="Corrupt text",
        ocr_confidence=1.0,
    )
    session.add(page)
    await session.flush()

    chunk = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc.id,
        page_id=page.id,
        patient_id=PATIENT_BOB_ID,
        chunk_index=0,
        content="Corrupt text",
        token_count=2,
    )
    session.add(chunk)
    await session.flush()
    await session.commit()

    runner = CdiV2Backfill(session, policy=BackfillPolicy(autoapprove_synthetic=True))
    parity_report = await runner.compute_parity_report([doc.id])
    assert parity_report["wrong_patient_count"] > 0
    assert parity_report["status"] == "failed"

    settings = get_settings()
    assert getattr(settings, "cdi_v2_dual_read", True) is False
    assert getattr(settings, "cdi_v2_active_generation_reads", True) is False
    assert getattr(settings, "cdi_v2_authoring_enabled", True) is False


def test_cdi_v2_reads_require_signed_parity_artifact(tmp_path) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    artifact = tmp_path / "parity.json"
    artifact.write_text('{"status":"passed"}', encoding="utf-8")
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    signature = private_key.sign(artifact.read_bytes())

    with pytest.raises(ValidationError, match="signed parity artifact"):
        from hospital_ai.core.config import Settings

        Settings(cdi_v2_active_generation_reads=True)

    from hospital_ai.core.config import Settings

    settings = Settings(
        cdi_v2_active_generation_reads=True,
        cdi_v2_parity_artifact_path=artifact,
        cdi_v2_parity_artifact_public_key=base64.b64encode(public_key).decode("ascii"),
        cdi_v2_parity_artifact_signature=base64.b64encode(signature).decode("ascii"),
    )
    assert settings.cdi_v2_active_generation_reads is True
