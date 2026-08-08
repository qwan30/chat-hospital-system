"""Tests for table parsing and table-aware chunking."""

from __future__ import annotations

from hospital_ai.services.chunking import ChunkingService
from hospital_ai.services.loaders.table_parser import (
    detect_table_boundaries,
    extract_lab_values,
    normalize_medical_table,
    tables_to_markdown,
)
from hospital_ai.services.ocr import OcrPage

# ── Table Parser tests ───────────────────────────────────────────────────


class TestTablesToMarkdown:
    def test_basic_table(self):
        table = [
            ["Test", "Value", "Unit"],
            ["HbA1c", "7.2", "%"],
            ["Glucose", "126", "mg/dL"],
        ]
        md = tables_to_markdown([table])
        assert "### Table 1" in md
        assert "| Test | Value | Unit |" in md
        assert "| HbA1c | 7.2 | % |" in md
        assert "| --- | --- | --- |" in md

    def test_empty_tables(self):
        assert tables_to_markdown([]) == ""

    def test_multiple_tables(self):
        table1 = [["A", "B"], ["1", "2"]]
        table2 = [["X", "Y"], ["3", "4"]]
        md = tables_to_markdown([table1, table2])
        assert "### Table 1" in md
        assert "### Table 2" in md

    def test_none_values(self):
        table = [["Name", None], ["Value", "123"]]
        md = tables_to_markdown([table])
        assert "| Name |  |" in md or "| Name | |" in md

    def test_pipe_escaping(self):
        table = [["Test | Result", "Pass"], ["A", "B"]]
        md = tables_to_markdown([table])
        assert "\\|" in md


class TestNormalizeMedicalTable:
    def test_removes_empty_rows(self):
        table = [
            ["Test", "Value"],
            [None, None],
            ["HbA1c", "7.2"],
            ["", ""],
        ]
        result = normalize_medical_table(table)
        assert len(result) == 2
        assert result[0] == ["Test", "Value"]
        assert result[1] == ["HbA1c", "7.2"]

    def test_removes_empty_columns(self):
        table = [
            ["Test", "", "Value"],
            ["HbA1c", "", "7.2"],
        ]
        result = normalize_medical_table(table)
        assert len(result) == 2
        assert result[0] == ["Test", "Value"]

    def test_empty_table(self):
        assert normalize_medical_table([]) == []

    def test_all_empty(self):
        assert normalize_medical_table([[None, None], ["", ""]]) == []

    def test_mixed_none_and_values(self):
        table = [
            ["Name", None, "Age"],
            ["Alice", None, "30"],
        ]
        result = normalize_medical_table(table)
        assert len(result[0]) == 2  # Empty column removed


class TestExtractLabValues:
    def test_markdown_table(self):
        md = """
| Test | Value | Unit |
| --- | --- | --- |
| HbA1c | 7.2 | % |
| Glucose | 126 | mg/dL |
"""
        values = extract_lab_values(md)
        assert "HbA1c" in values
        assert values["HbA1c"] == "7.2"

    def test_colon_format(self):
        text = "HbA1c: 7.2%\nGlucose: 126 mg/dL"
        values = extract_lab_values(text)
        assert "HbA1c" in values
        assert "7.2%" in values["HbA1c"]

    def test_empty_text(self):
        assert extract_lab_values("") == {}


class TestDetectTableBoundaries:
    def test_single_table(self):
        text = "Some text\n| A | B |\n| --- | --- |\n| 1 | 2 |\nMore text"
        boundaries = detect_table_boundaries(text)
        assert len(boundaries) == 1

    def test_no_tables(self):
        text = "Just plain text with no tables"
        boundaries = detect_table_boundaries(text)
        assert boundaries == []

    def test_multiple_tables(self):
        text = """Text before
| A | B |
| --- | --- |
| 1 | 2 |

Middle text

| X | Y |
| --- | --- |
| 3 | 4 |

Text after"""
        boundaries = detect_table_boundaries(text)
        assert len(boundaries) == 2

    def test_table_at_end(self):
        text = "Text\n| A | B |\n| --- | --- |\n| 1 | 2 |"
        boundaries = detect_table_boundaries(text)
        assert len(boundaries) == 1


# ── Table-Aware Chunking tests ──────────────────────────────────────────


class TestTableAwareChunking:
    def test_table_not_split(self):
        """A markdown table should never be split across chunks."""
        table_text = "| Test | Value |\n| --- | --- |\n"
        for i in range(20):
            table_text += f"| Test_{i} | {i * 10} |\n"

        page = OcrPage(page_number=1, text=f"Header text\n\n{table_text}\nFooter text", confidence=1.0)

        service = ChunkingService(max_chars=200, overlap_chars=50)
        chunks = service.chunk_pages([page])

        # Find the table chunk
        table_chunks = [c for c in chunks if c.chunk_type == "table"]
        [c for c in chunks if c.chunk_type == "text"]

        # Table should be in exactly one chunk (even if > max_chars)
        assert len(table_chunks) == 1
        assert "| Test_0 |" in table_chunks[0].content
        assert "| Test_19 |" in table_chunks[0].content

    def test_text_still_chunked_normally(self):
        """Regular text without tables should use sliding window as before."""
        long_text = "word " * 500  # ~2500 chars
        page = OcrPage(page_number=1, text=long_text, confidence=1.0)

        service = ChunkingService(max_chars=500, overlap_chars=50)
        chunks = service.chunk_pages([page])

        assert len(chunks) > 1
        assert all(c.chunk_type == "text" for c in chunks)

    def test_mixed_text_and_tables(self):
        """Page with both text and tables should produce both chunk types."""
        text = (
            "Patient presentation summary with extensive notes. " * 10
            + "\n\n"
            + "| Test | Value | Unit |\n| --- | --- | --- |\n| HbA1c | 7.2 | % |\n| Glucose | 126 | mg/dL |\n"
            + "\n\n"
            + "Follow-up recommendations and clinical notes. " * 10
        )

        page = OcrPage(page_number=1, text=text, confidence=1.0)
        service = ChunkingService(max_chars=300, overlap_chars=50)
        chunks = service.chunk_pages([page])

        types = {c.chunk_type for c in chunks}
        assert "table" in types
        assert "text" in types

    def test_empty_page(self):
        page = OcrPage(page_number=1, text="", confidence=0.0)
        service = ChunkingService()
        chunks = service.chunk_pages([page])
        assert chunks == []

    def test_chunk_type_field(self):
        """All chunks should have a chunk_type field."""
        page = OcrPage(page_number=1, text="Simple text content", confidence=1.0)
        service = ChunkingService()
        chunks = service.chunk_pages([page])
        assert all(hasattr(c, "chunk_type") for c in chunks)

    def test_backward_compatible_with_no_tables(self):
        """Chunking behavior should be identical to old behavior for text-only content."""
        text = "Simple paragraph " * 20
        page = OcrPage(page_number=1, text=text, confidence=1.0)

        service = ChunkingService(max_chars=200, overlap_chars=50)
        chunks = service.chunk_pages([page])

        # Should produce multiple chunks, all text type
        assert len(chunks) > 1
        assert all(c.chunk_type == "text" for c in chunks)
        # Chunks should overlap
        if len(chunks) >= 2:
            assert chunks[1].start_offset < chunks[0].end_offset
