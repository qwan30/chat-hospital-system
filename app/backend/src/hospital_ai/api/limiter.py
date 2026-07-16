"""Shared rate limiter for the Hospital AI API.

Import this limiter instance in route modules and apply via decorator:
    from hospital_ai.api.limiter import limiter

    @router.post("/ask")
    @limiter.limit("10/minute")
    async def chat_ask(request: Request, ...):
        ...
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# Disable rate limiting during development/testing
is_testing = os.getenv("TESTING", "true").lower() in ("true", "1", "yes")
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"], enabled=not is_testing)
