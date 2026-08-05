"""Frozen Threshold Artifacts and release gate enforcement."""

from __future__ import annotations

import hmac
import json
from datetime import datetime
from hashlib import sha256
from typing import Any, Optional

from pydantic import BaseModel


class ReleaseGateError(ValueError):
    """Raised when evaluation fails release criteria or holdout gate conditions."""


class ThresholdCalibrationInput(BaseModel):
    corpus_version: str
    qualification_run_id: str
    metric_version: str
    values: dict[str, Any]
    calibration_date: datetime
    git_sha: str


class ThresholdArtifact(BaseModel):
    corpus_version: str
    qualification_run_id: str
    metric_implementation_version: str
    values: dict[str, Any]
    calibration_date: str
    git_sha: str
    artifact_hash: str
    frozen: bool = True

    class Config:
        frozen = True


def _canonical_payload(
    corpus_version: str,
    qualification_run_id: str,
    metric_version: str,
    values: dict[str, Any],
    calibration_date: str,
    git_sha: str,
) -> bytes:
    payload = {
        "corpus_version": corpus_version,
        "qualification_run_id": qualification_run_id,
        "metric_implementation_version": metric_version,
        "values": dict(sorted(values.items())),
        "calibration_date": calibration_date,
        "git_sha": git_sha,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def freeze_thresholds(input_data: ThresholdCalibrationInput) -> ThresholdArtifact:
    """Produce an immutable ThresholdArtifact with calculated canonical SHA256 hash."""
    date_str = input_data.calibration_date.isoformat()
    payload_bytes = _canonical_payload(
        corpus_version=input_data.corpus_version,
        qualification_run_id=input_data.qualification_run_id,
        metric_version=input_data.metric_version,
        values=input_data.values,
        calibration_date=date_str,
        git_sha=input_data.git_sha,
    )
    artifact_hash = sha256(payload_bytes).hexdigest()
    return ThresholdArtifact(
        corpus_version=input_data.corpus_version,
        qualification_run_id=input_data.qualification_run_id,
        metric_implementation_version=input_data.metric_version,
        values=dict(sorted(input_data.values.items())),
        calibration_date=date_str,
        git_sha=input_data.git_sha,
        artifact_hash=artifact_hash,
        frozen=True,
    )


def verify_threshold_artifact(artifact: ThresholdArtifact) -> bool:
    """Verify that a threshold artifact is frozen and has not been mutated."""
    if not artifact.frozen:
        return False
    payload_bytes = _canonical_payload(
        corpus_version=artifact.corpus_version,
        qualification_run_id=artifact.qualification_run_id,
        metric_version=artifact.metric_implementation_version,
        values=artifact.values,
        calibration_date=artifact.calibration_date,
        git_sha=artifact.git_sha,
    )
    expected_hash = sha256(payload_bytes).hexdigest()
    return hmac.compare_digest(artifact.artifact_hash, expected_hash)


def check_holdout_gate(split: str, threshold_artifact: Optional[ThresholdArtifact] = None) -> None:
    """Enforce that evaluating on the holdout split requires a verified frozen threshold artifact."""
    if split == "holdout":
        if threshold_artifact is None or not verify_threshold_artifact(threshold_artifact):
            raise ReleaseGateError("frozen threshold artifact required before evaluating holdout split")
