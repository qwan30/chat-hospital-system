"""Build or verify the deterministic source inventory used by evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _load_manifest_builder():
    sys.path.insert(0, str(BACKEND_ROOT / "src"))
    from hospital_ai.evaluation.corpus_manifest import CorpusManifestValidationError, build_corpus_manifest

    return CorpusManifestValidationError, build_corpus_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write the manifest JSON to this path")
    parser.add_argument("--check", action="store_true", help="validate data and optionally compare a written manifest")
    args = parser.parse_args(argv)

    validation_error, build_manifest = _load_manifest_builder()
    try:
        manifest = build_manifest(BACKEND_ROOT / "data")
        rendered = json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
        if args.check:
            if args.output is not None and args.output.exists() and args.output.read_text(encoding="utf-8") != rendered:
                raise validation_error("manifest output is stale")
            print("evaluation corpus manifest is valid")
            return 0
        if args.output is None:
            parser.error("--output is required unless --check is used")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output}")
        return 0
    except (validation_error, OSError, KeyError, TypeError, ValueError) as error:
        print(f"invalid evaluation corpus: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
