"""Unit tests for Threshold Artifact freezing, verification, and release gates."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from hospital_ai.evaluation.threshold_artifact import (
    ReleaseGateError,
    ThresholdArtifact,
    ThresholdCalibrationInput,
    check_holdout_gate,
    freeze_thresholds,
    verify_threshold_artifact,
)


def _sample_input() -> ThresholdCalibrationInput:
    return ThresholdCalibrationInput(
        corpus_version="hospital-ai-unified-clinical-corpus-v3",
        qualification_run_id="run-qual-2026",
        metric_version="v1.0.0",
        values={"recall_at_5": 0.90, "mrr": 0.85, "unauthorized_evidence_count": 0.0},
        calibration_date=datetime(2026, 8, 5, 12, 0, 0, tzinfo=UTC),
        git_sha="abcdef1234567890abcdef1234567890abcdef12",
    )


def test_freeze_thresholds_produces_immutable_artifact_with_hash() -> None:
    inp = _sample_input()
    artifact = freeze_thresholds(inp)
    assert artifact.frozen is True
    assert artifact.corpus_version == "hospital-ai-unified-clinical-corpus-v3"
    assert len(artifact.artifact_hash) == 64
    assert verify_threshold_artifact(artifact) is True


def test_verify_threshold_artifact_rejects_mutated_values() -> None:
    inp = _sample_input()
    artifact = freeze_thresholds(inp)
    # Simulate mutation by changing a threshold in a dict copy and rebuilding without updating hash
    mutated_data = artifact.dict()
    mutated_data["values"]["recall_at_5"] = 0.50
    mutated = ThresholdArtifact.construct(**mutated_data)
    assert verify_threshold_artifact(mutated) is False


def test_verify_threshold_artifact_rejects_unfrozen() -> None:
    inp = _sample_input()
    artifact = freeze_thresholds(inp)
    mutated_data = artifact.dict()
    mutated_data["frozen"] = False
    mutated = ThresholdArtifact.construct(**mutated_data)
    assert verify_threshold_artifact(mutated) is False


def test_check_holdout_gate_requires_frozen_artifact() -> None:
    # Non-holdout splits do not raise even without artifact
    check_holdout_gate(split="train", threshold_artifact=None)
    check_holdout_gate(split="qualification", threshold_artifact=None)

    # Holdout raises without frozen artifact
    with pytest.raises(ReleaseGateError, match="frozen threshold artifact required"):
        check_holdout_gate(split="holdout", threshold_artifact=None)

    # Holdout succeeds with valid artifact
    inp = _sample_input()
    artifact = freeze_thresholds(inp)
    check_holdout_gate(split="holdout", threshold_artifact=artifact)
