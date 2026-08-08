"""Hospital AI backend package."""

from __future__ import annotations

import datetime
from datetime import timezone

if not hasattr(datetime, "UTC"):
    datetime.UTC = timezone.utc  # noqa: UP017
