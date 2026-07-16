"""Base document loader interface.
Giao diện trừu tượng cơ sở cho các bộ đọc/nạp tài liệu (Document Loaders).

All loaders must implement the `load` method which returns a list of
LoadedPage objects, each representing a page/section of the document.
Mọi loader phải triển khai phương thức `load` trả về danh sách đối tượng LoadedPage,
mỗi đối tượng tương ứng với một trang hoặc một phần nội dung của tài liệu.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LoadedPage:
    """A single page/section extracted from a document.
    Cấu trúc dữ liệu biểu diễn một trang/phần nội dung trích xuất từ tệp tài liệu.
    """

    page_number: int
    text: str
    confidence: float = 1.0
    metadata: dict[str, str] = field(default_factory=dict)


class BaseDocumentLoader(ABC):
    """Abstract base class for document loaders.
    Lớp trừu tượng cơ sở cho mọi bộ nạp tài liệu (PDF, Word, Excel, HTML...).
    """

    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """Return set of file extensions this loader handles (e.g. {'.pdf', '.PDF'}).
        Trả về tập hợp các đuôi mở rộng mà bộ nạp này hỗ trợ xử lý.
        """

    @abstractmethod
    def load(self, file_path: Path, mime_type: str = "") -> list[LoadedPage]:
        """Extract pages/sections from the given file.
        Trích xuất các trang/nội dung từ đường dẫn tệp đã chỉ định.

        Args:
            file_path: Path to the file on disk (Đường dẫn đến tệp trên ổ đĩa).
            mime_type: Optional MIME type hint (Gợi ý kiểu MIME nếu có).

        Returns:
            List of LoadedPage objects (Danh sách các đối tượng LoadedPage đã trích xuất).

        Raises:
            ExternalServiceError: If extraction fails (Khi quá trình đọc/trích xuất lỗi).
        """

    def can_handle(self, file_path: Path, mime_type: str = "") -> bool:
        """Check whether this loader can process the given file.
        Kiểm tra xem bộ nạp này có khả năng xử lý tệp đầu vào hay không dựa vào đuôi mở rộng.
        """
        return file_path.suffix.lower() in self.supported_extensions()
