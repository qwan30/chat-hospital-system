import argparse
import hashlib
import json
import os
import sys

REQUIRED_GATES = {
    "migration_chain",
    "legacy_parity",
    "zero_unauthorized_evidence",
    "zero_wrong_patient_citations",
    "zero_superseded_retrieval",
    "graph_provenance_coverage",
    "claim_validation",
    "sentinel_two_reviewers",
    "threshold_artifact_frozen",
    "hash_reproducibility",
    "ocr_strata_reported",
}


def check_gate(gate_name: str, evidence: dict, expected_sha: str) -> str:
    if not evidence.get("passed"):
        return "failed"
    if evidence.get("producer_sha") != expected_sha:
        return "stale"

    # Check tampered hash
    ev_copy = evidence.copy()
    ev_hash = ev_copy.pop("hash", None)
    if ev_hash is None:
        return "malformed"
    computed_hash = hashlib.sha256(json.dumps(ev_copy, sort_keys=True).encode()).hexdigest()
    if ev_hash != computed_hash:
        return "tampered"

    details = evidence.get("details", {})
    if gate_name == "sentinel_two_reviewers":
        if len(details.get("reviewers", [])) < 2:
            return "one reviewer"
    elif gate_name == "threshold_artifact_frozen":
        if details.get("status") != "frozen":
            return "unsigned/unfrozen threshold"
    elif gate_name == "ocr_strata_reported":
        if details.get("ocr_engine") == "fake":
            return "fake OCR output"

    return ""


def load_evidence(evidence_dir: str, expected_sha: str) -> dict:
    evidence_status = {}
    if not os.path.exists(evidence_dir):
        return evidence_status

    for filename in os.listdir(evidence_dir):
        if not filename.endswith(".json"):
            continue
        gate_name = filename[:-5]
        if gate_name not in REQUIRED_GATES:
            continue
        try:
            with open(os.path.join(evidence_dir, filename)) as f:
                evidence = json.load(f)
        except Exception:
            evidence_status[gate_name] = "malformed"
            continue

        reason = check_gate(gate_name, evidence, expected_sha)
        evidence_status[gate_name] = reason

    return evidence_status


def release_decision(evidence_status: dict, mode: str) -> str:
    if mode == "source":
        # Source contract only validates source contract and cannot return release GO.
        return "NO-GO"

    missing = REQUIRED_GATES - set(evidence_status.keys())
    failed = {name: reason for name, reason in evidence_status.items() if reason != ""}

    if missing or failed:
        if missing:
            print(f"Missing gates: {missing}")
        if failed:
            print(f"Failed gates: {failed}")
        return "NO-GO"
    return "GO"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["source", "artifact"], required=True)
    parser.add_argument("--evidence-dir", required=False, default="")
    parser.add_argument("--expected-git-sha", required=False, default="")
    args = parser.parse_args()

    if args.mode == "source":
        print("NO-GO")
        sys.exit(0)

    evidence_status = load_evidence(args.evidence_dir, args.expected_git_sha)
    decision = release_decision(evidence_status, args.mode)
    print(decision)
    if decision != "GO":
        sys.exit(1)


if __name__ == "__main__":
    main()
