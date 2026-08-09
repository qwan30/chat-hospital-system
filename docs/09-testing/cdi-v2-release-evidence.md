# CDI V2 Release Evidence

This document outlines the artifact-backed release gating mechanism for the CDI V2 pipeline. 

## Mechanism

Instead of simulating release verification in CI, we now validate explicit artifact paths for the required release gates.
The verification is done via `scripts/verify_cdi_v2_release.py`.

The required gates are:
- `migration_chain`
- `legacy_parity`
- `zero_unauthorized_evidence`
- `zero_wrong_patient_citations`
- `zero_superseded_retrieval`
- `graph_provenance_coverage`
- `claim_validation`
- `sentinel_two_reviewers`
- `threshold_artifact_frozen`
- `hash_reproducibility`
- `ocr_strata_reported`

## Evidence Format

Evidence is provided as a directory of JSON files matching the release-evidence schema (`release-evidence.schema.json`).
Each file is named after the gate (e.g. `migration_chain.json`).

The `verify_cdi_v2_release.py` script requires:
- `--mode`: `artifact` or `source`. `artifact` checks for valid evidence and can return `GO`. `source` validates the source contract only and always returns `NO-GO`.
- `--evidence-dir`: Directory containing the evidence JSON files.
- `--expected-git-sha`: The expected commit SHA of the artifacts.

## Exit Status

The verification script exits with a non-zero exit code and outputs `NO-GO` if:
- Required gates are missing.
- The evidence contains a false `passed` status.
- The producer SHA doesn't match the expected SHA.
- The hash of the artifact doesn't match.
- Specific gate requirements aren't met (e.g. fewer than 2 reviewers for sentinel gate, unfrozen status, etc.).

When all checks pass in `artifact` mode, the script outputs `GO` and exits with code `0`.
