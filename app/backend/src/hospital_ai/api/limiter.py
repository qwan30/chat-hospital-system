"""Shared rate limiter for the Hospital AI API.

Import this limiter instance in route modules and apply via decorator:
    from hospital_ai.api.limiter import limiter

    @router.post("/ask")
    @limiter.limit("10/minute")
    async def chat_ask(request: Request, ...):
        ...
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
