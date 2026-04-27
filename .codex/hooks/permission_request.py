from __future__ import annotations

from hook_common import DESTRUCTIVE_PATTERNS, append_history, deny_permission, read_payload, redact, sha256, tool_command


def main() -> None:
    payload = read_payload()
    command = tool_command(payload)

    append_history(
        payload,
        "permission_request",
        {
            "command_sha256": sha256(command) if command else None,
            "command_preview": redact(command) if command else None,
            "description": redact(str(payload.get("tool_input", {}).get("description", "")))
            if isinstance(payload.get("tool_input"), dict)
            else None,
        },
    )

    if command:
        for pattern, reason in DESTRUCTIVE_PATTERNS:
            if pattern.search(command):
                deny_permission(reason)
                return


if __name__ == "__main__":
    main()
