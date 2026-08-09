import importlib.util
import re
import uuid
from pathlib import Path

import pytest

from hospital_ai.db.migrations import ADMIN_ID, PATIENT_ALICE_ID
from hospital_ai.db.models import Document

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = BACKEND_ROOT / "scripts"
LEGACY_STATUS_PATTERN = re.compile(r"status\s*=\s*['\"]indexed['\"]")
SCRIPT_PATHS = [
    "scripts/seed_dev.py",
    "scripts/seed_data.py",
    "scripts/seed_mock_clinical_notes.py",
    "scripts/run_rag_eval.py",
    "scripts/generate_documents.py",
    "scripts/demo_setup.py",
]


def _load_script_module(script_name: str):
    script_path = SCRIPT_DIR / script_name
    spec = importlib.util.spec_from_file_location(f"test_{script_name.replace('.', '_')}", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_seed_dev_add_document_creates_ready_document(session_and_settings):
    session, _settings = session_and_settings
    seed_dev = _load_script_module("seed_dev.py")
    doc_id = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
    chunk_id = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002")
    page_id = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000003")

    returned_chunk_id = await seed_dev._add_document(
        session,
        doc_id=doc_id,
        patient_id=PATIENT_ALICE_ID,
        uploader_id=ADMIN_ID,
        title="Seed status contract note",
        document_type="clinical_note",
        content="Synthetic note content for seed status contract coverage.",
        chunk_meta={"source": "seed-status-contract"},
        chunk_uuid=chunk_id,
        page_uuid=page_id,
    )

    document = await session.get(Document, doc_id)
    assert returned_chunk_id == chunk_id
    assert document is not None
    assert document.status == "ready"


@pytest.mark.parametrize("relative_path", SCRIPT_PATHS)
def test_seed_scripts_do_not_use_legacy_indexed_document_status(relative_path: str):
    source = (BACKEND_ROOT / relative_path).read_text(encoding="utf-8")
    assert LEGACY_STATUS_PATTERN.search(source) is None, relative_path
