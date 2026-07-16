"""
Generate 100 realistic Vietnamese medical documents for all patients.

Mirrors: tests/conftest.py create_indexed_document() pattern
Run: python scripts/generate_documents.py
"""
import asyncio
import hashlib
import random
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hospital_ai.db.models import Document, DocumentPage, DocumentChunk, Patient
from hospital_ai.db.session import get_session
from hospital_ai.services.embeddings import deterministic_embedding
from sqlalchemy import select

DOCTOR_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
DOC_UUID_PREFIX = "30000000-0000-0000-0000-"

# ── Vietnamese medical content templates ─────────────────────────

LAB_RESULTS = [
    {
        "title": "Ket qua xet nghiem mau toan phan (CBC)",
        "content": (
            "XET NGHIEM HUYET HOC\n"
            "Ngay lay mau: {date}\n\n"
            "THONG SO                          KET QUA    KHOANG THAM CHIEU\n"
            "Hong cau (RBC)                    {rbc:.2f}     4.0-5.8 M/uL\n"
            "Hemoglobin (HGB)                  {hgb:.1f}     12.0-16.0 g/dL\n"
            "Hematocrit (HCT)                  {hct:.1f}     37.0-47.0 %\n"
            "Bach cau (WBC)                    {wbc:.1f}     4.0-10.0 K/uL\n"
            "Tieu cau (PLT)                    {plt}      150-400 K/uL\n\n"
            "KET LUAN: {conclusion}\n"
            "Bac si doc ket qua: BS. {doctor}"
        ),
    },
    {
        "title": "Ket qua xet nghiem sinh hoa mau",
        "content": (
            "XET NGHIEM SINH HOA MAU\n"
            "Ngay lay mau: {date}\n\n"
            "CHI SO                            KET QUA    KHOANG THAM CHIEU\n"
            "Glucose (doi)                     {glu:.1f}     3.9-6.1 mmol/L\n"
            "HbA1c                             {hba1c:.1f}     < 6.5 %\n"
            "Creatinine                        {cre:.1f}     62-115 umol/L\n"
            "AST (GOT)                         {ast}         < 40 U/L\n"
            "ALT (GPT)                         {alt}         < 41 U/L\n"
            "Cholesterol toan phan             {chol:.1f}     < 5.2 mmol/L\n"
            "Triglyceride                      {tg:.1f}       < 1.7 mmol/L\n\n"
            "KET LUAN: {conclusion}\n"
            "Bac si: BS. {doctor}"
        ),
    },
    {
        "title": "Ket qua tong phan tich nuoc tieu",
        "content": (
            "TONG PHAN TICH NUOC TIEU\n"
            "Ngay: {date}\n\n"
            "CHI SO                  KET QUA        BINH THUONG\n"
            "Mau sac                 {color}        Vang nhat\n"
            "Do trong                {clarity}      Trong\n"
            "pH                      {ph:.1f}          5.0-7.0\n"
            "Protein                 {protein}      Am tinh\n"
            "Glucose                 {glucose}      Am tinh\n"
            "Hong cau                {rbc_urine}    0-2 /HPF\n"
            "Bach cau                {wbc_urine}    0-5 /HPF\n\n"
            "KET LUAN: {conclusion}\n"
            "BS. {doctor}"
        ),
    },
]

CLINICAL_NOTES = [
    {
        "title": "Ghi chu lam sang - Kham tong quat",
        "content": (
            "BENH AN KHAM LAM SANG\n"
            "Ngay kham: {date}\n"
            "Bac si: BS. {doctor}\n\n"
            "LY DO KHAM: {reason}\n\n"
            "TIEN SU BENH: {history}\n\n"
            "KHAM LAM SANG:\n"
            "- Nhiet do: {temp:.1f} do C\n"
            "- Mach: {pulse} lan/phut\n"
            "- Huyet ap: {bp_sys}/{bp_dia} mmHg\n"
            "- Nhip tho: {resp} lan/phut\n"
            "- SpO2: {spo2}%\n"
            "- BMI: {bmi:.1f}\n\n"
            "KHAM THUC THE:\n{exam}\n\n"
            "CHAN DOAN SO BO: {diagnosis}\n"
            "KE HOACH: {plan}"
        ),
    },
    {
        "title": "Ghi chu lam sang - Tai kham",
        "content": (
            "BENH AN TAI KHAM\n"
            "Ngay: {date} | BS. {doctor}\n\n"
            "BENH NHAN TAI KHAM THEO HEN\n"
            "Chan doan truoc: {diagnosis}\n\n"
            "DIEN TIEN:\n{progress}\n\n"
            "KHAM HIEN TAI:\n"
            "- Huyet ap: {bp_sys}/{bp_dia} mmHg\n"
            "- Mach: {pulse} l/p\n\n"
            "DANH GIA: {assessment}\n"
            "DIEU CHINH: {adjustment}"
        ),
    },
]

DISCHARGE_SUMMARIES = [
    {
        "title": "Tom tat xuat vien",
        "content": (
            "TOM TAT XUAT VIEN\n"
            "Ngay nhap vien: {admit_date}\n"
            "Ngay xuat vien: {discharge_date}\n"
            "Bac si dieu tri: BS. {doctor}\n\n"
            "CHAN DOAN CHINH: {diagnosis}\n"
            "CHAN DOAN KEM THEO: {comorbid}\n\n"
            "TOM TAT QUA TRINH DIEU TRI:\n{course}\n\n"
            "THUOC XUAT VIEN:\n{meds}\n\n"
            "KE HOACH THEO DOI:\n{followup}\n"
            "TIEN LUONG: {prognosis}"
        ),
    },
]

IMAGING_REPORTS = [
    {
        "title": "Ket qua chup X-quang nguc",
        "content": (
            "KET QUA CHAN DOAN HINH ANH\n"
            "Phuong phap: X-quang nguc thang\n"
            "Ngay chup: {date}\n"
            "Bac si doc: BS. {doctor}\n\n"
            "MO TA HINH ANH:\n{findings}\n\n"
            "KET LUAN: {conclusion}\n"
            "DE NGHI: {recommendation}"
        ),
    },
    {
        "title": "Ket qua sieu am tong quat",
        "content": (
            "KET QUA SIEU AM\n"
            "Phuong phap: Sieu am {region}\n"
            "Ngay: {date} | BS. {doctor}\n\n"
            "MO TA:\n{findings}\n\n"
            "KICH THUOC: {measurements}\n"
            "KET LUAN: {conclusion}"
        ),
    },
]

PRESCRIPTIONS = [
    {
        "title": "Don thuoc dieu tri ngoai tru",
        "content": (
            "DON THUOC\n"
            "Ngay ke: {date} | BS. {doctor}\n"
            "Chan doan: {diagnosis}\n\n"
            "THUOC DIEU TRI:\n{med_list}\n\n"
            "HUONG DAN:\n- Uong thuoc dung gio, dung lieu\n"
            "- {special_instruction}\n"
            "- Tai kham sau {followup_days} ngay neu khong do\n\n"
            "TONG SO THUOC: {med_count} loai"
        ),
    },
]

ENCOUNTER_NOTES = [
    {
        "title": "Phieu kham benh",
        "content": (
            "PHIEU KHAM BENH (SOAP)\n"
            "Ngay: {date} | BS. {doctor}\n\n"
            "S - CHU QUAN (Subjective):\n{subjective}\n\n"
            "O - KHACH QUAN (Objective):\n{objective}\n\n"
            "A - DANH GIA (Assessment):\n{assessment}\n\n"
            "P - KE HOACH (Plan):\n{plan}"
        ),
    },
]


def gen_date(seed):
    rng = random.Random(seed)
    y = rng.randint(2023, 2026)
    m = rng.randint(1, 12)
    d = rng.randint(1, 28)
    return f"{d:02d}/{m:02d}/{y}"


DO_NAMES = ["Tran Van Minh", "Nguyen Thi Lan", "Le Hoang Phuc"]


def gen_lab_result(rng):
    template = rng.choice(LAB_RESULTS)
    abnormal = rng.random() < 0.35
    c_norm = ["Cac chi so trong gioi han binh thuong.", "Khong phat hien bat thuong."]
    c_ab = ["Phat hien tang nhe men gan, can theo doi them.", "HbA1c tang, de nghi kiem soat duong huyet chat che hon."]
    return template["title"], template["content"].format(
        date=gen_date(rng.randint(1, 1000)),
        rbc=round(rng.uniform(3.5, 6.0), 2),
        hgb=round(rng.uniform(11.0, 16.5), 1),
        hct=round(rng.uniform(35.0, 48.0), 1),
        wbc=round(rng.uniform(3.5, 11.0), 1),
        plt=rng.randint(130, 420),
        glu=round(rng.uniform(4.0, 9.0), 1),
        hba1c=round(rng.uniform(5.0, 8.5), 1),
        cre=round(rng.uniform(55, 140), 1),
        ast=rng.randint(15, 60),
        alt=rng.randint(12, 65),
        chol=round(rng.uniform(3.5, 6.5), 1),
        tg=round(rng.uniform(0.8, 2.5), 1),
        color=rng.choice(["Vang nhat", "Vang", "Vang dam"]),
        clarity=rng.choice(["Trong", "Hoi duc"]),
        ph=round(rng.uniform(5.0, 7.5), 1),
        protein=rng.choice(["Am tinh", "Am tinh", "Vet"]),
        glucose=rng.choice(["Am tinh", "Am tinh", "Am tinh", "Duong tinh (+)"]),
        rbc_urine=rng.choice(["0-1", "0-2", "1-3", "2-5"]),
        wbc_urine=rng.choice(["0-2", "0-5", "2-8"]),
        conclusion=rng.choice(c_ab if abnormal else c_norm),
        doctor=rng.choice(DO_NAMES),
    )


def gen_clinical_note(rng):
    template = rng.choice(CLINICAL_NOTES)
    reasons = ["Dau nguc", "Kho tho", "Dau dau keo dai", "Met moi", "Sot", "Dau bung", "Ho khan"]
    histories = ["Tang huyet ap 5 nam, dang dung Lisinopril.", "Dai thao duong type 2.", "Khong co tien su benh."]
    exams = ["Tim deu, phoi khong rale, bung mem.", "Phoi co rale am day phai.", "Kham trong gioi han binh thuong."]
    diagnoses = ["Tang huyet ap vo can", "Dai thao duong type 2", "Viem phe quan cap", "Roi loan lipid mau"]
    return template["title"], template["content"].format(
        date=gen_date(rng.randint(1, 1000)),
        reason=rng.choice(reasons),
        history=rng.choice(histories),
        temp=round(rng.uniform(36.5, 39.0), 1),
        pulse=rng.randint(60, 110),
        bp_sys=rng.randint(100, 160),
        bp_dia=rng.randint(60, 100),
        resp=rng.randint(14, 28),
        spo2=rng.randint(94, 100),
        bmi=round(rng.uniform(18.5, 32.0), 1),
        exam=rng.choice(exams),
        diagnosis=rng.choice(diagnoses),
        plan="Tiep tuc theo doi va dieu tri theo phac do." if rng.random() > 0.3 else "Can lam them xet nghiem.",
        progress="Benh nhan dap ung tot." if rng.random() > 0.3 else "Benh nhan con met, can theo doi them.",
        assessment="On dinh." if rng.random() > 0.3 else "Can dieu chinh lieu thuoc.",
        adjustment="Giu nguyen phac do." if rng.random() > 0.5 else "Tang lieu Metformin len 1000mg/ngay.",
        doctor=rng.choice(DO_NAMES),
    )


def gen_discharge_summary(rng):
    template = rng.choice(DISCHARGE_SUMMARIES)
    diagnoses = ["Viem phoi cong dong", "Nhoi mau co tim cap", "Dot quy thieu mau nao", "Suy tim sung huyet"]
    return template["title"], template["content"].format(
        admit_date=gen_date(rng.randint(1, 1000)),
        discharge_date=gen_date(rng.randint(1001, 2000)),
        diagnosis=rng.choice(diagnoses),
        comorbid="Tang huyet ap, Dai thao duong type 2" if rng.random() > 0.4 else "Khong",
        course=f"Benh nhan nhap vien trong tinh trang {rng.choice(['kho tho','dau nguc','sot cao'])}. "
               f"Dap ung tot voi {rng.choice(['khang sinh','thuoc van mach','thuoc loi tieu'])}.",
        meds="- {} 10mg, 1 vien/ngay\n- {} 500mg, 2 vien/ngay".format(
            rng.choice(["Amlodipine", "Lisinopril", "Losartan"]),
            rng.choice(["Metformin", "Atorvastatin", "Clopidogrel"]),
        ),
        followup="Tai kham sau 2 tuan tai phong kham Noi Tim Mach.",
        prognosis="Tot neu tuan thu dieu tri.",
        doctor=rng.choice(["BS. Tran Van Minh", "BS. Nguyen Thi Lan"]),
    )


def gen_imaging_report(rng):
    template = rng.choice(IMAGING_REPORTS)
    findings_list = [
        "Bong tim khong to, phoi sang khong ton thuong khu tru.",
        "Co hinh anh tham nhiem day phoi phai, khong tran dich mang phoi.",
        "Bong tim to nhe, phoi co dau hieu u huyet nhe.",
        "Cau truc nhu mo dong nhat, khong phat hien khoi u hay nang.",
    ]
    return template["title"], template["content"].format(
        date=gen_date(rng.randint(1, 1000)),
        region=rng.choice(["bung tong quat", "tuyen giap", "tim", "o bung"]),
        measurements="Kich thuoc trong gioi han binh thuong.",
        findings=rng.choice(findings_list),
        conclusion="Binh thuong" if rng.random() > 0.3 else "Can theo doi them",
        recommendation="Chup CT neu trieu chung khong cai thien." if rng.random() > 0.5 else "Khong can can thiep them.",
        doctor=rng.choice(["BS. Tran Van Minh", "BS. Le Hoang Phuc"]),
    )


def gen_prescription(rng):
    template = rng.choice(PRESCRIPTIONS)
    meds_data = [
        ("Amlodipine", "5mg", "1 vien/ngay", "sang"),
        ("Metformin", "500mg", "2 vien/ngay", "sang - toi"),
        ("Atorvastatin", "10mg", "1 vien/ngay", "toi"),
        ("Lisinopril", "10mg", "1 vien/ngay", "sang"),
        ("Omeprazole", "20mg", "1 vien/ngay", "truoc an 30p"),
        ("Paracetamol", "500mg", "3 vien/ngay", "khi dau"),
        ("Amoxicillin", "500mg", "3 vien/ngay", "sau an"),
    ]
    selected = rng.sample(meds_data, rng.randint(2, 4))
    med_list = "\n".join(f"- {m[0]} {m[1]}, {m[2]} ({m[3]})" for m in selected)
    return template["title"], template["content"].format(
        date=gen_date(rng.randint(1, 1000)),
        diagnosis=rng.choice(["Tang huyet ap", "Dai thao duong", "Roi loan lipid mau", "Viem da day"]),
        med_list=med_list,
        special_instruction=rng.choice(["Uong nhieu nuoc", "Tranh ruou bia", "Theo doi huyet ap hang ngay"]),
        followup_days=rng.choice([7, 14, 30]),
        med_count=len(selected),
        doctor=rng.choice(["BS. Nguyen Thi Lan", "BS. Le Hoang Phuc"]),
    )


def gen_encounter_note(rng):
    template = rng.choice(ENCOUNTER_NOTES)
    return template["title"], template["content"].format(
        date=gen_date(rng.randint(1, 1000)),
        subjective=rng.choice([
            "Benh nhan than dau dau 3 ngay, dau tang khi van dong.",
            "Benh nhan ho khan 1 tuan, khong sot, khong kho tho.",
            "Benh nhan met moi keo dai, an uong kem.",
        ]),
        objective=f"Mach {rng.randint(65,100)} l/p, HA {rng.randint(100,150)}/{rng.randint(60,95)}, "
                  f"nhiet do {rng.uniform(36.5,38.5):.1f} do C, SpO2 {rng.randint(94,99)}%.",
        assessment=rng.choice([
            "Dau dau cang co, chua loai tru nguyen nhan mach mau.",
            "Viem hong cap, khong bien chung.",
            "Suy nhuoc co the, can kiem tra cong thuc mau.",
        ]),
        plan="Ke don thuoc dieu tri trieu chung, hen tai kham sau 1 tuan.",
        doctor=rng.choice(["BS. Nguyen Thi Lan", "BS. Tran Van Minh"]),
    )


GENERATORS = {
    "lab_result": gen_lab_result,
    "clinical_note": gen_clinical_note,
    "discharge_summary": gen_discharge_summary,
    "imaging_report": gen_imaging_report,
    "prescription": gen_prescription,
    "encounter_note": gen_encounter_note,
}

TYPE_WEIGHTS = [
    ("lab_result", 25), ("clinical_note", 20), ("discharge_summary", 10),
    ("imaging_report", 15), ("prescription", 20), ("encounter_note", 10),
]


async def generate():
    async for session in get_session():
        result = await session.execute(
            select(Patient).where(Patient.deleted_at.is_(None)).order_by(Patient.mrn)
        )
        patients = result.scalars().all()
        print(f"Found {len(patients)} patients")

        type_pool = []
        for doc_type, weight in TYPE_WEIGHTS:
            type_pool.extend([doc_type] * weight)
        random.Random(42).shuffle(type_pool)

        existing = await session.execute(select(Document.storage_uri))
        existing_uris = {row[0] for row in existing.all()}

        created = 0
        skipped = 0

        for i, patient in enumerate(patients):
            if created >= 100:
                break
            num_docs = 1
            if i < 20 and created + 3 <= 100:
                num_docs = 3
            elif i < 50 and created + 2 <= 100:
                num_docs = 2

            for _ in range(num_docs):
                if created >= 100:
                    break
                doc_type = type_pool[created % len(type_pool)]
                gen_func = GENERATORS[doc_type]
                rng = random.Random(4200 + created)
                title, content = gen_func(rng)

                doc_id = uuid.UUID(f"{DOC_UUID_PREFIX}{created + 3:012d}")
                storage_uri = f"seed://{doc_id}"

                if storage_uri in existing_uris:
                    skipped += 1
                    continue

                doc = Document(
                    id=doc_id,
                    patient_id=patient.id,
                    uploaded_by=DOCTOR_ID,
                    title=title,
                    document_type=doc_type,
                    storage_uri=storage_uri,
                    mime_type="text/plain",
                    status="indexed",
                    page_count=1,
                    indexed_source_sha256=hashlib.sha256(content.encode()).hexdigest(),
                    index_generation=1,
                )
                session.add(doc)
                await session.flush()

                page = DocumentPage(
                    document_id=doc.id,
                    page_number=1,
                    ocr_text=content,
                    ocr_confidence=1.0,
                )
                session.add(page)
                await session.flush()

                chunk = DocumentChunk(
                    document_id=doc.id,
                    page_id=page.id,
                    patient_id=patient.id,
                    chunk_index=0,
                    content=content,
                    token_count=len(content.split()),
                    embedding=deterministic_embedding(content),
                    meta={"doc_type": doc_type, "page_number": 1},
                )
                session.add(chunk)
                created += 1

                if created % 25 == 0:
                    await session.commit()
                    print(f"  ... {created} documents ...")

        await session.commit()
        print(f"Done: {created} created, {skipped} skipped (exists)")
        print(f"Total docs: {len(existing_uris) + created}")
        break


if __name__ == "__main__":
    asyncio.run(generate())
