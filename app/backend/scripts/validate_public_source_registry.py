"""Validate an explicitly selected public-source registry and its local artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _load_validator():
    sys.path.insert(0, str(BACKEND_ROOT / "src"))
    from hospital_ai.data_sources.registry import (  # noqa: PLC0415
        VendoredDataValidationError,
        validate_vendored_sources,
    )

    return VendoredDataValidationError, validate_vendored_sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        type=Path,
        required=True,
        help="root directory that contains the explicitly registered local artifacts",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        required=True,
        help="path to a source registry; no repository-wide default is assumed",
    )
    args = parser.parse_args(argv)
    validation_error, validate = _load_validator()

    try:
        results = validate(args.data_root, args.registry)
    except (validation_error, OSError, TypeError, ValueError) as error:
        print(f"invalid public-source registry: {error}", file=sys.stderr)
        return 2

    print(f"public-source registry is valid: {len(results)} local artifact(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
