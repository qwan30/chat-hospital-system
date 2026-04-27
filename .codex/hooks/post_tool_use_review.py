from __future__ import annotations

from hook_common import append_history, detect_phi, detect_secrets, print_json, read_payload, redact, sha256, tool_command, tool_output


def main() -> None:
    payload = read_payload()
    command = tool_command(payload)
    output = tool_output(payload)
    secret_hits = detect_secrets(output)
    phi_hits = detect_phi(output)

    append_history(
        payload,
        "post_tool_use",
        {
            "command_sha256": sha256(command) if command else None,
            "command_preview": redact(command) if command else None,
            "output_sha256": sha256(output) if output else None,
            "output_len": len(output),
            "secret_flags": secret_hits,
            "phi_flags": phi_hits,
        },
    )

    if secret_hits:
        print_json(
            {
                "decision": "block",
                "reason": "Tool output appears to contain secrets. Redact the output before using or quoting it.",
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": "A previous tool result was blocked because it appeared to expose secret material.",
                },
            }
        )
        return

    if phi_hits:
        print_json(
            {
                "systemMessage": "Tool output appears to contain patient identifiers. Use synthetic or de-identified data only.",
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": "Review the latest tool output for PHI-like identifiers before continuing.",
                },
            }
        )


if __name__ == "__main__":
    main()
