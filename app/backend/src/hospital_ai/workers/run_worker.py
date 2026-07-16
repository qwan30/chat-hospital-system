"""Redis RQ Worker runner script.
Script khởi chạy worker RQ (Redis Queue) lắng nghe và xử lý hàng đợi 'document-indexing' trong môi trường production.
"""

from redis import Redis
from rq import Queue, Worker

from hospital_ai.core.config import get_settings


def main() -> None:
    """Initialize Redis connection and start listening on the document-indexing queue.
    Khởi tạo kết nối Redis và bắt đầu thực thi các tác vụ trong hàng đợi index tài liệu.
    """
    settings = get_settings()
    connection = Redis.from_url(settings.redis_url)
    worker = Worker([Queue("document-indexing", connection=connection)], connection=connection)
    worker.work()


if __name__ == "__main__":
    main()
