from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


SECRET_PATTERNS = [
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "OpenAI-style API key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*['\"]?[^'\"\s]{8,}"), "credential field"),
]

PHI_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "SSN-like identifier"),
    (re.compile(r"(?i)\b(MRN|medical record(?: number)?)\b\s*[:#-]?\s*\d{5,}"), "MRN-like identifier"),
    (re.compile(r"(?i)\b(DOB|date of birth)\b\s*[:#-]?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"), "DOB-like identifier"),
]

DESTRUCTIVE_PATTERNS = [
    (re.compile(r"(?i)\bgit\s+reset\s+--hard\b"), "git reset --hard would discard workspace changes"),
    (re.compile(r"(?i)\bgit\s+clean\s+-[^\s]*[fdx][^\s]*\b"), "git clean can delete untracked workspace files"),
    (re.compile(r"(?i)\bgit\s+checkout\s+--\b"), "git checkout -- can discard user changes"),
    (re.compile(r"(?i)\brm\s+-[^\s]*r[^\s]*f[^\s]*\s+(?:/|\.|\"\.\"|'\.')\b"), "recursive deletion of a broad path is blocked"),
    (re.compile(r"(?i)\bRemove-Item\b[^\n\r;|]*\b-Recurse\b[^\n\r;|]*\b-Force\b"), "recursive forced deletion is blocked"),
    (re.compile(r"(?i)\brd\s+/s\s+/q\b"), "recursive deletion is blocked"),
    (re.compile(r"(?i)\bformat\s+[A-Z]:"), "disk formatting is blocked"),
]

ENV_READ_PATTERNS = [
    re.compile(r"(?i)\b(cat|type|Get-Content)\b[^\n\r;|]*(^|\s)\.env(\.\w+)?\b"),
    re.compile(r"(?i)\b(cat|type|Get-Content)\b[^\n\r;|]*id_rsa\b"),
    re.compile(r"(?i)\b(cat|type|Get-Content)\b[^\n\r;|]*private[_-]?key\b"),
]


def read_payload() -> Dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw_stdin_sha256": sha256(raw), "_raw_stdin_len": len(raw)}
    return payload if isinstance(payload, dict) else {"payload": payload}


def repo_root(payload: Optional[Dict[str, Any]] = None) -> Path:
    starts: List[Path] = []
    if payload and payload.get("cwd"):
        starts.append(Path(str(payload["cwd"])))
    starts.append(Path.cwd())
    starts.append(Path(__file__).resolve())

    for start in starts:
        try:
            current = start.resolve()
        except OSError:
            continue
        if current.is_file():
            current = current.parent
        for candidate in [current, *current.parents]:
            if (candidate / ".codex").is_dir() and (candidate / "AGENTS.md").exists():
                return candidate

    return Path.cwd().resolve()


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256(value: Any) -> str:
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, default=str)
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def detect(patterns: Iterable, text: str) -> List[str]:
    hits = []
    for pattern, label in patterns:
        if pattern.search(text):
            hits.append(label)
    return hits


def detect_secrets(text: str) -> List[str]:
    return detect(SECRET_PATTERNS, text)


def detect_phi(text: str) -> List[str]:
    return detect(PHI_PATTERNS, text)


def redact(text: str, limit: int = 220) -> str:
    redacted = text
    for pattern, label in SECRET_PATTERNS + PHI_PATTERNS:
        redacted = pattern.sub(f"[REDACTED:{label}]", redacted)
    redacted = re.sub(r"\s+", " ", redacted).strip()
    if len(redacted) > limit:
        return redacted[: limit - 3] + "..."
    return redacted


def relpath(root: Path, value: Any) -> Optional[str]:
    if not value:
        return None
    try:
        path = Path(str(value)).resolve()
        return str(path.relative_to(root))
    except Exception:
        return str(value)


def tool_command(payload: Dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    return ""


def tool_output(payload: Dict[str, Any]) -> str:
    response = payload.get("tool_response")
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    return json.dumps(response, sort_keys=True, default=str)


def append_history(payload: Dict[str, Any], event: str, extra: Optional[Dict[str, Any]] = None) -> None:
    root = repo_root(payload)
    history_dir = root / ".codex" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    record: Dict[str, Any] = {
        "timestamp": utc_now(),
        "event": event,
        "hook_event_name": payload.get("hook_event_name"),
        "session_id": payload.get("session_id"),
        "turn_id": payload.get("turn_id"),
        "tool_name": payload.get("tool_name"),
        "model": payload.get("model"),
        "cwd": relpath(root, payload.get("cwd")),
    }
    if extra:
        record.update(extra)

    with (history_dir / "hooks.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, separators=(",", ":")))


def deny_pre_tool(reason: str) -> None:
    print_json(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    )


def deny_permission(reason: str) -> None:
    print_json(
        {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {
                    "behavior": "deny",
                    "message": reason,
                },
            }
        }
    )


def block_prompt(reason: str) -> None:
    print_json({"decision": "block", "reason": reason})
