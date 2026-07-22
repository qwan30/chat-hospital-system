"""Ingest the governed synthetic corpus with complete, idempotent accounting."""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
import uuid
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import select  # noqa: E402

from hospital_ai.core.config import get_settings  # noqa: E402
from hospital_ai.db.migrations import RECORDS_ID  # noqa: E402
from hospital_ai.db.models import Patient  # noqa: E402
from hospital_ai.db.session import get_session  # noqa: E402
from hospital_ai.evaluation.corpus import sha256_file  # noqa: E402
from hospital_ai.evaluation.ingestion import (  # noqa: E402
    IngestFileResult,
    IngestionRun,
    account_failure,
    ingest_one,
)
from hospital_ai.evaluation.models import CorpusFile, CorpusManifest  # noqa: E402
from hospital_ai.workers.jobs import process_document  # noqa: E402

_DEFAULT_MANIFEST = Path("data/hosp_ai_synthetic_dataset/MANIFEST.json")
_DEFAULT_DATA_ROOT = Path("data")
_METADATA_PATHS = (
    Path("data/metadata/global_ingestion_metadata.jsonl"),
    Path("data/metadata/ingestion_metadata.jsonl"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=_DEFAULT_MANIFEST)
    parser.add_argument("--data-root", type=Path, default=_DEFAULT_DATA_ROOT)
    return parser.parse_args()


async def ingest_file(
    session,
    manifest_file: CorpusFile,
    metadata: dict,
    data_root: Path,
    settings,
) -> IngestFileResult:
    """Ingest one manifest file, or account for its deliberate quarantine."""
    try:
        source_path = _contained_source(data_root, manifest_file.relative_path)
        actual_fingerprint = sha256_file(source_path)
        if actual_fingerprint != manifest_file.sha256:
            result = account_failure(
                manifest_file,
                "source_fingerprint_mismatch",
                fingerprint=actual_fingerprint,
            )
            print(_result_message(result))
            return result
        storage_uri = manifest_file.relative_path

        if manifest_file.runtime_approved and manifest_file.quarantine_state == "active":
            target_directory = settings.storage_root / "patients" / str(manifest_file.patient_id)
            target_directory.mkdir(parents=True, exist_ok=True)
            target_path = target_directory / f"{manifest_file.document_id}_{source_path.name}"
            if not target_path.exists() or sha256_file(target_path) != actual_fingerprint:
                shutil.copy2(source_path, target_path)
            storage_uri = str(target_path)

        async def processor(processor_session, document):
            return await process_document(
                processor_session,
                document.id,
                settings,
                expected_source_sha256=manifest_file.sha256,
            )

        result = await ingest_one(
            session,
            manifest_file,
            processor=processor,
            storage_uri=storage_uri,
            title=metadata.get("title") or manifest_file.document_id,
            uploaded_by=uuid.UUID(metadata["uploaded_by"]) if metadata.get("uploaded_by") else RECORDS_ID,
            access_tags=metadata.get("access_tags") or (),
            actual_fingerprint=actual_fingerprint,
        )
    except FileNotFoundError:
        result = account_failure(manifest_file, "source_unavailable")
    except (OSError, ValueError, KeyError, TypeError):
        result = account_failure(manifest_file, "invalid_metadata")
    except Exception:
        result = account_failure(manifest_file, "processing_failed")
    print(_result_message(result))
    return result


async def main() -> int:
    args = parse_args()
    settings = get_settings()
    manifest = CorpusManifest.parse_raw(args.manifest.read_text(encoding="utf-8"))
    data_root = args.data_root.resolve(strict=True)
    metadata = _load_metadata(_METADATA_PATHS)

    print(f"Starting governed synthetic ingestion. Storage root: {settings.storage_root}")
    async for session in get_session():
        missing_patients = await _missing_patients(session, manifest)
        results = []
        for manifest_file in manifest.files:
            if manifest_file.patient_id in missing_patients:
                result = account_failure(manifest_file, "patient_missing")
                print(_result_message(result))
            else:
                result = await ingest_file(
                    session,
                    manifest_file,
                    metadata.get(manifest_file.relative_path, {}),
                    data_root,
                    settings,
                )
            results.append(result)
        results = tuple(results)
        run = IngestionRun(manifest=manifest, results=results)
        print(json.dumps(_run_summary(run), default=str, sort_keys=True))
        return 1 if any(result.state == "failed" for result in results) else 0

    print(json.dumps({"state": "failed", "error_code": "database_session_unavailable"}, sort_keys=True))
    return 1


def _load_metadata(paths: tuple[Path, ...]) -> dict[str, dict]:
    metadata: dict[str, dict] = {}
    for path in paths:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                row = json.loads(line)
                relative_path = _metadata_relative_path(row.get("storage_uri", ""))
                if relative_path:
                    metadata[relative_path] = row
    return metadata


def _metadata_relative_path(storage_uri: str) -> str:
    normalized = storage_uri.replace("\\", "/")
    for prefix in ("app/backend/data/", "data/"):
        if normalized.startswith(prefix):
            return normalized[len(prefix) :]
    return normalized


def _contained_source(data_root: Path, relative_path: str) -> Path:
    source_path = (data_root / relative_path).resolve(strict=True)
    try:
        source_path.relative_to(data_root)
    except ValueError as exc:
        raise ValueError(f"Manifest path escapes data root: {relative_path}") from exc
    return source_path


async def _missing_patients(session, manifest: CorpusManifest) -> tuple[uuid.UUID, ...]:
    patient_ids = {item.patient_id for item in manifest.files if item.runtime_approved and item.patient_id is not None}
    if not patient_ids:
        return ()
    result = await session.execute(select(Patient.id).where(Patient.id.in_(patient_ids)))
    existing_patient_ids = set(result.scalars().all())
    return tuple(sorted(patient_ids - existing_patient_ids, key=str))


def _result_message(result: IngestFileResult) -> str:
    error = f" error_code={result.error_code}" if result.error_code else ""
    return (
        f"[{result.state.upper()}] {result.path} document={result.document_id} "
        f"generation={result.generation} attempts={result.attempts}{error}"
    )


def _run_summary(run: IngestionRun) -> dict:
    state_counts: dict[str, int] = {}
    for result in run.results:
        state_counts[result.state] = state_counts.get(result.state, 0) + 1
    return {
        "corpus_version": run.manifest.corpus_version,
        "manifest_file_count": len(run.manifest.files),
        "accounted_file_count": len(run.results),
        "state_counts": dict(sorted(state_counts.items())),
        "results": [asdict(result) for result in run.results],
    }


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
