"""Validate the repository-side Vercel/Dokploy deployment contract.

This gate intentionally checks repository invariants only. It does not contact
Dokploy, GHCR, Cloudflare, the VPS, or an LLM provider.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ContractViolation:
    code: str
    message: str
    path: str


REQUIRED_FILES = (
    ".github/workflows/ci.yml",
    ".github/workflows/cd.yml",
    ".github/workflows/rollback.yml",
    "infra/docker-compose.yml",
    "docs/10-deployment/deployment-guide.md",
    "docs/10-deployment/env-variables.md",
    "docs/10-deployment/ci-cd.md",
    "docs/10-deployment/release-checklist.md",
    "docs/10-deployment/vps-operations.md",
    "docs/10-deployment/vps-preflight-evidence.md",
)

EVIDENCE_PENDING_STATUS = "PENDING — operator evidence required"
EVIDENCE_TABLE_HEADER = "| Status | Check | Command | Expected result | Operator-captured value | Timestamp | Owner |"
REQUIRED_PREFLIGHT_CHECKS = (
    "Candidate SHA pinned",
    "CI Run ID recorded",
    "Synthetic/de-identified data only",
    "OS and version",
    "RAM headroom",
    "Disk headroom",
    "Swap configured or absent",
    "SSH key access",
    "Firewall policy",
    "Listener review for 22/80/443/3000",
    "Docker server version",
    "Docker Compose version",
    "Dokploy installed",
    "Dokploy domain and HTTPS route",
    "GitHub source connection",
    "GHCR candidate image access",
    "Secret key presence only",
    "Vercel `VITE_API_URL` route",
    "Backend CORS allowlist for Vercel origin",
    "API health route from the approved domain",
)
FORBIDDEN_CORS_CONTRACTS = (
    "HOSPITAL_AI_CORS_ORIGINS=*",
    "Access-Control-Allow-Origin: *",
    "allow any origin",
    "reflect the request Origin header",
    "echo the request Origin header",
    "mirror the request Origin header",
)
FRONTEND_SECRET_SCAN_ALLOWLIST = {
    Path("app/frontend/scripts/verify-public-bundle.mjs"),
}


def find_repo_root(start: Path | None = None) -> Path:
    """Find a repository root from a script path or an explicit directory."""

    candidate = (start or Path(__file__)).resolve()
    if candidate.is_file():
        candidate = candidate.parent

    for root in (candidate, *candidate.parents):
        if (root / "infra/docker-compose.yml").is_file() and (root / ".github/workflows/cd.yml").is_file():
            return root
    raise FileNotFoundError("could not find repository root with infra/docker-compose.yml and CD workflow")


def _read(root: Path, relative_path: str, violations: list[ContractViolation]) -> str:
    path = root / relative_path
    if not path.is_file():
        violations.append(
            ContractViolation("missing_file", f"required file is missing: {relative_path}", relative_path)
        )
        return ""
    return path.read_text(encoding="utf-8")


def _require(
    text: str, needle: str, path: str, violations: list[ContractViolation], code: str = "missing_contract"
) -> None:
    if needle not in text:
        violations.append(ContractViolation(code, f"missing required text: {needle}", path))


def _forbid(
    text: str, needle: str, path: str, violations: list[ContractViolation], code: str = "forbidden_contract"
) -> None:
    if needle in text:
        violations.append(ContractViolation(code, f"forbidden text present: {needle}", path))


def _forbid_wildcard_cors(text: str, path: str, violations: list[ContractViolation]) -> None:
    for needle in FORBIDDEN_CORS_CONTRACTS:
        _forbid(text, needle, path, violations, code="wildcard_cors")


def _parse_markdown_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None

    cells: list[str] = []
    current: list[str] = []
    in_code_span = False
    for character in stripped[1:-1]:
        if character == "`":
            in_code_span = not in_code_span
            current.append(character)
            continue
        if character == "|" and not in_code_span:
            cells.append("".join(current).strip())
            current = []
            continue
        current.append(character)

    cells.append("".join(current).strip())
    return cells


def _validate_preflight_evidence_table(text: str, path: str, violations: list[ContractViolation]) -> None:
    lines = text.splitlines()
    try:
        header_index = next(index for index, line in enumerate(lines) if line.strip() == EVIDENCE_TABLE_HEADER)
    except StopIteration:
        return

    separator_index = header_index + 1
    if separator_index >= len(lines):
        violations.append(
            ContractViolation(
                "invalid_preflight_table",
                "preflight evidence table is missing the markdown separator row",
                path,
            )
        )
        return

    separator_cells = _parse_markdown_row(lines[separator_index])
    if (
        separator_cells is None
        or len(separator_cells) != 7
        or any(not re.fullmatch(r":?-{3,}:?", cell) for cell in separator_cells)
    ):
        violations.append(
            ContractViolation(
                "invalid_preflight_table",
                "preflight evidence table separator must contain exactly seven markdown divider cells",
                path,
            )
        )
        return

    seen_checks: dict[str, int] = {}
    pending_checks: set[str] = set()

    for line_number, raw_line in enumerate(lines[separator_index + 1 :], start=separator_index + 2):
        stripped = raw_line.strip()
        if not stripped:
            break

        cells = _parse_markdown_row(raw_line)
        if cells is None or len(cells) != 7:
            violations.append(
                ContractViolation(
                    "invalid_preflight_row",
                    f"line {line_number} must be a seven-column markdown table row",
                    path,
                )
            )
            continue

        status, check_name, *_ = cells
        if status != EVIDENCE_PENDING_STATUS:
            violations.append(
                ContractViolation(
                    "invalid_preflight_status",
                    (
                        f"line {line_number} for '{check_name}' must start with exactly "
                        f"'{EVIDENCE_PENDING_STATUS}', found '{status or '<blank>'}'"
                    ),
                    path,
                )
            )

        if check_name not in REQUIRED_PREFLIGHT_CHECKS:
            violations.append(
                ContractViolation(
                    "unexpected_preflight_check",
                    f"line {line_number} has unexpected preflight check '{check_name}'",
                    path,
                )
            )
            continue

        seen_checks[check_name] = seen_checks.get(check_name, 0) + 1
        if seen_checks[check_name] > 1:
            violations.append(
                ContractViolation(
                    "duplicate_preflight_check",
                    f"line {line_number} duplicates required preflight check '{check_name}'",
                    path,
                )
            )

        if status == EVIDENCE_PENDING_STATUS and seen_checks[check_name] == 1:
            pending_checks.add(check_name)

    for check_name in REQUIRED_PREFLIGHT_CHECKS:
        if check_name not in seen_checks:
            violations.append(
                ContractViolation(
                    "missing_preflight_row",
                    f"missing required preflight evidence row for '{check_name}'",
                    path,
                )
            )
        elif check_name not in pending_checks:
            violations.append(
                ContractViolation(
                    "pending_preflight_row_required",
                    f"required preflight evidence row for '{check_name}' must remain pending",
                    path,
                )
            )


def _has_public_mapping(compose: str, container_port: str) -> bool:
    """Return true only for a Compose host:container mapping, not a URL/healthcheck."""

    mapping = re.compile(rf"^\s*-\s*['\"]?[^'\"\s]+:{re.escape(container_port)}['\"]?\s*$", re.MULTILINE)
    return bool(mapping.search(compose))


def _frontend_secret_leaks(root: Path) -> list[str]:
    forbidden = (
        "HOSPITAL_AI_GEMINI_API_KEY",
        "HOSPITAL_AI_OPENAI_API_KEY",
        "HOSPITAL_AI_R2_ACCESS_KEY_ID",
        "HOSPITAL_AI_R2_SECRET_ACCESS_KEY",
        "HOSPITAL_AI_JWT_HMAC_SECRET",
    )
    ignored_parts = {".git", "node_modules", ".next", "dist", "coverage", "__pycache__"}
    frontend_root = root / "app/frontend"
    if not frontend_root.is_dir():
        return []

    leaks: list[str] = []
    for path in frontend_root.rglob("*"):
        if not path.is_file():
            continue
        if ignored_parts.intersection(path.parts):
            continue
        if path.relative_to(root) in FRONTEND_SECRET_SCAN_ALLOWLIST:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for secret_name in forbidden:
            if secret_name in content:
                leaks.append(f"{path.relative_to(root)} contains {secret_name}")
    return leaks


def validate_deployment_contract(root: Path | None = None) -> list[ContractViolation]:
    """Return deterministic repository contract violations."""

    repo_root = find_repo_root(root)
    violations: list[ContractViolation] = []
    files = {relative: _read(repo_root, relative, violations) for relative in REQUIRED_FILES}

    compose = files["infra/docker-compose.yml"]
    cd_workflow = files[".github/workflows/cd.yml"]
    rollback_workflow = files[".github/workflows/rollback.yml"]
    deployment_guide = files["docs/10-deployment/deployment-guide.md"]
    env_docs = files["docs/10-deployment/env-variables.md"]
    ci_cd_docs = files["docs/10-deployment/ci-cd.md"]
    release_checklist = files["docs/10-deployment/release-checklist.md"]
    vps_ops = files["docs/10-deployment/vps-operations.md"]
    vps_evidence = files["docs/10-deployment/vps-preflight-evidence.md"]

    for forbidden in ("\n  nginx:", "\n  ollama:", "HOSPITAL_AI_OLLAMA_BASE_URL", "localhost:11434"):
        _forbid(compose, forbidden, "infra/docker-compose.yml", violations)
    _require(compose, 'expose:\n      - "8000"', "infra/docker-compose.yml", violations)
    _require(compose, "BACKEND_IMAGE", "infra/docker-compose.yml", violations)
    for variable in (
        "HOSPITAL_AI_STORAGE_BACKEND",
        "HOSPITAL_AI_R2_ENDPOINT",
        "HOSPITAL_AI_R2_BUCKET",
        "HOSPITAL_AI_GEMINI_API_KEY",
        "HOSPITAL_AI_JWT_ISSUER",
        "HOSPITAL_AI_JWKS_URL",
    ):
        _require(compose, variable, "infra/docker-compose.yml", violations)
    for port in ("5432", "6379", "8000"):
        if _has_public_mapping(compose, port):
            violations.append(
                ContractViolation(
                    "public_port", f"public host mapping for port {port} is forbidden", "infra/docker-compose.yml"
                )
            )

    for workflow_path, workflow in (
        (".github/workflows/cd.yml", cd_workflow),
        (".github/workflows/rollback.yml", rollback_workflow),
    ):
        for forbidden in ("appleboy/ssh-action", "appleboy/scp-action", "infra/nginx"):
            _forbid(workflow, forbidden, workflow_path, violations)
        _require(workflow, "docker manifest inspect", workflow_path, violations)
        _require(workflow, "sha-", workflow_path, violations)

    _require(cd_workflow, "workflow_run", ".github/workflows/cd.yml", violations)
    _require(cd_workflow, "DOKPLOY_DEPLOY_HOOK_URL", ".github/workflows/cd.yml", violations)
    _require(cd_workflow, '"action":"deploy"', ".github/workflows/cd.yml", violations)
    _require(rollback_workflow, "DOKPLOY_ROLLBACK_HOOK_URL", ".github/workflows/rollback.yml", violations)
    _require(rollback_workflow, '"action":"rollback"', ".github/workflows/rollback.yml", violations)
    _require(rollback_workflow, "ROLLBACK", ".github/workflows/rollback.yml", violations)

    _require(deployment_guide, "Vercel", "docs/10-deployment/deployment-guide.md", violations)
    _require(deployment_guide, "Dokploy/Traefik", "docs/10-deployment/deployment-guide.md", violations)
    _require(deployment_guide, "not installed on the Dokploy VPS", "docs/10-deployment/deployment-guide.md", violations)
    _require(deployment_guide, "4 GB", "docs/10-deployment/deployment-guide.md", violations)
    _require(env_docs, "Supabase is not part", "docs/10-deployment/env-variables.md", violations)
    _require(env_docs, "The VPS does not run Ollama", "docs/10-deployment/env-variables.md", violations)
    _require(env_docs, "VITE_API_URL=/api", "docs/10-deployment/env-variables.md", violations)
    _require(
        env_docs,
        "Vite rewrites that local path to `/api/v1` in development.",
        "docs/10-deployment/env-variables.md",
        violations,
    )
    _require(
        env_docs,
        "VITE_API_URL=https://api-preview.example.com/api/v1",
        "docs/10-deployment/env-variables.md",
        violations,
    )
    _require(
        env_docs,
        "HOSPITAL_AI_CORS_ORIGINS=https://preview-app.example.com",
        "docs/10-deployment/env-variables.md",
        violations,
    )
    _require(
        env_docs,
        "VITE_API_URL=https://api.example.com/api/v1",
        "docs/10-deployment/env-variables.md",
        violations,
    )
    _require(
        env_docs,
        "HOSPITAL_AI_CORS_ORIGINS=https://app.example.com",
        "docs/10-deployment/env-variables.md",
        violations,
    )
    _require(
        env_docs,
        "Preview domains must be explicitly approved and added to the backend CORS",
        "docs/10-deployment/env-variables.md",
        violations,
    )
    _forbid_wildcard_cors(env_docs, "docs/10-deployment/env-variables.md", violations)
    _require(ci_cd_docs, "DOKPLOY_DEPLOY_HOOK_URL", "docs/10-deployment/ci-cd.md", violations)
    _require(ci_cd_docs, "DOKPLOY_ROLLBACK_HOOK_URL", "docs/10-deployment/ci-cd.md", violations)
    _require(release_checklist, "verify_deployment_contract.py", "docs/10-deployment/release-checklist.md", violations)
    _require(release_checklist, "synthetic/de-identified", "docs/10-deployment/release-checklist.md", violations)
    _require(
        vps_ops,
        "Repository validation is static only;",
        "docs/10-deployment/vps-operations.md",
        violations,
    )
    _require(
        vps_ops,
        "The route remains UNVERIFIED until an operator captures candidate-specific evidence.",
        "docs/10-deployment/vps-operations.md",
        violations,
    )
    _require(
        vps_ops,
        "VITE_API_URL=https://<API_DOMAIN>/api/v1",
        "docs/10-deployment/vps-operations.md",
        violations,
    )
    _require(
        vps_ops,
        "HOSPITAL_AI_CORS_ORIGINS=https://<VERCEL_FRONTEND_ORIGIN>",
        "docs/10-deployment/vps-operations.md",
        violations,
    )
    _forbid_wildcard_cors(vps_ops, "docs/10-deployment/vps-operations.md", violations)
    for needle in (
        "cat /etc/os-release",
        "free -h",
        'df -h "<VPS_DATA_MOUNT>"',
        "swapon --show",
        "ufw status numbered",
        "ss -ltnp",
        "docker --version",
        "docker compose version",
        'docker manifest inspect "ghcr.io/<GHCR_NAMESPACE>/<IMAGE_NAME>:sha-<CANDIDATE_SHA>"',
        'curl --fail --silent --show-error "https://<API_DOMAIN>/api/v1/health"',
    ):
        _require(vps_ops, needle, "docs/10-deployment/vps-operations.md", violations)
    _require(
        vps_evidence,
        "Every row in this template starts as `PENDING — operator evidence required`.",
        "docs/10-deployment/vps-preflight-evidence.md",
        violations,
    )
    _require(
        vps_evidence,
        "| Status | Check | Command | Expected result | Operator-captured value | Timestamp | Owner |",
        "docs/10-deployment/vps-preflight-evidence.md",
        violations,
    )
    _require(
        vps_evidence,
        "<CANDIDATE_SHA>",
        "docs/10-deployment/vps-preflight-evidence.md",
        violations,
    )
    _require(
        vps_evidence,
        "<CI_RUN_ID>",
        "docs/10-deployment/vps-preflight-evidence.md",
        violations,
    )
    _require(
        vps_evidence,
        "repository validation is static only and does not prove",
        "docs/10-deployment/vps-preflight-evidence.md",
        violations,
    )
    _forbid_wildcard_cors(vps_evidence, "docs/10-deployment/vps-preflight-evidence.md", violations)
    _validate_preflight_evidence_table(
        vps_evidence,
        "docs/10-deployment/vps-preflight-evidence.md",
        violations,
    )

    for leak in _frontend_secret_leaks(repo_root):
        violations.append(ContractViolation("frontend_secret_leak", leak, "app/frontend"))

    return violations


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, help="repository root; defaults to auto-detection")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        repo_root = find_repo_root(args.repo_root)
        violations = validate_deployment_contract(repo_root)
    except (FileNotFoundError, OSError) as exc:
        violations = [ContractViolation("invalid_repository", str(exc), str(args.repo_root or ""))]

    result = {"valid": not violations, "violations": [asdict(item) for item in violations]}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif violations:
        print("deployment contract: INVALID")
        for violation in violations:
            print(f"- [{violation.code}] {violation.path}: {violation.message}")
    else:
        print("deployment contract: VALID")

    return 0 if not violations else 2


if __name__ == "__main__":
    sys.exit(main())
