from __future__ import annotations

from hook_common import (
    DESTRUCTIVE_PATTERNS,
    ENV_READ_PATTERNS,
    append_history,
    deny_pre_tool,
    read_payload,
    redact,
    sha256,
    tool_command,
)


def main() -> None:
    payload = read_payload()
    command = tool_command(payload)

    append_history(
        payload,
        "pre_tool_use",
        {
            "command_sha256": sha256(command) if command else None,
            "command_preview": redact(command) if command else None,
        },
    )

    if command:
        for pattern, reason in DESTRUCTIVE_PATTERNS:
            if pattern.search(command):
                deny_pre_tool(reason)
                return

        for pattern in ENV_READ_PATTERNS:
            if pattern.search(command):
                deny_pre_tool(
                    "Reading secrets or private key files directly is blocked. Use redacted examples or environment variable names instead."
                )
                return


if __name__ == "__main__":
    main()
