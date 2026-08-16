"""Guard the public provenance contract for the CDI V2 promotion branch."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
MANIFEST_PATH = REPOSITORY_ROOT / "docs" / "09-testing" / "evidence" / "cdi-v2-promotion-manifest.json"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
BANNED_SURFACE_PATTERNS = (
    "app/backend/artifacts/",
    "app/backend/eval_output.txt",
    "app/backend/test_results.txt",
    "app/backend/fix.py",
    "app/backend/patch_new_migration.py",
)
REQUIRED_SHA_FIELDS = ("main", "candidate", "merge_base")
REQUIRED_MANIFEST_KEYS = {
    "schema_version",
    "branch",
    "shas",
    "pull_requests",
    "preserved_dirty_paths",
    "path_disposition",
    "test_commands",
}
SECRET_LIKE_KEY_PATTERN = re.compile(
    r"(?:^|[_-])(api[_-]?key|secret|token|password|private[_-]?key|access[_-]?key)(?:[_-]|$)",
    re.IGNORECASE,
)
MIGRATION_REVISION_PATTERN = re.compile(r"^\s*revision:\s*str\s*=\s*[\"']([^\"']+)[\"']", re.MULTILINE)
MIGRATION_DOWN_REVISION_PATTERN = re.compile(
    r"^\s*down_revision:\s*(?:Union\[[^\]]+\]|str\s*\|\s*None)\s*=\s*[\"']([^\"']+)[\"']",
    re.MULTILINE,
)
MIGRATION_FILENAME_PATTERN = re.compile(r"^cdi_v2_(\d{4})_.*\.py$")


def load_manifest() -> dict[str, Any]:
    with MANIFEST_PATH.open(encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


def _secret_like_key_errors(value: Any, location: str = "manifest") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if SECRET_LIKE_KEY_PATTERN.search(str(key)):
                errors.append(f"secret-like key is not allowed: {location}.{key}")
            errors.extend(_secret_like_key_errors(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_secret_like_key_errors(child, f"{location}[{index}]"))
    return errors


def migration_validation_errors(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    revisions: dict[str, Path] = {}
    known_revisions: set[str] = set()

    for path in paths:
        text = path.read_text(encoding="utf-8")
        revision_match = MIGRATION_REVISION_PATTERN.search(text)
        if revision_match is None:
            errors.append(f"migration is missing a revision header: {path.name}")
            continue

        revision = revision_match.group(1)
        known_revisions.add(revision)
        previous = revisions.get(revision)
        if previous is not None:
            errors.append(f"duplicate migration revision header {revision}: {previous.name}, {path.name}")
        revisions[revision] = path

        filename_match = MIGRATION_FILENAME_PATTERN.match(path.name)
        revision_match_ordinal = re.fullmatch(r"cdi_v2_(\d{4})", revision)
        if filename_match and revision_match_ordinal and filename_match.group(1) != revision_match_ordinal.group(1):
            errors.append(f"migration filename/header ordinal mismatch: {path.name} declares {revision}")

        down_revision_match = MIGRATION_DOWN_REVISION_PATTERN.search(text)
        if down_revision_match and down_revision_match.group(1).startswith("cdi_v2_"):
            down_revision = down_revision_match.group(1)
            if down_revision not in known_revisions and not any(
                MIGRATION_REVISION_PATTERN.search(candidate.read_text(encoding="utf-8"))
                and MIGRATION_REVISION_PATTERN.search(candidate.read_text(encoding="utf-8")).group(1) == down_revision
                for candidate in paths
            ):
                errors.append(f"migration down_revision target is missing: {path.name} -> {down_revision}")

    return errors


def validation_errors(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing_keys = REQUIRED_MANIFEST_KEYS.difference(manifest)
    errors.extend(f"missing manifest key: {key}" for key in sorted(missing_keys))

    branch = manifest.get("branch")
    if branch in {"main", "master"} or not isinstance(branch, str) or not branch.startswith("feat/"):
        errors.append("promotion branch must be a non-main feat/* branch")

    shas = manifest.get("shas")
    if not isinstance(shas, dict):
        errors.append("shas must be an object")
    else:
        for field in REQUIRED_SHA_FIELDS:
            value = shas.get(field)
            if not isinstance(value, str) or not SHA_PATTERN.fullmatch(value):
                errors.append(f"invalid or missing SHA: {field}")

    pull_requests = manifest.get("pull_requests")
    if not isinstance(pull_requests, list) or {
        item.get("number") for item in pull_requests if isinstance(item, dict)
    } != set(range(89, 104)):
        errors.append("pull_requests must cover PRs 89 through 103")

    path_disposition = manifest.get("path_disposition")
    if not isinstance(path_disposition, list):
        errors.append("path_disposition must be a list")
    else:
        seen_paths: set[str] = set()
        for item in path_disposition:
            if not isinstance(item, dict):
                errors.append("path disposition entries must be objects")
                continue
            path = item.get("path")
            disposition = item.get("disposition")
            if not isinstance(path, str) or disposition not in {"include", "adapt", "exclude"}:
                errors.append("path disposition entries require path and include/adapt/exclude")
                continue
            if path in seen_paths:
                errors.append(f"duplicate path disposition: {path}")
            seen_paths.add(path)
            for field in ("owner", "reason", "verification"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    errors.append(f"path disposition {path} requires {field}")
            if disposition == "include" and any(
                path == banned or path.startswith(banned) for banned in BANNED_SURFACE_PATTERNS
            ):
                errors.append(f"banned generated surface included: {path}")

    if not isinstance(manifest.get("test_commands"), list) or not manifest["test_commands"]:
        errors.append("test_commands must contain at least one command identifier")
    if not isinstance(manifest.get("preserved_dirty_paths"), list):
        errors.append("preserved_dirty_paths must be a list")
    errors.extend(_secret_like_key_errors(manifest))
    errors.extend(
        migration_validation_errors(
            sorted((REPOSITORY_ROOT / "app" / "backend" / "alembic" / "versions").glob("cdi_v2_*.py"))
        )
    )
    return errors


def assert_valid_manifest(manifest: dict[str, Any]) -> None:
    errors = validation_errors(manifest)
    assert not errors, "invalid CDI V2 promotion manifest: " + "; ".join(errors)


def test_checked_in_promotion_manifest_is_valid() -> None:
    assert_valid_manifest(load_manifest())


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        (lambda value: value["shas"].pop("candidate"), "candidate"),
        (lambda value: value.update(branch="main"), "branch"),
        (
            lambda value: value["path_disposition"].append({"path": "app/backend/fix.py", "disposition": "include"}),
            "banned generated surface",
        ),
        (
            lambda value: value["path_disposition"].append(
                {
                    "path": "docs/example.json",
                    "disposition": "include",
                    "owner": "test",
                    "reason": "synthetic",
                    "verification": "test",
                    "api_key": "must-not-appear",
                }
            ),
            "secret-like key",
        ),
    ],
)
def test_manifest_rejects_missing_mainline_provenance_or_banned_paths(mutation, expected_error: str) -> None:
    manifest = load_manifest()
    mutation(manifest)

    assert any(expected_error in error for error in validation_errors(manifest))


def test_promotion_manifest_rejects_duplicate_path_dispositions() -> None:
    manifest = load_manifest()
    manifest["path_disposition"].append(dict(manifest["path_disposition"][0]))

    assert any("duplicate path disposition" in error for error in validation_errors(manifest))


def test_migration_headers_are_unique_and_filename_aligned() -> None:
    paths = sorted((REPOSITORY_ROOT / "app" / "backend" / "alembic" / "versions").glob("cdi_v2_*.py"))

    assert migration_validation_errors(paths) == []


def test_migration_header_validator_rejects_duplicate_and_misaligned_files(tmp_path: Path) -> None:
    duplicate_a = tmp_path / "cdi_v2_0007_first.py"
    duplicate_b = tmp_path / "cdi_v2_0007_second.py"
    mismatch = tmp_path / "cdi_v2_0004_mismatch.py"
    duplicate_a.write_text(
        'revision: str = "cdi_v2_0007"\ndown_revision: str | None = "cdi_v2_0006"\n', encoding="utf-8"
    )
    duplicate_b.write_text(
        'revision: str = "cdi_v2_0007"\ndown_revision: str | None = "cdi_v2_0006"\n', encoding="utf-8"
    )
    mismatch.write_text('revision: str = "cdi_v2_0005"\ndown_revision: str | None = "cdi_v2_0004"\n', encoding="utf-8")

    errors = migration_validation_errors([duplicate_a, duplicate_b, mismatch])

    assert any("duplicate migration revision header" in error for error in errors)
    assert any("filename/header ordinal mismatch" in error for error in errors)
