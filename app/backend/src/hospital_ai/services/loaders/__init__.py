"""Document loaders — provider-agnostic file ingestion pipeline.
Gói bộ nạp tài liệu (Document Loaders) — hệ thống xử lý và đọc các định dạng tệp đầu vào không phụ thuộc nhà cung cấp.

Inspired by kotaemon's loader architecture with composite fallback chain.
Lấy cảm hứng từ kiến trúc bộ nạp của kotaemon với chuỗi xử lý dự phòng tự động (composite fallback chain).
"""

from hospital_ai.services.loaders.base import BaseDocumentLoader, LoadedPage
from hospital_ai.services.loaders.composite import CompositeLoader

__all__ = ["BaseDocumentLoader", "LoadedPage", "CompositeLoader"]
