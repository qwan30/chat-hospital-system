from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock


class MockPage:
    def __init__(self, page_or_text):
        self.page = page_or_text
        if isinstance(page_or_text, str):
            self.inserted_text = page_or_text
        else:
            self.inserted_text = ""

    def get_text(self, *args, **kwargs):
        if self.inserted_text:
            return self.inserted_text
        if hasattr(self.page, "extract_text") and not isinstance(self.page, MagicMock):
            return self.page.extract_text()
        return "Mocked PDF text"

    def insert_text(self, point, text, *args, **kwargs):
        self.inserted_text += text + "\n"

    def get_pixmap(self, *args, **kwargs):
        class MockPixmap:
            def __init__(self):
                self.h = 100
                self.w = 100
                self.height = 100
                self.width = 100
                self.n = 3
                self.samples = b"\x00" * (100 * 100 * 3)

            def tobytes(self, fmt="png"):
                return b"\x89PNGfake_png_data"

        return MockPixmap()


class MockFitzDoc:
    def __init__(self, path=None, from_json=None):
        if from_json is not None:
            self.pages = [MockPage(t) for t in from_json]
        elif path is not None:
            try:
                from pathlib import Path

                content = Path(path).read_bytes()
                if content.startswith(b"["):
                    from_json = json.loads(content)
                    self.pages = [MockPage(t) for t in from_json]
                    return
            except Exception:
                pass
            import pypdf

            self.reader = pypdf.PdfReader(str(path))
            self.pages = [MockPage(p) for p in self.reader.pages]
        else:
            self.pages = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __len__(self):
        return len(self.pages)

    @property
    def page_count(self):
        return len(self.pages)

    def __iter__(self):
        return iter(self.pages)

    def __getitem__(self, idx):
        return self.pages[idx]

    def load_page(self, idx):
        return self.pages[idx]

    def new_page(self, *args, **kwargs):
        page = MockPage(MagicMock())
        self.pages.append(page)
        return page

    def tobytes(self):
        return json.dumps([p.inserted_text for p in self.pages]).encode("utf-8")

    def save(self, path):
        with open(path, "wb") as f:
            f.write(self.tobytes())

    def close(self):
        pass


class MockPixmap:
    def __init__(self, *args, **kwargs):
        if len(args) >= 4 and isinstance(args[3], bytes):
            self.samples = b"\x89PNG" + args[3]
        else:
            self.samples = b"\x89PNGfake_png_data"

    def tobytes(self, fmt="png"):
        return self.samples


class MockFitz(MagicMock):
    FileDataError = type("FileDataError", (Exception,), {})
    csRGB = "csRGB"
    Pixmap = MockPixmap

    def open(self, *args, **kwargs):
        if args:
            return MockFitzDoc(path=args[0])
        if "stream" in kwargs:
            stream = kwargs["stream"]
            if isinstance(stream, bytes):
                try:
                    return MockFitzDoc(from_json=json.loads(stream.decode("utf-8")))
                except Exception:
                    pass
                import io

                stream = io.BytesIO(stream)
            try:
                return MockFitzDoc(path=stream)
            except Exception:
                return MockFitzDoc()
        return MockFitzDoc()


sys.modules["fitz"] = MockFitz()


class MockNumpyArray:
    def __init__(self, shape=(100, 100, 3), seed=None):
        self.shape = tuple(shape)
        self.seed = seed

    def copy(self):
        return MockNumpyArray(self.shape, self.seed)

    def tobytes(self):
        if self.seed is not None:
            return f"fake_png_data_seed_{self.seed}".encode()
        return b"fake_png_data"

    def __floordiv__(self, other):
        return self

    def astype(self, dtype):
        return self

    def __add__(self, other):
        if isinstance(other, MockNumpyArray) and other.seed is not None:
            self.seed = other.seed
        return self

    def __mul__(self, other):
        return self

    def __getitem__(self, item):
        return self

    def __setitem__(self, key, value):
        pass


class MockNumpy(MagicMock):
    uint8 = "uint8"
    int16 = "int16"

    def frombuffer(self, *args, **kwargs):
        class MockReshape:
            def reshape(self, *shape):
                return MockNumpyArray(shape)

        return MockReshape()

    def ascontiguousarray(self, a, *args, **kwargs):
        return a

    def full(self, shape, *args, **kwargs):
        return MockNumpyArray(shape)

    def zeros(self, shape, *args, **kwargs):
        return MockNumpyArray(shape)

    def clip(self, a, *args):
        return a

    float32 = "float32"

    class random:
        @staticmethod
        def default_rng(seed):
            class MockRng:
                def __init__(self, seed):
                    self.seed = seed

                def normal(self, *args, **kwargs):
                    return MockNumpyArray(seed=self.seed)

            return MockRng(seed)


sys.modules["numpy"] = MockNumpy()

import os  # noqa: E402
import sys  # noqa: E402
import uuid  # noqa: E402
from collections.abc import AsyncIterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

# Rate limiting is fail-closed (enabled unless TESTING opts out), and
# hospital_ai.api.limiter reads this at import time — so it must be set
# before any hospital_ai module is imported below.
os.environ.setdefault("TESTING", "true")

# Match the CI backend-test job (ci.yml sets HOSPITAL_AI_DISABLE_GUARDRAILS=true).
# The guardrail scanners are ONNX models that take ~4-8s per scan on CPU; running
# them for real makes the suite slow and timing-dependent. Tests that exercise
# guardrail behaviour patch the scanners directly instead.
os.environ.setdefault("HOSPITAL_AI_DISABLE_GUARDRAILS", "true")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # noqa: E402

import datetime  # noqa: E402
from datetime import timezone  # noqa: E402

if not hasattr(datetime, "UTC"):  # noqa: E402
    datetime.UTC = timezone.utc  # noqa: E402, UP017

from hospital_ai.core.config import Settings  # noqa: E402
from hospital_ai.db.migrations import seed_synthetic_data  # noqa: E402
from hospital_ai.db.models import Base, Document, DocumentChunk, DocumentPage  # noqa: E402
from hospital_ai.services.embeddings import deterministic_embedding  # noqa: E402


@pytest.fixture(autouse=True)
def mock_extract_entities_and_relations_nlp(monkeypatch):
    from hospital_ai.services.graph_rag import ExtractedEntity, ExtractedRelation

    async def mock_extract_nlp(content):
        entities = []
        relations = []

        if "metformin" in content.lower():
            entities.append(ExtractedEntity("metformin", "drug"))
        if "diabetes" in content.lower():
            entities.append(ExtractedEntity("diabetes", "condition"))
            relations.append(ExtractedRelation("metformin", "diabetes", "treats"))
        if "lisinopril" in content.lower():
            entities.append(ExtractedEntity("lisinopril", "drug"))
        if "hypertension" in content.lower():
            entities.append(ExtractedEntity("hypertension", "condition"))
        if "lisinopril" in content.lower() and "hypertension" in content.lower():
            relations.append(ExtractedRelation("lisinopril", "hypertension", "treats"))
        if "aspirin" in content.lower():
            entities.append(ExtractedEntity("aspirin", "drug"))
        if "metformin" in content.lower() and "aspirin" in content.lower():
            # Add an explicit relation to simulate the test's expectation for Bob's text
            relations.append(ExtractedRelation("metformin", "aspirin", "prescribed_for"))

        return entities, relations

    monkeypatch.setattr("hospital_ai.services.graph_rag.extract_entities_and_relations_nlp", mock_extract_nlp)


@pytest_asyncio.fixture
async def session_and_settings(tmp_path: Path) -> AsyncIterator[tuple[AsyncSession, Settings]]:
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        storage_root=tmp_path / "storage",
        worker_inline=True,
        embedding_provider="deterministic",
        chat_provider="stub",
        evidence_threshold=0.0,
    )
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        await seed_synthetic_data(session)
        yield session, settings

    await engine.dispose()


async def create_indexed_document(
    session: AsyncSession,
    *,
    patient_id: uuid.UUID,
    uploaded_by: uuid.UUID,
    title: str,
    content: str,
) -> Document:
    import hashlib

    from hospital_ai.db.clinical_documents import (
        DocumentIndexGeneration,
        DocumentPageRevision,
        DocumentRevisionSet,
    )

    document = Document(
        patient_id=patient_id,
        uploaded_by=uploaded_by,
        title=title,
        document_type="note",
        storage_uri="memory://synthetic",
        mime_type="text/plain",
        status="ready",
        page_count=1,
    )
    session.add(document)
    await session.flush()

    page = DocumentPage(
        document_id=document.id,
        page_number=1,
        ocr_text=content,
        ocr_confidence=1.0,
    )
    session.add(page)
    await session.flush()

    content_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    page_rev = DocumentPageRevision(
        id=uuid.uuid4(),
        document_id=document.id,
        page_number=1,
        revision_number=1,
        revision_type="machine_ocr",
        raw_text_snapshot=content,
        corrected_text=content,
        confidence=1.0,
        status="approved",
        created_by_user_id=uploaded_by,
        content_sha256=content_sha,
        version=1,
    )
    session.add(page_rev)
    await session.flush()

    rev_set = DocumentRevisionSet(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_number=1,
        status="approved",
        created_by_user_id=uploaded_by,
        submitted_at=datetime.datetime.now(datetime.UTC),
        approved_by_user_id=uploaded_by,
        approved_at=datetime.datetime.now(datetime.UTC),
    )
    session.add(rev_set)
    await session.flush()

    gen = DocumentIndexGeneration(
        id=uuid.uuid4(),
        document_id=document.id,
        revision_set_id=rev_set.id,
        state="active",
        revision_set_sha256=content_sha,
        generation_sha256=content_sha,
        created_at=datetime.datetime.now(datetime.UTC),
        started_at=datetime.datetime.now(datetime.UTC),
        activated_at=datetime.datetime.now(datetime.UTC),
    )
    session.add(gen)
    await session.flush()

    document.approved_revision_set_id = rev_set.id
    document.active_index_generation_id = gen.id

    session.add(
        DocumentChunk(
            document_id=document.id,
            page_id=page.id,
            patient_id=patient_id,
            chunk_index=0,
            content=content,
            token_count=len(content.split()),
            embedding=deterministic_embedding(content),
            meta={"page_number": 1},
            generation_id=gen.id,
            revision_set_id=rev_set.id,
            page_revision_id=page_rev.id,
            approval_state="approved",
            source_text_sha256=content_sha,
            text_start_offset=0,
            text_end_offset=len(content),
        )
    )
    await session.commit()
    return document
