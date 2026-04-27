# Codex Project Configuration

This directory contains project-local Codex configuration for the hospital knowledge assistant workspace.

- `config.toml` enables Codex hooks, project logs, and bounded native history persistence.
- `rules/default.rules` defines command approval rules for risky shell prefixes.
- `hooks/` contains deterministic hook scripts for project context, prompt checks, tool checks, and redacted history events.
- `history/` stores local generated hook metadata. Generated JSONL files are ignored because they may contain operational details.

To activate this layer, trust this project's `.codex` configuration in Codex and restart the session. The hook commands are Windows PowerShell based and walk upward from the current directory until they find `.codex/hooks/run_hook.ps1`.
