"""Validate public datasets committed directly to the repository."""

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
        default=BACKEND_ROOT / "data",
        help="backend data root containing the public registry and artifacts",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        help="registry path; defaults to <data-root>/public/sources.json",
    )
    args = parser.parse_args(argv)
    registry_path = args.registry or args.data_root / "public" / "sources.json"
    validation_error, validate = _load_validator()

    try:
        results = validate(args.data_root, registry_path)
    except (validation_error, OSError, TypeError, ValueError) as error:
        print(f"invalid vendored public data: {error}", file=sys.stderr)
        return 2

    print(f"vendored public data is valid: {len(results)} artifact(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
