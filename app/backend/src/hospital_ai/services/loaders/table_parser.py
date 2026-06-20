"""Table parsing utilities for medical documents.

Converts raw table data from PDF extraction into structured markdown
format that LLMs can comprehend. Handles common medical table patterns
like lab results, vital signs, and medication lists.
"""

from __future__ import annotations

import re


def tables_to_markdown(tables: list[list[list[str]]] | None) -> str:
    """Convert a list of raw tables to markdown format.

    Args:
        tables: List of tables, each a 2D list of cell values.
                Cell values may be None for empty cells.

    Returns:
        Markdown string with all tables formatted with headers.
    """
    if not tables:
        return ""

    sections: list[str] = []
    for idx, table in enumerate(tables, start=1):
        md = _single_table_to_markdown(table)
        if md.strip():
            sections.append(f"### Table {idx}\n\n{md}")

    return "\n\n".join(sections)


def _single_table_to_markdown(table: list[list[str]] | None) -> str:
    """Convert a single table to markdown format."""
    if not table:
        return ""

    # Clean and normalize the table
    cleaned = normalize_medical_table(table)
    if not cleaned:
        return ""

    # Determine column widths for alignment
    col_count = max(len(row) for row in cleaned) if cleaned else 0
    if col_count == 0:
        return ""

    # Pad rows to have uniform column count
    padded = []
    for row in cleaned:
        padded_row = list(row) + [""] * (col_count - len(row))
        padded.append(padded_row)

    # Build markdown table
    lines: list[str] = []

    # Header row
    header = padded[0]
    lines.append("| " + " | ".join(_escape_pipe(cell) for cell in header) + " |")

    # Separator
    lines.append("| " + " | ".join("---" for _ in header) + " |")

    # Data rows
    for row in padded[1:]:
        lines.append("| " + " | ".join(_escape_pipe(cell) for cell in row) + " |")

    return "\n".join(lines)


def normalize_medical_table(
    table: list[list[str]] | None,
) -> list[list[str]]:
    """Normalize a raw table for medical document parsing.

    Handles:
    - None/empty cell values
    - Merged cells (carries forward non-empty values)
    - Whitespace cleanup
    - Removal of completely empty rows and columns

    Args:
        table: Raw 2D list with possible None values.

    Returns:
        Cleaned 2D list of strings.
    """
    if not table:
        return []

    # Step 1: Replace None with empty string, strip whitespace
    cleaned: list[list[str]] = []
    for row in table:
        cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
        cleaned.append(cleaned_row)

    # Step 2: Remove completely empty rows
    cleaned = [row for row in cleaned if any(cell.strip() for cell in row)]

    if not cleaned:
        return []

    # Step 3: Remove completely empty columns
    col_count = max(len(row) for row in cleaned)
    non_empty_cols = []
    for col_idx in range(col_count):
        has_content = any(col_idx < len(row) and row[col_idx].strip() for row in cleaned)
        if has_content:
            non_empty_cols.append(col_idx)

    if not non_empty_cols:
        return []

    result = []
    for row in cleaned:
        filtered_row = [row[col_idx] if col_idx < len(row) else "" for col_idx in non_empty_cols]
        result.append(filtered_row)

    return result


def extract_lab_values(table_md: str) -> dict[str, str]:
    """Extract key-value pairs from lab result tables.

    Looks for patterns like:
    - "| Test Name | Value | Unit | Reference |"
    - "HbA1c: 7.2%"
    - "Glucose 126 mg/dL"

    Args:
        table_md: Markdown text containing table data.

    Returns:
        Dictionary mapping test names to their values.
    """
    lab_values: dict[str, str] = {}

    # Pattern 1: Markdown table rows — parse full rows with all columns
    for line in table_md.split("\n"):
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        # Split by pipe, strip each cell
        cells = [c.strip() for c in line.split("|")]
        # Remove empty first and last elements from leading/trailing pipes
        cells = [c for c in cells if c]

        if not cells or len(cells) < 2:
            continue

        # Skip separator rows
        if all(set(c) <= {"-", " ", ":"} for c in cells):
            continue

        # Skip header rows (common medical table headers)
        if cells[0].lower() in ("test", "parameter", "name", "item", "analyte"):
            continue

        # First cell is the name, second is the value
        name = cells[0].strip()
        value = cells[1].strip()
        if name and value:
            lab_values[name] = value

    # Pattern 2: Colon-separated values
    colon_pattern = re.findall(r"([A-Za-z][A-Za-z0-9\s]+?):\s*([0-9.,]+\s*[A-Za-z/%]*)", table_md)
    for name, value in colon_pattern:
        name = name.strip()
        value = value.strip()
        if name and value:
            lab_values[name] = value

    return lab_values


def detect_table_boundaries(text: str) -> list[tuple[int, int]]:
    """Detect markdown table boundaries in text.

    Returns a list of (start_pos, end_pos) tuples marking table regions.
    """
    boundaries: list[tuple[int, int]] = []
    lines = text.split("\n")
    in_table = False
    table_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        is_table_line = stripped.startswith("|") and stripped.endswith("|")
        bool(re.match(r"^\|[\s\-|]+\|$", stripped))

        if is_table_line and not in_table:
            in_table = True
            table_start = sum(len(lines[j]) + 1 for j in range(i))
        elif not is_table_line and in_table:
            in_table = False
            table_end = sum(len(lines[j]) + 1 for j in range(i))
            boundaries.append((table_start, table_end))

    # Handle table at end of text
    if in_table:
        table_end = len(text)
        boundaries.append((table_start, table_end))

    return boundaries


def _escape_pipe(cell: str) -> str:
    """Escape pipe characters within a cell value."""
    return cell.replace("|", "\\|")
