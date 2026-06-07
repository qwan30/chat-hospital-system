import sys
import os
import re
import json

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from hospital_ai.main import app

def get_backend_paths():
    openapi = app.openapi()
    paths = list(openapi.get("paths", {}).keys())
    return paths

def normalize_path(path):
    # Strip query parameters if any
    path = path.split("?")[0]
    # Replace OpenAPI parameters {param} with *
    path = re.sub(r'\{[^}]+\}', '*', path)
    # Replace Frontend parameters ${param} with *
    path = re.sub(r'\$\{[^}]+\}', '*', path)
    # Replace double slashes and trailing slashes
    path = re.sub(r'/+', '/', path)
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return path

def get_frontend_paths(api_client_path):
    with open(api_client_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find apiFetch<...>("..." or `...`) calls
    paths = []
    pattern = r'apiFetch(?:<[^>]+>)?\(\s*[`"\']([^`"\']+)[`"\'\s]*,?'
    for match in re.finditer(pattern, content):
        paths.append(match.group(1))
        
    # Match custom fetch URLs and literal paths starting with /
    literal_pattern = r'[`"\'](/[^`"\'\s?]+)[`"\']'
    for match in re.finditer(literal_pattern, content):
        path = match.group(1)
        if path not in paths and not path.startswith("//"):
            paths.append(path)
            
    return list(set(paths))

def verify():
    backend_paths = get_backend_paths()
    frontend_client_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/src/lib/api-client.ts"))
    
    if not os.path.exists(frontend_client_file):
        print(f"Error: Frontend API client not found at {frontend_client_file}")
        sys.exit(1)
        
    frontend_paths = get_frontend_paths(frontend_client_file)
    
    normalized_backend = {normalize_path(p): p for p in backend_paths}
    # Add default docs/openapi routes and health check aliases
    normalized_backend["/docs"] = "/docs"
    normalized_backend["/redoc"] = "/redoc"
    normalized_backend["/openapi.json"] = "/openapi.json"
    normalized_backend["/health"] = "/health"
    
    errors = 0
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
            # Simple wildcard matching: replace * with .*
            pattern = re.escape(norm_b).replace(r'\*', '.*')
            if re.match(f"^{pattern}$", norm_f):
                matched = True
                matched_backend_path = normalized_backend[norm_b]
                break
                
        if not matched:
            print(f"❌ Mismatch: Frontend calls '{f_path}' (normalized: '{norm_f}') but no matching backend route exists.")
            errors += 1
        else:
            print(f"✅ Match: Frontend '{f_path}' -> Backend '{matched_backend_path}'")
            
    if errors > 0:
        print(f"\nVerification FAILED with {errors} contract mismatch(es).")
        sys.exit(1)
    else:
        print("\nAll API contracts verified successfully!")
        sys.exit(0)

if __name__ == "__main__":
    verify()
