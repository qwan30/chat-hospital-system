"""Versioned, immutable result contracts for AI evaluation runs."""

from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt


class ClinicalField(BaseModel):
    field_type: Literal["date", "dose", "number", "mrn"]
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
    name: Literal[
        "rot_90",
        "rot_180",
        "rot_270",
        "low_res_72dpi",
        "low_res_150dpi",
        "blur_light",
        "blur_heavy",
        "noise_gaussian",
        "contrast_low",
        "skew_slight",
        "low_dpi",
        "skew",
        "blur",
        "noise",
    ]
    seed: int
    width: int
    height: int
    sha256: str
    png_bytes: bytes

    class Config:
        frozen = True


class ClinicalFieldMatchResult(BaseModel):
    field_type: str
    gold_value: str
    extracted_value: Optional[str] = None
    exact_match: bool
    normalized_match: bool
    decimal_misread_risk: bool

    class Config:
        frozen = True


class OcrVariantMetric(BaseModel):
    variant_name: str
    page_count: int
    cer: float
    wer: float
    clinical_field_accuracy: float
    decimal_misread_count: int
    mean_latency_seconds: float

    class Config:
        frozen = True


class OcrEvaluationSummary(BaseModel):
    schema_version: Literal["2.0"] = "2.0"
    gold_page_count: int
    total_variants_evaluated: int
    overall_cer: float
    overall_wer: float
    overall_clinical_accuracy: float
    variant_metrics: tuple[OcrVariantMetric, ...]

    class Config:
        frozen = True


EvaluationComponent = Literal["corpus", "ocr", "retrieval", "graph", "chat", "harness"]
ResultStatus = Literal["passed", "failed", "skipped"]
RunStatus = Literal["passed", "failed", "skipped", "invalid"]
ScalarValue = Union[StrictBool, StrictInt, StrictFloat, str]


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


class MetricDriftComparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    metric_name: str
    baseline_value: float
    candidate_value: float
    delta: float
    tolerance: float
    higher_is_better: bool = True
    hard_gate_min: Optional[float] = None
    hard_gate_max: Optional[float] = None
    status: Literal["passed", "failed_drift", "failed_hard_gate"]


class DriftViolation(BaseModel):
    model_config = ConfigDict(frozen=True)

    metric_name: str
    violation_type: Literal["hard_gate", "relative_drift"]
    baseline_value: float
    candidate_value: float
    message: str


class DriftGateResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    verdict: Literal["GO", "NO-GO"]
    passed: bool
    total_metrics_evaluated: int
    violation_count: int
    violations: tuple[DriftViolation, ...]
    comparisons: tuple[MetricDriftComparison, ...]
    git_sha_baseline: str
    git_sha_candidate: str
