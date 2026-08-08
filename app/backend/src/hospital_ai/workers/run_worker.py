from __future__ import annotations

import argparse
from collections.abc import Sequence
from typing import Optional

from redis import Redis
from rq import Queue, Worker

from hospital_ai.core.config import Settings, get_settings

WORKER_QUEUE_NAMES = ("document-indexing", "cdss-analysis")


def build_worker(settings: Settings) -> Worker:
    """Build the long-running worker for all active background queues.

    The dead-letter queue is intentionally excluded: it is an inspection and
    recovery queue, not a queue that should be drained automatically.
    """
    connection = Redis.from_url(settings.redis_url)
    queues = [Queue(name, connection=connection) for name in WORKER_QUEUE_NAMES]
    return Worker(queues, connection=connection)


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Run Hospital AI background workers.")
    parser.add_argument(
        "--burst",
        action="store_true",
        help="Process currently queued jobs and exit instead of polling continuously.",
    )
    args = parser.parse_args(argv)

    worker = build_worker(get_settings())
    worker.work(burst=args.burst)


if __name__ == "__main__":
    main()
