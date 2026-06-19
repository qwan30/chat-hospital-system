import sys
import os
import re

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from hospital_ai.core.config import get_settings
from hospital_ai.main import create_app


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


def get_frontend_paths(frontend_root, scan_files):
    """Scan multiple frontend files for API path references.

    Detects:
    - apiFetch<...>("/path", ...)
    - fetch(`.../path`, ...)
    - fetch(url + "/path", ...)
    - String literals starting with / that look like API routes
    """
    paths = []

    for rel_file in scan_files:
        file_path = os.path.join(frontend_root, rel_file)
        if not os.path.exists(file_path):
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find apiFetch<...>("..." or `...`) calls — direct string literal args
        pattern = r'apiFetch(?:<[^>]+>)?\(\s*[`"\']([^`"\']+)[`"\'\s]*,?'
        for match in re.finditer(pattern, content):
            paths.append(match.group(1))

        # Find template-literal paths: `${...}/auth/me`, `${...}/patients/...`
        template_pattern = r"\$\{[^}]*\}(/[a-zA-Z0-9_/\-.*]+)"
        for match in re.finditer(template_pattern, content):
            path = match.group(1)
            if path and path.startswith("/"):
                paths.append(path)

        # Find string-concatenation paths: base + "/path"
        concat_pattern = r'["\']\s*\+\s*["\'](/[^"\']+)["\']'
        for match in re.finditer(concat_pattern, content):
            paths.append(match.group(1))

        # Match literal paths starting with / (for inline fetch, axios, etc.)
        literal_pattern = r'[`"\'](/\w[^`"\'\s?]{2,})[`"\']'
        for match in re.finditer(literal_pattern, content):
            path = match.group(1)
            # Filter out file paths, CSS, HTML, and non-API patterns
            if (
                path not in paths
                and not path.startswith("//")
                and not path.startswith("/@")
                and not path.startswith("/_")
                and not path.startswith("/node_modules")
                and not re.search(r"\.(png|jpg|svg|ico|css|woff2?|ttf|jsx?|tsx?)$", path)
            ):
                paths.append(path)

    return list(set(paths))


def verify():
    backend_paths = get_backend_paths()
    frontend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))

    # Scan frontend files that make real API calls (not mock data)
    scan_files = [
        "src/lib/api-client.ts",
        "src/lib/auth-context.tsx",
        "src/lib/stream-client.ts",
    ]

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
        "/auth/token",  # TODO: backend needs JWT token endpoint (currently uses static tokens)
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
            # Simple wildcard matching: replace * with .*
            pattern = re.escape(norm_b).replace(r"\*", ".*")
            if re.match(f"^{pattern}$", norm_f):
                matched = True
                matched_backend_path = normalized_backend[norm_b]
                break

        if not matched:
            if norm_f in KNOWN_MISMATCHES:
                print(f"WRN Known gap: Frontend calls '{f_path}' — no backend route (tracked as TODO).")
                warnings += 1
            else:
                print(
                    f"ERR Mismatch: Frontend calls '{f_path}' (normalized: '{norm_f}') but no matching backend route exists."
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
