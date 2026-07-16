"""Hospital AI backend package."""

import datetime
from datetime import timezone

if not hasattr(datetime, "UTC"):
    datetime.UTC = timezone.utc  # noqa: UP017
