"""Shared rate limiter for the Hospital AI API.

Import this limiter instance in route modules and apply via decorator:
    from hospital_ai.api.limiter import limiter

    @router.post("/ask")
    @limiter.limit("10/minute")
    async def chat_ask(request: Request, ...):
        ...
"""
from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiting is enabled by default and must be opted out of explicitly.
# Defaulting TESTING to "false" keeps this control fail-closed: an environment
# that forgets to set it gets protection rather than silently losing it.
# The test suite and local dev set TESTING=true to disable.
is_testing = os.getenv("TESTING", "false").lower() in ("true", "1", "yes")
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"], enabled=not is_testing)
