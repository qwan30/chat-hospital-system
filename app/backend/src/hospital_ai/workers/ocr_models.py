from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class OcrResourceError(Exception):
    """Raised when an OCR model exceeds memory budget or fails resource validation."""


@dataclass(frozen=True)
class ModelArtifact:
    route: str
    path: str
    sha256: str
    revision: str


class ModelRegistry:
    def __init__(self, artifacts: Optional[Mapping[str, ModelArtifact]] = None) -> None:
        self._artifacts = dict(artifacts or {})

    @classmethod
    def from_manifest(cls, path: str | Path) -> ModelRegistry:
        manifest_path = Path(path)
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OcrResourceError("Approved OCR model manifest is unavailable or invalid.") from exc
        records = payload.get("models", payload) if isinstance(payload, dict) else None
        if not isinstance(records, dict):
            raise OcrResourceError("Approved OCR model manifest has an invalid shape.")
        artifacts: dict[str, ModelArtifact] = {}
        for route, value in records.items():
            if not isinstance(value, dict):
                raise OcrResourceError("Approved OCR model manifest contains an invalid entry.")
            try:
                artifacts[route] = ModelArtifact(
                    route=route,
                    path=str(value["path"]),
                    sha256=str(value["sha256"]),
                    revision=str(value["revision"]),
                )
            except KeyError as exc:
                raise OcrResourceError("Approved OCR model manifest is missing required metadata.") from exc
        return cls(artifacts)

    def require_approved(self, route: str) -> ModelArtifact:
        artifact = self._artifacts.get(route)
        if not artifact or not artifact.path or not artifact.revision:
            raise OcrResourceError(f"No approved OCR model artifact is registered for route {route}.")
        if len(artifact.sha256) != 64 or any(char not in "0123456789abcdefABCDEF" for char in artifact.sha256):
            raise OcrResourceError("Approved OCR model artifact has an invalid SHA-256.")
        return artifact


class Telemetry:
    def __init__(self) -> None:
        self.oom_events: list[dict[str, object]] = []
        self.fallback_events: list[dict[str, object]] = []

    async def record_oom(self, route: str, revision: str, rss_mb: float) -> None:
        self.oom_events.append({"route": route, "revision": revision, "rss_mb": rss_mb})

    async def record_fallback(self, from_route: str, to_route: str, reason: str) -> None:
        self.fallback_events.append({"from_route": from_route, "to_route": to_route, "reason": reason})


def verify_sha256(path: str, expected_sha256: str) -> None:
    if not path or "://" in path:
        raise OcrResourceError("OCR model artifact must be a local file.")
    if len(expected_sha256) != 64 or any(char not in "0123456789abcdefABCDEF" for char in expected_sha256):
        raise OcrResourceError("OCR model artifact has an invalid expected SHA-256.")
    artifact_path = Path(path)
    if not artifact_path.is_file():
        raise OcrResourceError("OCR model artifact file is unavailable.")
    digest = hashlib.sha256()
    try:
        with artifact_path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise OcrResourceError("Unable to read OCR model artifact.") from exc
    if not hmac.compare_digest(digest.hexdigest(), expected_sha256.lower()):
        raise OcrResourceError("OCR model artifact SHA-256 does not match its approved manifest.")


def current_rss_mb() -> float:
    try:
        import psutil

        return float(psutil.Process(os.getpid()).memory_info().rss) / (1024 * 1024)
    except (ImportError, OSError):
        try:
            import resource

            return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024
        except (ImportError, OSError):
            return 0.0


class Recognizer:
    def __init__(self, artifact: ModelArtifact) -> None:
        self.route = artifact.route
        self.artifact = artifact
        if artifact.route == "force_oom":
            raise MemoryError("Model exceeds memory budget.")


class OcrModelManager:
    def __init__(
        self,
        *,
        registry: Optional[ModelRegistry] = None,
        memory_budget_mb: int = 4096,
        idle_unload_seconds: float = 300.0,
    ) -> None:
        self._single_worker = asyncio.Lock()
        self.registry = registry or ModelRegistry()
        self.memory_budget_mb = memory_budget_mb
        self.idle_unload_seconds = idle_unload_seconds
        self.telemetry = Telemetry()
        self._loaded: dict[str, Recognizer] = {}
        self._idle_unload_handles: dict[str, asyncio.TimerHandle] = {}

    async def _lazy_load(self, artifact: ModelArtifact) -> Recognizer:
        if artifact.route not in self._loaded:
            self._loaded[artifact.route] = Recognizer(artifact)
        return self._loaded[artifact.route]

    async def unload(self, route: str) -> None:
        self._loaded.pop(route, None)
        handle = self._idle_unload_handles.pop(route, None)
        if handle is not None:
            handle.cancel()

    def _schedule_idle_unload(self, route: str) -> None:
        previous = self._idle_unload_handles.pop(route, None)
        if previous is not None:
            previous.cancel()
        loop = asyncio.get_running_loop()
        self._idle_unload_handles[route] = loop.call_later(
            self.idle_unload_seconds,
            lambda: asyncio.create_task(self.unload(route)),
        )

    @classmethod
    def from_settings(cls, settings, *, registry: Optional[ModelRegistry] = None) -> OcrModelManager:
        if registry is None:
            manifest_path = getattr(settings, "ocr_model_manifest_path", None)
            if manifest_path is None:
                default_manifest = Path(getattr(settings, "ocr_models_path", ".models")) / "manifest.json"
                if default_manifest.is_file():
                    manifest_path = default_manifest
            if manifest_path is not None and Path(manifest_path).is_file():
                registry = ModelRegistry.from_manifest(manifest_path)
            else:
                registry = ModelRegistry()
        return cls(
            registry=registry,
            memory_budget_mb=settings.ocr_memory_budget_mb,
            idle_unload_seconds=settings.ocr_idle_unload_seconds,
        )

    @asynccontextmanager
    async def acquire_model(self, route: str) -> AsyncIterator[Recognizer]:
        async with self._single_worker:
            if self.memory_budget_mb <= 4096:
                for loaded_route in list(self._loaded.keys()):
                    if loaded_route != route:
                        await self.unload(loaded_route)
            artifact = self.registry.require_approved(route)
            pending = self._idle_unload_handles.pop(route, None)
            if pending is not None:
                pending.cancel()
            verify_sha256(artifact.path, artifact.sha256)
            try:
                model = await self._lazy_load(artifact)
                if current_rss_mb() > self.memory_budget_mb:
                    raise MemoryError("OCR model exceeds the configured memory budget.")
                yield model
            except MemoryError as exc:
                await self.telemetry.record_oom(route, artifact.revision, current_rss_mb())
                await self.unload(route)
                raise OcrResourceError("OCR model exceeded the configured memory budget.") from exc
            except (RuntimeError, Exception) as exc:
                if "out of memory" in str(exc).lower() or "oom" in str(exc).lower() or "alloc" in str(exc).lower():
                    await self.telemetry.record_oom(route, artifact.revision, current_rss_mb())
                    await self.unload(route)
                    raise OcrResourceError("OCR model exceeded the configured memory budget.") from exc
                raise
            finally:
                if route in self._loaded:
                    self._schedule_idle_unload(route)

    @asynccontextmanager
    async def acquire_model_with_fallback(self, route: str) -> AsyncIterator[Recognizer]:
        fallback_map = {
            "vietocr_handwritten": "paddle_printed",
            "trocr_handwritten": "paddle_printed",
            "paddle_printed": "native",
            "force_oom": "native",
        }
        current_route = route
        yielded = False
        while True:
            try:
                async with self.acquire_model(current_route) as model:
                    yielded = True
                    yield model
                return
            except OcrResourceError as exc:
                if yielded:
                    raise
                fallback = fallback_map.get(current_route)
                if not fallback:
                    raise
                await self.telemetry.record_fallback(current_route, fallback, str(exc))
                current_route = fallback
