import asyncio

from sqlalchemy import select

from hospital_ai.db.models import Patient
from hospital_ai.db.session import get_session


async def main():
    async for session in get_session():
        res = await session.execute(select(Patient.id, Patient.full_name, Patient.mrn))
        for p in res.all():
            print(f"ID: {p[0]} | Name: {p[1]} | MRN: {p[2]}")
        break


if __name__ == "__main__":
    asyncio.run(main())
