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


def load_manifest() -> dict[str, Any]:
    with MANIFEST_PATH.open(encoding="utf-8") as manifest_file:
        return json.load(manifest_file)


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
    if not isinstance(pull_requests, list) or {item.get("number") for item in pull_requests if isinstance(item, dict)} != set(
        range(89, 104)
    ):
        errors.append("pull_requests must cover PRs 89 through 103")

    path_disposition = manifest.get("path_disposition")
    if not isinstance(path_disposition, list):
        errors.append("path_disposition must be a list")
    else:
        for item in path_disposition:
            if not isinstance(item, dict):
                errors.append("path disposition entries must be objects")
                continue
            path = item.get("path")
            disposition = item.get("disposition")
            if not isinstance(path, str) or disposition not in {"include", "adapt", "exclude"}:
                errors.append("path disposition entries require path and include/adapt/exclude")
                continue
            if disposition == "include" and any(
                path == banned or path.startswith(banned) for banned in BANNED_SURFACE_PATTERNS
            ):
                errors.append(f"banned generated surface included: {path}")

    if not isinstance(manifest.get("test_commands"), list) or not manifest["test_commands"]:
        errors.append("test_commands must contain at least one command identifier")
    if not isinstance(manifest.get("preserved_dirty_paths"), list):
        errors.append("preserved_dirty_paths must be a list")
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
            lambda value: value["path_disposition"].append(
                {"path": "app/backend/fix.py", "disposition": "include"}
            ),
            "banned generated surface",
        ),
    ],
)
def test_manifest_rejects_missing_mainline_provenance_or_banned_paths(mutation, expected_error: str) -> None:
    manifest = load_manifest()
    mutation(manifest)

    assert any(expected_error in error for error in validation_errors(manifest))
