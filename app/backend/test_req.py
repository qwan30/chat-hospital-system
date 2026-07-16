import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        response = await client.post('http://127.0.0.1:8000/api/v1/chat/stream', json={'message': 'cảm ơn', 'patient_id': '30000000-0000-0000-0000-000000000001'}, headers={'Authorization': 'Bearer dev-admin'})
        print(response.text)

asyncio.run(test())
