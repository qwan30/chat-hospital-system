"""Versioned, immutable result contracts for AI evaluation runs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, StrictBool, StrictFloat, StrictInt


class ClinicalField(BaseModel):
    field_type: Literal["date", "dose", "number"]
    value: str
    span_start: int
    span_end: int

    class Config:
        frozen = True


class OcrGoldPage(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    source_path: str
    source_sha256: str
    page_number: int
    native_text: str
    clinical_fields: tuple[ClinicalField, ...]

    class Config:
        frozen = True


class OcrEngineStatus(BaseModel):
    status: Literal["engine_unavailable", "engine_available_not_run"]
    available: bool
    reason: str

    class Config:
        frozen = True


class ScanVariant(BaseModel):
    name: Literal["low_dpi", "skew", "blur", "noise"]
    seed: int
    width: int
    height: int
    sha256: str
    png_bytes: bytes

    class Config:
        frozen = True


EvaluationComponent = Literal["corpus", "ocr", "retrieval", "graph", "chat", "harness"]
ResultStatus = Literal["passed", "failed", "skipped"]
RunStatus = Literal["passed", "failed", "skipped", "invalid"]
ScalarValue = StrictBool | StrictInt | StrictFloat | str


class GateResult(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    name: str
    component: EvaluationComponent
    passed: bool
    hard: bool
    observed: ScalarValue
    threshold: str
    details: str = ""

    class Config:
        frozen = True


class CaseResult(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    case_id: str
    component: EvaluationComponent
    status: ResultStatus
    metrics: dict[str, ScalarValue] = Field(default_factory=dict)
    gates: tuple[GateResult, ...] = ()
    reason: str = ""
    latency_ms: float = 0.0
    token_usage: int = 0

    class Config:
        frozen = True


class RunManifest(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    run_id: str
    suite: Literal["smoke", "release"]
    lane: Literal["deterministic", "live"]
    components: tuple[str, ...]
    status: RunStatus
    dataset_version: str
    git_sha: str
    provider: str
    model: str
    prompt_version: str
    configuration: dict[str, ScalarValue]
    started_at: str
    finished_at: str
    latency_ms: float
    token_usage: int
    selected_case_count: int
    passed_cases: int
    failed_cases: int
    skipped_cases: int
    failure_reason: str = ""

    class Config:
        frozen = True
