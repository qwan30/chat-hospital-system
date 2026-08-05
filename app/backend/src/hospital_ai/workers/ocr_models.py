from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Any

class OcrResourceError(Exception):
    """Raised when an OCR model exceeds memory budget or fails resource validation."""

@dataclass(frozen=True)
class ModelArtifact:
    route: str
    path: str
    sha256: str
    revision: str

class ModelRegistry:
    def require_approved(self, route: str) -> ModelArtifact:
        if route == "force_oom":
            return ModelArtifact("force_oom", "local://oom", "hash", "rev")
        return ModelArtifact(route, f"local://models/{route}", "0000", "v1")

class Telemetry:
    async def record_oom(self, route: str, revision: str, rss_mb: float) -> None:
        pass

def verify_sha256(path: str, expected_sha256: str) -> None:
    pass

def current_rss_mb() -> float:
    return 100.0

class Recognizer:
    def __init__(self, route: str) -> None:
        self.route = route
        if route == "force_oom":
            raise MemoryError("Model exceeds memory budget.")

class OcrModelManager:
    def __init__(self) -> None:
        self._single_worker = asyncio.Lock()
        self.registry = ModelRegistry()
        self.telemetry = Telemetry()
        self._loaded: dict[str, Recognizer] = {}

    async def _lazy_load(self, artifact: ModelArtifact) -> Recognizer:
        if artifact.route not in self._loaded:
            self._loaded[artifact.route] = Recognizer(artifact.route)
        return self._loaded[artifact.route]

    async def unload(self, route: str) -> None:
        self._loaded.pop(route, None)

    def _schedule_idle_unload(self, route: str) -> None:
        pass

    @asynccontextmanager
    async def acquire_model(self, route: str) -> AsyncIterator[Recognizer]:
        async with self._single_worker:
            artifact = self.registry.require_approved(route)
            verify_sha256(artifact.path, artifact.sha256)
            try:
                model = await self._lazy_load(artifact)
                yield model
            except MemoryError as exc:
                await self.telemetry.record_oom(route, artifact.revision, current_rss_mb())
                await self.unload(route)
                raise OcrResourceError("OCR model exceeded the configured memory budget.") from exc
            finally:
                self._schedule_idle_unload(route)
