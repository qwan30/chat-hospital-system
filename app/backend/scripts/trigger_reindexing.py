import asyncio

from sqlalchemy import select

from hospital_ai.core.config import get_settings
from hospital_ai.db.models import Document
from hospital_ai.db.session import get_session_factory
from hospital_ai.workers.jobs import process_document


async def main():
    settings = get_settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        result = await session.execute(select(Document))
        documents = result.scalars().all()

        for doc in documents:
            doc.status = "uploaded"
            doc.indexed_source_sha256 = None
        await session.commit()

        print(f"Triggering re-indexing for {len(documents)} documents...")
        for doc in documents:
            print(f"Processing document {doc.id}...")
            await process_document(session, doc.id, settings)

    print("Re-indexing complete.")


if __name__ == "__main__":
    asyncio.run(main())
