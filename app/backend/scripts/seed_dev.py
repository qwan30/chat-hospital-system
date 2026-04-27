import asyncio

from hospital_ai.db.migrations import seed_synthetic_data
from hospital_ai.db.session import get_session_factory


async def main() -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        await seed_synthetic_data(session)
    print("Seeded synthetic users, patients, and permissions.")


if __name__ == "__main__":
    asyncio.run(main())
