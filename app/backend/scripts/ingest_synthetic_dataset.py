"""
Ingest synthetic English dataset (global guidelines, drug safety, and 100 patients documents/labs).
Copies files to storage root, inserts Document records, runs OCR/parsing/embedding generation,
and propagates access_tags from metadata to document chunks.

Usage:
  python scripts/ingest_synthetic_dataset.py
"""

import asyncio
import json
import shutil
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import select

from hospital_ai.core.config import get_settings
from hospital_ai.db.models import Document, DocumentChunk, Patient
from hospital_ai.db.session import get_session
from hospital_ai.workers.jobs import process_document


def find_source_file(original_uri: str) -> Path:
    """Find source file path relative to current working directory (app/backend)."""
    p = Path(original_uri)
    if p.exists():
        return p
    # If path starts with app/backend, try stripping it
    parts = list(p.parts)
    if parts and parts[0] == "app":
        # check if it starts with app/backend
        if len(parts) > 1 and parts[1] == "backend":
            p2 = Path(*parts[2:])
            if p2.exists():
                return p2
    return p


async def ingest_file(session, row: dict, is_global: bool, settings) -> None:
    patient_id_str = row.get("patient_id")
    patient_id = uuid.UUID(patient_id_str) if patient_id_str else None

    # Deterministic Document UUID from storage_uri to allow re-runs
    doc_id = uuid.uuid5(uuid.NAMESPACE_DNS, row["storage_uri"])

    # Check if document already exists
    existing = await session.execute(select(Document).where(Document.id == doc_id))
    if existing.scalar_one_or_none() is not None:
        print(f"  [SKIP] Document {row['title']} ({doc_id}) already exists.")
        return

    # Find the source file on disk
    src_path = find_source_file(row["storage_uri"])
    if not src_path.exists():
        print(f"  [ERROR] Source file not found: {row['storage_uri']} (resolved to {src_path})")
        return

    # Copy to settings.storage_root/patients/<patient_id_or_global>/<doc_id>_<filename>
    folder_name = "global" if is_global else str(patient_id)
    target_dir = settings.storage_root / "patients" / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = src_path.name
    target_path = target_dir / f"{doc_id}_{filename}"

    shutil.copy2(src_path, target_path)

    # Insert Document
    doc = Document(
        id=doc_id,
        patient_id=patient_id,
        uploaded_by=uuid.UUID(row["uploaded_by"]),
        title=row["title"],
        document_type=row["document_type"],
        storage_uri=str(target_path),
        mime_type=row["mime_type"],
        status="uploaded",
    )
    session.add(doc)
    await session.commit()

    print(f"  [INGESTING] Processing {row['title']} ({doc_id}) ...")
    try:
        await process_document(session, doc_id, settings)
    except Exception as e:
        print(f"  [ERROR] Processing failed for {row['title']}: {e}")
        return

    # Refresh document
    await session.commit()
    existing = await session.execute(select(Document).where(Document.id == doc_id))
    doc = existing.scalar_one()
    if doc.status in ("ready", "ready_with_warnings", "indexed"):
        print(f"  [SUCCESS] Ready: {row['title']}")
        # Propagate access tags to chunks
        if "access_tags" in row and row["access_tags"]:
            chunk_result = await session.execute(select(DocumentChunk).where(DocumentChunk.document_id == doc_id))
            chunks = chunk_result.scalars().all()
            for chunk in chunks:
                meta = dict(chunk.meta or {})
                meta["access_tags"] = row["access_tags"]
                chunk.meta = meta
            await session.commit()
            print(f"    Added access_tags {row['access_tags']} to {len(chunks)} chunks.")
    else:
        print(f"  [FAILED] Document {row['title']} processing status: {doc.status}. Error: {doc.ocr_error}")


async def main():
    settings = get_settings()
    print(f"Starting ingestion of synthetic dataset. Storage root: {settings.storage_root}")

    global_meta_path = Path("data/metadata/global_ingestion_metadata.jsonl")
    patient_meta_path = Path("data/metadata/ingestion_metadata.jsonl")

    if not global_meta_path.exists():
        print(f"ERROR: Global metadata file not found at {global_meta_path}")
        return
    if not patient_meta_path.exists():
        print(f"ERROR: Patient metadata file not found at {patient_meta_path}")
        return

    # 1. Load global guidelines & drug databases
    print("\n--- Ingesting Global Guidelines & Drug Databases ---")
    with open(global_meta_path, encoding="utf-8") as f:
        global_rows = [json.loads(line) for line in f if line.strip()]

    async for session in get_session():
        for row in global_rows:
            await ingest_file(session, row, is_global=True, settings=settings)
        break

    # 2. Load patient documents and lab sheets
    print("\n--- Ingesting Patient Documents & Lab Sheets ---")
    with open(patient_meta_path, encoding="utf-8") as f:
        patient_rows = [json.loads(line) for line in f if line.strip()]

    async for session in get_session():
        # Quick validation: check patients exist
        patient_ids = {uuid.UUID(r["patient_id"]) for r in patient_rows if r.get("patient_id")}
        print(f"Checking {len(patient_ids)} target patients exist in the EMR database...")
        db_patients_result = await session.execute(select(Patient.id).where(Patient.id.in_(list(patient_ids))))
        existing_patient_ids = {row[0] for row in db_patients_result.all()}
        missing = patient_ids - existing_patient_ids
        if missing:
            print(f"WARNING: {len(missing)} patient IDs from ingestion metadata do not exist in the database!")
            print("Please run scripts/import_patients_seed.py first to seed patients.")
            # We will continue but skip documents for missing patients

        count = 0
        for row in patient_rows:
            p_id = uuid.UUID(row["patient_id"])
            if p_id not in existing_patient_ids:
                print(f"  [SKIP] Skipping doc {row['title']} because patient {p_id} does not exist.")
                continue

            await ingest_file(session, row, is_global=False, settings=settings)
            count += 1
            if count % 10 == 0:
                print(f"Processed {count}/{len(patient_rows)} patient documents.")
        break

    print("\nIngestion complete.")


if __name__ == "__main__":
    asyncio.run(main())
