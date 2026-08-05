"""
Bulk import patients from the normalized CSV seed file with exact UUIDs.

Usage:
  python scripts/import_patients_seed.py --file data/metadata/generated_patients_seed.csv
"""

import argparse
import csv
import datetime
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

DOCTOR_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
RECORDS_ID = uuid.UUID("10000000-0000-0000-0000-000000000002")
ADMIN_ID = uuid.UUID("10000000-0000-0000-0000-000000000004")
NURSE_ID = uuid.UUID("10000000-0000-0000-0000-000000000005")
PHARMACIST_ID = uuid.UUID("10000000-0000-0000-0000-000000000006")


def parse_args():
    p = argparse.ArgumentParser(description="Bulk import patients from normalized CSV seed")
    p.add_argument("--file", required=True, help="Path to generated_patients_seed.csv")
    p.add_argument("--dry-run", action="store_true", help="Validate only, no insert")
    return p.parse_args()


def read_csv(path: Path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


async def import_patients(file_path: str, dry_run: bool = False):
    path = Path(file_path)
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        return

    rows = read_csv(path)
    print(f"Read {len(rows)} patient rows from {path.name}")

    if dry_run:
        print("[DRY RUN] Patient seed validation preview:")
        for r in rows[:5]:
            mrn = r.get("mrn") or ""
            name = r.get("full_name") or ""
            dob = r.get("dob") or ""
            masked_name = name[:2] + "*" * (len(name) - 2) if len(name) > 2 else "**"
            masked_dob = dob[:4] + "-**-**" if len(dob) > 4 else "****"
            print(f"  {mrn[:4]}... | {masked_name} | {masked_dob} | {r.get('department')} | {r.get('status')}")
        return

    from sqlalchemy import select

    from hospital_ai.db.models import Patient, PatientPermission
    from hospital_ai.db.session import get_session

    imported = 0
    skipped = 0
    perms_added = 0

    async for session in get_session():
        for row in rows:
            mrn = row["mrn"].strip()
            name = row["full_name"].strip()
            dob_str = (row.get("dob") or "").strip()
            department = (row.get("department") or "").strip()
            status = (row.get("status") or "active").strip().lower()
            patient_id_str = row["patient_id"].strip()
            patient_id = uuid.UUID(patient_id_str)

            existing = await session.execute(select(Patient).where(Patient.mrn == mrn))
            patient = existing.scalar_one_or_none()

            if patient is None:
                dob = datetime.date.fromisoformat(dob_str) if dob_str else None
                patient = Patient(
                    id=patient_id,
                    mrn=mrn,
                    full_name=name,
                    dob=dob,
                    department=department or None,
                    status=status,
                )
                session.add(patient)
                imported += 1
            else:
                skipped += 1
                # Ensure the ID matches
                if patient.id != patient_id:
                    print(f"  WARNING: Patient with MRN {mrn[:4]}... has different ID in DB than CSV")

            # Seed permissions for doctor, nurse, pharmacist, records, admin
            permissions = [
                # Doctor
                PatientPermission(user_id=DOCTOR_ID, patient_id=patient.id, scope="read"),
                PatientPermission(user_id=DOCTOR_ID, patient_id=patient.id, scope="summary"),
                PatientPermission(user_id=DOCTOR_ID, patient_id=patient.id, scope="medication"),
                # Nurse
                PatientPermission(user_id=NURSE_ID, patient_id=patient.id, scope="read"),
                PatientPermission(user_id=NURSE_ID, patient_id=patient.id, scope="summary"),
                # Pharmacist
                PatientPermission(user_id=PHARMACIST_ID, patient_id=patient.id, scope="read"),
                PatientPermission(user_id=PHARMACIST_ID, patient_id=patient.id, scope="medication"),
                # Records
                PatientPermission(user_id=RECORDS_ID, patient_id=patient.id, scope="upload"),
                # Admin
                PatientPermission(user_id=ADMIN_ID, patient_id=patient.id, scope="admin"),
            ]

            for perm in permissions:
                exists_perm = await session.execute(
                    select(PatientPermission).where(
                        PatientPermission.user_id == perm.user_id,
                        PatientPermission.patient_id == perm.patient_id,
                        PatientPermission.scope == perm.scope,
                    )
                )
                if exists_perm.scalar_one_or_none() is None:
                    session.add(perm)
                    perms_added += 1

        await session.commit()
        break

    print(
        f"\nImport Complete: Imported {imported} patients, skipped {skipped} "
        f"existing. Added {perms_added} permission records."
    )


if __name__ == "__main__":
    args = parse_args()
    import asyncio

    asyncio.run(import_patients(args.file, args.dry_run))
