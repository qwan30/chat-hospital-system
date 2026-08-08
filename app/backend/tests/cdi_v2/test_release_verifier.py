import json
import os
import subprocess

import pytest

VERIFIER_SCRIPT = os.path.join(os.path.dirname(__file__), "../../scripts/verify_cdi_v2_release.py")

REQUIRED_GATES = [
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
]


def run_verifier(evidence_dir, expected_sha="abcdef1234567890", mode="artifact"):
    cmd = [
        "python",
        VERIFIER_SCRIPT,
        "--mode",
        mode,
        "--evidence-dir",
        evidence_dir,
        "--expected-git-sha",
        expected_sha,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def create_valid_evidence(gate_name, sha="abcdef1234567890", details=None):
    if details is None:
        details = {}
        if gate_name == "sentinel_two_reviewers":
            details = {"reviewers": ["alice", "bob"]}
        elif gate_name == "threshold_artifact_frozen":
            details = {"status": "frozen", "signature": "valid"}
        elif gate_name == "ocr_strata_reported":
            details = {"ocr_engine": "paddle_v2"}

    return {
        "gate_name": gate_name,
        "passed": True,
        "source_artifact": f"s3://bucket/artifacts/{gate_name}.zip",
        "producer_sha": sha,
        "schema_version": "1.0.0",
        "hash": "dummyhash",
        "details": details,
    }


@pytest.fixture
def evidence_dir(tmp_path):
    d = tmp_path / "cdi-v2"
    d.mkdir()
    return str(d)


def test_empty_directory(evidence_dir):
    res = run_verifier(evidence_dir)
    assert res.returncode != 0
    assert "NO-GO" in res.stdout


def test_one_missing_gate(evidence_dir):
    for gate in REQUIRED_GATES[:-1]:
        with open(os.path.join(evidence_dir, f"{gate}.json"), "w") as f:
            json.dump(create_valid_evidence(gate), f)
    res = run_verifier(evidence_dir)
    assert res.returncode != 0
    assert "NO-GO" in res.stdout
    assert REQUIRED_GATES[-1] in res.stdout


def test_failed_gate(evidence_dir):
    for gate in REQUIRED_GATES:
        ev = create_valid_evidence(gate)
        if gate == "legacy_parity":
            ev["passed"] = False
        with open(os.path.join(evidence_dir, f"{gate}.json"), "w") as f:
            json.dump(ev, f)
    res = run_verifier(evidence_dir)
    assert res.returncode != 0
    assert "NO-GO" in res.stdout


def test_stale_head_sha(evidence_dir):
    for gate in REQUIRED_GATES:
        ev = create_valid_evidence(gate, sha="stalesha000")
        with open(os.path.join(evidence_dir, f"{gate}.json"), "w") as f:
            json.dump(ev, f)
    res = run_verifier(evidence_dir, expected_sha="abcdef1234567890")
    assert res.returncode != 0
    assert "NO-GO" in res.stdout


def test_hash_mismatch(evidence_dir):
    import hashlib

    for gate in REQUIRED_GATES:
        ev = create_valid_evidence(gate)
        ev_copy = ev.copy()
        ev_copy.pop("hash", None)
        ev["hash"] = hashlib.sha256(json.dumps(ev_copy, sort_keys=True).encode()).hexdigest()
        if gate == "migration_chain":
            ev["hash"] = "tampered_hash"
        with open(os.path.join(evidence_dir, f"{gate}.json"), "w") as f:
            json.dump(ev, f)
    res = run_verifier(evidence_dir)
    assert res.returncode != 0
    assert "NO-GO" in res.stdout


def test_unsigned_unfrozen_threshold(evidence_dir):
    for gate in REQUIRED_GATES:
        ev = create_valid_evidence(gate)
        if gate == "threshold_artifact_frozen":
            ev["details"] = {"status": "unfrozen"}
        with open(os.path.join(evidence_dir, f"{gate}.json"), "w") as f:
            json.dump(ev, f)
    res = run_verifier(evidence_dir)
    assert res.returncode != 0
    assert "NO-GO" in res.stdout


def test_one_reviewer(evidence_dir):
    for gate in REQUIRED_GATES:
        ev = create_valid_evidence(gate)
        if gate == "sentinel_two_reviewers":
            ev["details"] = {"reviewers": ["alice"]}
        with open(os.path.join(evidence_dir, f"{gate}.json"), "w") as f:
            json.dump(ev, f)
    res = run_verifier(evidence_dir)
    assert res.returncode != 0
    assert "NO-GO" in res.stdout


def test_fake_ocr_output(evidence_dir):
    for gate in REQUIRED_GATES:
        ev = create_valid_evidence(gate)
        if gate == "ocr_strata_reported":
            ev["details"] = {"ocr_engine": "fake"}
        with open(os.path.join(evidence_dir, f"{gate}.json"), "w") as f:
            json.dump(ev, f)
    res = run_verifier(evidence_dir)
    assert res.returncode != 0
    assert "NO-GO" in res.stdout


def test_complete_valid_synthetic_fixture(evidence_dir):
    # We must compute proper hash for tampered check!
    import hashlib

    for gate in REQUIRED_GATES:
        ev = create_valid_evidence(gate)
        # Compute hash
        ev_copy = ev.copy()
        ev_copy.pop("hash", None)
        ev["hash"] = hashlib.sha256(json.dumps(ev_copy, sort_keys=True).encode()).hexdigest()

        with open(os.path.join(evidence_dir, f"{gate}.json"), "w") as f:
            json.dump(ev, f)
    res = run_verifier(evidence_dir)
    assert res.returncode == 0
    assert res.stdout.strip() == "GO"


def test_mode_source_cannot_return_go(evidence_dir):
    import hashlib

    for gate in REQUIRED_GATES:
        ev = create_valid_evidence(gate)
        ev_copy = ev.copy()
        ev_copy.pop("hash", None)
        ev["hash"] = hashlib.sha256(json.dumps(ev_copy, sort_keys=True).encode()).hexdigest()
        with open(os.path.join(evidence_dir, f"{gate}.json"), "w") as f:
            json.dump(ev, f)
    res = run_verifier(evidence_dir, mode="source")
    assert res.stdout.strip() == "NO-GO"
