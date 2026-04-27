from __future__ import annotations

from hook_common import append_history, print_json, read_payload, redact, sha256


def main() -> None:
    payload = read_payload()
    last_message = str(payload.get("last_assistant_message") or "")
    append_history(
        payload,
        "stop",
        {
            "stop_hook_active": payload.get("stop_hook_active"),
            "last_assistant_message_sha256": sha256(last_message) if last_message else None,
            "last_assistant_message_preview": redact(last_message) if last_message else None,
        },
    )
    print_json({"continue": True})


if __name__ == "__main__":
    main()
