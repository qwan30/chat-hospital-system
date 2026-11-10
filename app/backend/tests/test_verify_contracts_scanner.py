import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import verify_contracts as vc  # noqa: E402


def test_verify_contracts_extracts_interpolated_api_paths() -> None:
    frontend_root = Path(__file__).resolve().parents[2] / "frontend"
    scan_files = vc.discover_frontend_scan_files(str(frontend_root))
    assert any(f.endswith("metrics.ts") for f in scan_files)
    paths = vc.get_frontend_paths(str(frontend_root), scan_files)
    normalized = {vc.normalize_path(p) for p in paths}
    assert "/metrics/vector" in normalized
    assert "/patients/*/labs" in normalized
    assert "/audit/logs" in normalized
    assert "/api/v1/metrics/vector" not in normalized
