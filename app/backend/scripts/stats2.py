import asyncio
import json

from sqlalchemy import text

from hospital_ai.core.config import get_settings
from hospital_ai.db.session import create_async_engine


async def main():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.connect() as conn:
        try:
            entities = await conn.scalar(text("SELECT COUNT(*) FROM graph_entities"))
            relations = await conn.scalar(text("SELECT COUNT(*) FROM graph_relations"))

            # drug entities maybe?
            drugs = await conn.scalar(
                text("SELECT COUNT(*) FROM graph_entities WHERE entity_type = 'medication' OR entity_type = 'drug'")
            )  # noqa: E501
        except Exception:
            entities = 0
            relations = 0
            drugs = 0

        print(json.dumps({"graph_entities": entities, "graph_relations": relations, "drug_entities": drugs}))


if __name__ == "__main__":
    asyncio.run(main())
