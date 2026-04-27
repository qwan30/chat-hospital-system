from __future__ import annotations

from hook_common import append_history, print_json, read_payload, repo_root


def main() -> None:
    payload = read_payload()
    root = repo_root(payload)
    append_history(payload, "session_start", {"source": payload.get("source")})

    rules_path = root / ".codex" / "PROJECT_RULES.md"
    rules_text = ""
    if rules_path.exists():
        rules_text = rules_path.read_text(encoding="utf-8").strip()

    context = (
        "Project Codex hooks are active. Follow AGENTS.md and the project-local rules below. "
        "Hook history is recorded as redacted metadata in .codex/history/hooks.jsonl.\n\n"
        f"{rules_text}"
    ).strip()

    print_json(
        {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            },
        }
    )


if __name__ == "__main__":
    main()
