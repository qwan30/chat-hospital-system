import os
import re
import sys

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from hospital_ai.core.config import get_settings
from hospital_ai.main import create_app

API_ROOT_PREFIXES = (
    "/access-requests",
    "/audit",
    "/auth",
    "/chat",
    "/chat-threads",
    "/dashboard",
    "/documents",
    "/graph",
    "/health",
    "/medication-safety",
    "/metrics",
    "/patients",
    "/search",
    "/timeline",
    "/api",
)


def get_backend_paths():
    app = create_app()
    openapi = app.openapi()
    paths = list(openapi.get("paths", {}).keys())
    return paths


def normalize_path(path):
    # Strip query parameters if any
    path = path.split("?")[0]
    # Replace Frontend parameters ${param} with *
    path = re.sub(r"\$\{[^}]+\}", "*", path)
    # Replace OpenAPI parameters {param} with *
    path = re.sub(r"\{[^}]+\}", "*", path)
    # Replace double slashes and trailing slashes
    path = re.sub(r"/+", "/", path)
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return path


def discover_frontend_scan_files(frontend_root: str) -> list[str]:
    """Return core frontend client files plus all API modules in src/lib/api/*.ts."""
    base_files = [
        "src/lib/api-client.ts",
        "src/lib/auth-context.tsx",
        "src/lib/stream-client.ts",
    ]
    api_dir = os.path.join(frontend_root, "src", "lib", "api")
    if os.path.isdir(api_dir):
        for entry in sorted(os.listdir(api_dir)):
            if (
                entry.endswith(".ts")
                and not entry.endswith(".test.ts")
                and entry != "example.functions.ts"
            ):
                base_files.append(f"src/lib/api/{entry}")
    return base_files


def _is_candidate_api_path(path: str) -> bool:
    if not path or not path.startswith("/") or path.startswith("//"):
        return False
    if re.search(r"\.(png|jpg|svg|ico|css|woff2?|ttf|jsx?|tsx?)$", path):
        return False
    norm = normalize_path(path)
    return any(norm == prefix or norm.startswith(f"{prefix}/") for prefix in API_ROOT_PREFIXES)


def get_frontend_paths(frontend_root, scan_files):
    """Scan multiple frontend files for API path references.

    Detects:
    - apiFetch<...>("/path", ...) and apiFetchBlob(`/path`)
    - Template literals starting with ${baseUrl}/path
    - String / template literals starting with / that match API root prefixes
    """
    paths = []

    for rel_file in scan_files:
        file_path = os.path.join(frontend_root, rel_file)
        if not os.path.exists(file_path):
            continue
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # 1. Direct apiFetch / apiFetchBlob literal or template literal arguments
        call_pattern = r"(?:apiFetch(?:Blob)?)(?:<[^>]+>)?\(\s*([`\"'])(/[^`\"']+)\1"
        for match in re.finditer(call_pattern, content):
            candidate = match.group(2).strip()
            if _is_candidate_api_path(candidate):
                paths.append(candidate)

        # 2. Template literals prefixed by a base URL interpolation: `${baseUrl}/auth/me`
        base_template_pattern = r"`\$\{[^}]+\}(/[^`]+)`"
        for match in re.finditer(base_template_pattern, content):
            candidate = match.group(1).strip()
            if _is_candidate_api_path(candidate):
                paths.append(candidate)

        # 3. Any string or template literal starting with / that is a root API path
        literal_pattern = r"([`\"'])(/[a-zA-Z0-9_/\-.$?={}&()*]+)\1"
        for match in re.finditer(literal_pattern, content):
            candidate = match.group(2).strip()
            if _is_candidate_api_path(candidate):
                paths.append(candidate)

    return sorted(set(paths))


def verify():
    backend_paths = get_backend_paths()
    frontend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))

    scan_files = discover_frontend_scan_files(frontend_root)
    frontend_paths = get_frontend_paths(frontend_root, scan_files)

    normalized_backend = {normalize_path(p): p for p in backend_paths}
    api_prefix = get_settings().api_v1_prefix.rstrip("/")
    for p in backend_paths:
        if p.startswith(f"{api_prefix}/"):
            normalized_backend[normalize_path(p[len(api_prefix) :])] = p
    # Add default docs/openapi routes and health check aliases
    normalized_backend["/docs"] = "/docs"
    normalized_backend["/redoc"] = "/redoc"
    normalized_backend["/openapi.json"] = "/openapi.json"
    normalized_backend["/health"] = "/health"

    # Known gaps tracked as TODOs — warn but don't block CI
    KNOWN_MISMATCHES = {
        "/api",  # Vite dev proxy prefix — frontend uses /api as base URL, Vite rewrites to /api/v1
    }

    errors = 0
    warnings = 0
    print("=== Verifying API Contracts ===")
    print(f"Detected {len(backend_paths)} backend paths.")
    print(f"Detected {len(frontend_paths)} frontend paths.")

    for f_path in sorted(frontend_paths):
        if not f_path.startswith("/"):
            continue
        norm_f = normalize_path(f_path)

        matched = False
        matched_backend_path = None
        for norm_b in normalized_backend:
            if norm_f.endswith("*") and norm_f[:-1] == norm_b:
                matched = True
                matched_backend_path = normalized_backend[norm_b]
                break
            # Segment-exact wildcard matching: replace * with [^/]+ so /documents/* does not swallow sub-routes
            pattern = re.escape(norm_b).replace(r"\*", "[^/]+")
            if re.match(f"^{pattern}$", norm_f):
                matched = True
                matched_backend_path = normalized_backend[norm_b]
                break

        if not matched:
            if norm_f in KNOWN_MISMATCHES:
                print(
                    f"WRN Known gap: Frontend calls '{f_path}' — no backend route (tracked as TODO)."
                )
                warnings += 1
            else:
                print(
                    f"ERR Mismatch: Frontend calls '{f_path}' (normalized: '{norm_f}') "
                    "but no matching backend route exists."
                )
                errors += 1
        else:
            print(f"OK Match: Frontend '{f_path}' -> Backend '{matched_backend_path}'")

    if errors > 0:
        print(f"\nVerification FAILED with {errors} mismatch(es) and {warnings} known gap(s).")
        sys.exit(1)
    elif warnings > 0:
        print(f"\nAll contracts verified (with {warnings} known gap(s) — tracked as TODOs).")
        sys.exit(0)
    else:
        print("\nAll API contracts verified successfully!")
        sys.exit(0)


if __name__ == "__main__":
    verify()
