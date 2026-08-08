from typing import Any

from pydantic import BaseModel


class DocumentGraphRead(BaseModel):
    mentions: list[dict[str, Any]]
    assertions: list[dict[str, Any]]
