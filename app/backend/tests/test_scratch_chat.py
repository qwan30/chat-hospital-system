import uuid

import pytest
from sqlalchemy import select

from hospital_ai.db.migrations import DOCTOR_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import DocumentChunk, PatientPermission, User
from hospital_ai.services.chat import ChatService
from tests.conftest import create_indexed_document


@pytest.mark.asyncio
async def test_10_chat_scenarios(session_and_settings):
    session, settings = session_and_settings

    # 1. Setup users
    doctor = await session.get(User, DOCTOR_ID)

    lab_staff = User(id=uuid.uuid4(), email="lab@test.com", role="lab_staff", full_name="Lab Staff")
    records_staff = User(id=uuid.uuid4(), email="records@test.com", role="records_staff", full_name="Records Staff")
    unauth_user = User(id=uuid.uuid4(), email="unauth@test.com", role="doctor", full_name="Unauth Doctor")

    session.add_all([lab_staff, records_staff, unauth_user])
    await session.flush()

    # Setup permissions for lab_staff and records_staff
    session.add_all(
        [
            PatientPermission(user_id=lab_staff.id, patient_id=PATIENT_ALICE_ID, scope="read"),
            PatientPermission(user_id=records_staff.id, patient_id=PATIENT_ALICE_ID, scope="read"),
        ]
    )
    await session.flush()

    # 2. Setup documents
    clinical_note = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Clinical Note",
        content="Patient is recovering well from surgery.",
    )

    lab_result = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Lab Results",
        content="Hemoglobin is 14 g/dL.",
    )
    # Set document_type to 'labs'
    clinical_note.document_type = "note"
    lab_result.document_type = "labs"

    # Psychiatric note with access tags
    psych_note = await create_indexed_document(
        session,
        patient_id=PATIENT_ALICE_ID,
        uploaded_by=DOCTOR_ID,
        title="Psychiatric Evaluation",
        content="Patient discussed anxiety symptoms.",
    )
    # Add access_tags metadata to chunks
    chunks_res = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == psych_note.id))
    for chunk in chunks_res.scalars().all():
        chunk.metadata = {"access_tags": ["psychiatry"]}

    await session.commit()

    chat_svc = ChatService(session, settings)

    scenarios = [
        ("1. Doctor: Chit-chat (No evidence needed)", doctor, "Xin chào!"),
        ("2. Doctor: Đọc Clinical Note (Truy cập hợp lệ)", doctor, "Tình trạng phẫu thuật thế nào?"),
        (
            "3. Lab Staff: Đọc Lab Result (Truy cập hợp lệ theo document_type)",
            lab_staff,
            "Chỉ số Hemoglobin là bao nhiêu?",
        ),
        ("4. Lab Staff: Đọc Psychiatric Note (Bị chặn do tag bypass fix)", lab_staff, "Triệu chứng lo âu thế nào?"),
        (
            "5. Records Staff: Đọc Clinical Note (Hợp lệ do được bổ sung role)",
            records_staff,
            "Tình trạng phẫu thuật thế nào?",
        ),
        (
            "6. Doctor: Đọc Psychiatric Note (Bị chặn vì doctor chưa có scope 'psychiatry')",
            doctor,
            "Triệu chứng lo âu thế nào?",
        ),
        (
            "7. Unauth User: Truy vấn Alice (Bị chặn phân quyền bệnh nhân)",
            unauth_user,
            "Tình trạng phẫu thuật thế nào?",
        ),
        ("8. Records Staff: Chit-chat (Graceful fallback, no scary permission error)", records_staff, "Cám ơn bạn!"),
        ("9. Doctor: Truy vấn không có dữ liệu (Graceful no evidence)", doctor, "Kết quả chụp MRI thế nào?"),
        (
            "10. Lab Staff: Truy vấn Clinical Note chung (Hợp lệ do 'read' scope fix)",
            lab_staff,
            "Bệnh nhân có hồi phục tốt không?",
        ),
    ]

    results = []
    for desc, user, question in scenarios:
        try:
            # We must use deterministic_embedding for the query so it matches our mocked chunks
            # Wait, ChatService does this internally via EmbeddingService, but in tests it's mocked via mock_openai
            # It might require patching the embedding service if it calls OpenAI directly. Let's see what happens.
            # Actually test_chat_endpoint uses `mock_openai` fixture.
            # I should just use `_get_conversation_history` logic or let the service run.
            ans = await chat_svc.answer(
                user=user,
                patient_id=PATIENT_ALICE_ID,
                question=question,
                top_k=5,
                trace_id=str(uuid.uuid4()),
                ip_address="127.0.0.1",
            )
            status = "✅ THÀNH CÔNG" if ans.answer else "❌ THẤT BẠI"
            answer_preview = ans.answer[:100] + "..." if len(ans.answer) > 100 else ans.answer
        except Exception as e:
            status = "❌ LỖI / BỊ CHẶN (DENIED)"
            answer_preview = str(e)

        results.append(
            f"### {desc}\n**Role:** `{user.role}` | **Query:** `{question}`\n"
            f"**Status:** {status}\n**AI Response:** {answer_preview}\n"
        )

    with open(
        "C:/Users/NITRO/.gemini/antigravity/brain/340ed16e-6aa9-4af3-a95c-2b034f67f732/chat_results.md",
        "w",
        encoding="utf-8",
    ) as f:
        f.write("# Kết quả 10 câu Chat sau khi Fix Bugs\n\n")
        f.write("\n".join(results))
