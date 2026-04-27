from redis import Redis
from rq import Queue, Worker

from hospital_ai.core.config import get_settings


def main() -> None:
    settings = get_settings()
    connection = Redis.from_url(settings.redis_url)
    worker = Worker([Queue("document-indexing", connection=connection)], connection=connection)
    worker.work()


if __name__ == "__main__":
    main()
