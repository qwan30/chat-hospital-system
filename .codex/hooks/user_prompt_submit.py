from __future__ import annotations

from hook_common import append_history, block_prompt, detect_phi, detect_secrets, read_payload, redact, sha256


def main() -> None:
    payload = read_payload()
    prompt = str(payload.get("prompt") or "")
    secret_hits = detect_secrets(prompt)
    phi_hits = detect_phi(prompt)

    append_history(
        payload,
        "user_prompt_submit",
        {
            "prompt_sha256": sha256(prompt),
            "prompt_len": len(prompt),
            "prompt_preview": redact(prompt),
            "secret_flags": secret_hits,
            "phi_flags": phi_hits,
        },
    )

    if secret_hits:
        block_prompt(
            "Prompt appears to contain credentials or private key material. Remove secrets and use environment variable names or redacted examples."
        )
        return

    if phi_hits:
        block_prompt(
            "Prompt appears to contain direct patient identifiers. Use synthetic or de-identified hospital data before continuing."
        )


if __name__ == "__main__":
    main()
