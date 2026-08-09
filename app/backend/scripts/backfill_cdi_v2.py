#!/usr/bin/env python
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import uuid
from pathlib import Path

# Ensure src is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlalchemy import select
from hospital_ai.db.session import get_session_factory
from hospital_ai.db.models import Document
from hospital_ai.migrations.cdi_v2_backfill import CdiV2Backfill, BackfillPolicy, BackfillBlocked

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("backfill_cdi_v2")


async def run_backfill(args: argparse.Namespace) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        policy = BackfillPolicy(autoapprove_synthetic=True)
        runner = CdiV2Backfill(session, policy=policy)

        doc_ids: list[uuid.UUID] = []
        if args.document_id:
            doc_ids = [uuid.UUID(d) for d in args.document_id]
        else:
            res = await session.execute(select(Document.id))
            doc_ids = list(res.scalars().all())

        if args.mode == "parity":
            report = await runner.compute_parity_report(doc_ids if args.document_id else None)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            logger.info(
                "Parity check completed: status=%s (wrong_patient=%d, superseded=%d)",
                report["status"],
                report["wrong_patient_count"],
                report["superseded_generation_count"],
            )
            return 0 if report["status"] == "passed" else 1

        results = []
        for doc_id in doc_ids:
            try:
                res = await runner.run_document(doc_id)
                results.append(
                    {
                        "document_id": str(doc_id),
                        "status": "success",
                        "generation_id": str(res.generation_id) if res.generation_id else None,
                    }
                )
            except BackfillBlocked as exc:
                logger.warning("Document %s blocked: %s", doc_id, exc.failure_codes)
                results.append({"document_id": str(doc_id), "status": "blocked", "failure_codes": exc.failure_codes})
            except Exception as exc:
                logger.exception("Document %s error: %s", doc_id, exc)
                results.append({"document_id": str(doc_id), "status": "error", "detail": str(exc)})

        if args.mode == "dry-run":
            await session.rollback()
            logger.info("Dry run complete (rolled back)")
        else:
            await session.commit()
            logger.info("Apply complete (committed)")

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as f:
            json.dump({"mode": args.mode, "count": len(results), "results": results}, f, indent=2)

        return 0 if all(r["status"] in ("success", "blocked") for r in results) else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="CDI v2 Legacy Document Backfill and Parity CLI")
    parser.add_argument("--mode", choices=("dry-run", "apply", "parity"), required=True)
    parser.add_argument("--document-id", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    exit_code = asyncio.run(run_backfill(args))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
