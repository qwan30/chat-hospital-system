"""Validate and materialize the immutable canonical RAG corpus manifest."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hospital_ai.evaluation.corpus import (  # noqa: E402
    CorpusValidationError,
    build_manifest,
    pair_verified_duplicates,
    require_complete_duplicate_pairing,
    sha256_file,
    validate_manifest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the canonical synthetic RAG corpus")
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--duplicate-root", type=Path)
    parser.add_argument("--write-manifest", type=Path)
    parser.add_argument("--write-duplicate-report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        pairs = pair_verified_duplicates(args.data_root, args.duplicate_root) if args.duplicate_root is not None else {}
        if args.duplicate_root is not None:
            require_complete_duplicate_pairing(pairs)
        manifest = build_manifest(args.data_root, None)
        result = validate_manifest(manifest, args.data_root)
    except CorpusValidationError as exc:
        print(json.dumps({"is_valid": False, "error": str(exc)}, sort_keys=True))
        return 1

    if args.write_manifest is not None:
        _write_text(args.write_manifest, manifest.json(indent=2, sort_keys=True) + "\n")
    if args.write_duplicate_report is not None:
        _write_duplicate_report(args.write_duplicate_report, args.data_root, args.duplicate_root, pairs)

    output = result.dict()
    output["duplicate_pair_count"] = len(pairs)
    output["duplicate_pairings_by_directory"] = _pairings_by_directory(args.data_root, pairs)
    print(json.dumps(output, default=str, sort_keys=True))
    return 0 if result.is_valid else 1


def _pairings_by_directory(data_root: Path, pairs: dict[Path, Path]) -> dict[str, int]:
    root = data_root.resolve(strict=True)
    directories = Counter(path.relative_to(root).parts[0] for path in pairs)
    return dict(sorted(directories.items()))


def _write_duplicate_report(
    output_path: Path,
    data_root: Path,
    duplicate_root: Path | None,
    pairs: dict[Path, Path],
) -> None:
    root = data_root.resolve(strict=True)
    duplicate = duplicate_root.resolve(strict=True) if duplicate_root is not None else None
    payload = {
        "pair_count": len(pairs),
        "mismatch_count": 0,
        "pairs": [
            {
                "canonical_path": canonical.relative_to(root).as_posix(),
                "duplicate_path": duplicate_path.relative_to(duplicate).as_posix() if duplicate is not None else None,
                "sha256": sha256_file(canonical),
            }
            for canonical, duplicate_path in sorted(pairs.items(), key=lambda item: item[0].as_posix())
        ],
    }
    _write_text(output_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
