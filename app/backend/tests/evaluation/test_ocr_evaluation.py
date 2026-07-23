from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import fitz

from hospital_ai.evaluation.corpus_manifest import build_corpus_manifest
from hospital_ai.evaluation.ocr_evaluation import (
    build_ocr_gold_pages,
    probe_image_ocr_engine,
    render_scan_variants,
    run_isolated_paddle_ocr,
)

BACKEND_ROOT = Path(__file__).parents[2]
DATA_ROOT = BACKEND_ROOT / "data"


def _write_fixture_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=300, height=200)
    page.insert_text((24, 50), "Metformin 500 mg on 2026-07-22")
    document.save(path)
    document.close()


def test_gold_pages_are_bound_to_pdf_hash_page_and_native_text() -> None:
    manifest = build_corpus_manifest(DATA_ROOT)
    pages = build_ocr_gold_pages(manifest, DATA_ROOT, limit=2)

    assert len(pages) == 2
    for gold in pages:
        source = DATA_ROOT / gold.source_path
        assert gold.source_sha256 == hashlib.sha256(source.read_bytes()).hexdigest()
        assert gold.page_number >= 1
        assert gold.native_text.strip()
    assert any(gold.clinical_fields for gold in pages)


def test_scan_variants_are_reproducible_and_seeded(tmp_path: Path) -> None:
    pdf_path = tmp_path / "fixture.pdf"
    _write_fixture_pdf(pdf_path)

    first = render_scan_variants(pdf_path, page_number=1, seed=713)
    second = render_scan_variants(pdf_path, page_number=1, seed=713)
    changed_seed = render_scan_variants(pdf_path, page_number=1, seed=714)

    expected_names = (
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
    )
    assert tuple(variant.name for variant in first) == expected_names
    assert tuple(variant.sha256 for variant in first) == tuple(variant.sha256 for variant in second)
    assert (
        next(item for item in first if item.name == "noise_gaussian").sha256
        != next(item for item in changed_seed if item.name == "noise_gaussian").sha256
    )
    assert all(variant.png_bytes.startswith(b"\x89PNG") for variant in first)



def test_missing_paddle_dependencies_are_explicitly_unavailable() -> None:
    status = probe_image_ocr_engine(find_spec=lambda _name: None)

    assert status.status == "engine_unavailable"
    assert not status.available
    assert "paddleocr" in status.reason
    assert "paddlepaddle" in status.reason


def test_available_paddle_dependencies_do_not_claim_an_ocr_run() -> None:
    status = probe_image_ocr_engine(find_spec=lambda _name: object())

    assert status.status == "engine_available_not_run"
    assert status.available
    assert "not executed" in status.reason


def test_isolated_paddle_worker_without_configured_interpreter_is_explicitly_unavailable() -> None:
    result = run_isolated_paddle_ocr(b"\x89PNG\r\n\x1a\nfixture", isolated_python=None)

    assert result.status == "engine_unavailable"
    assert not result.available
    assert "not configured" in result.reason


def test_isolated_paddle_worker_uses_a_new_windows_process_group_and_json_contract() -> None:
    observed: dict[str, object] = {}

    class FakeProcess:
        pid = 7001
        returncode = 0

        def communicate(self, *, timeout: float) -> tuple[str, str]:
            observed["timeout"] = timeout
            return (
                json.dumps(
                    {
                        "status": "executed",
                        "text": "Metformin 500 mg",
                        "rec_scores": [0.99, 0.98],
                    }
                ),
                "",
            )

        def poll(self) -> int:
            return 0

    def fake_popen(command: list[str], **kwargs: object) -> FakeProcess:
        observed["command"] = command
        observed["kwargs"] = kwargs
        image_path = Path(command[-1])
        assert image_path.exists()
        assert image_path.read_bytes().startswith(b"\x89PNG")
        return FakeProcess()

    result = run_isolated_paddle_ocr(
        b"\x89PNG\r\n\x1a\nfixture",
        isolated_python=Path("C:/isolated/python.exe"),
        worker_script=Path("C:/worker/ocr_worker.py"),
        popen=fake_popen,
        is_windows=True,
    )

    assert result.status == "executed"
    assert result.available
    assert result.text == "Metformin 500 mg"
    assert result.rec_scores == (0.99, 0.98)
    assert observed["command"][:3] == [
        str(Path("C:/isolated/python.exe")),
        str(Path("C:/worker/ocr_worker.py")),
        "--image",
    ]
    assert not Path(observed["command"][-1]).exists()
    assert observed["timeout"] == 60.0
    assert observed["kwargs"] == {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "shell": False,
        "creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    }


def test_isolated_paddle_worker_timeout_kills_the_windows_process_tree() -> None:
    observed: dict[str, object] = {}

    class TimeoutProcess:
        pid = 7002
        returncode = None

        def communicate(self, *, timeout: float) -> tuple[str, str]:
            raise subprocess.TimeoutExpired("ocr-worker", timeout)

        def poll(self) -> None:
            return None

    def fake_popen(_command: list[str], **_kwargs: object) -> TimeoutProcess:
        return TimeoutProcess()

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    result = run_isolated_paddle_ocr(
        b"\x89PNG\r\n\x1a\nfixture",
        isolated_python=Path("C:/isolated/python.exe"),
        worker_script=Path("C:/worker/ocr_worker.py"),
        popen=fake_popen,
        run=fake_run,
        is_windows=True,
    )

    assert result.status == "execution_failed"
    assert not result.available
    assert "timed out" in result.reason
    assert observed["command"] == ["taskkill", "/PID", "7002", "/T", "/F"]
    assert observed["kwargs"] == {
        "capture_output": True,
        "check": False,
        "text": True,
        "shell": False,
        "timeout": 5,
    }


def test_isolated_paddle_worker_fails_explicitly_for_malformed_output() -> None:
    class FakeProcess:
        pid = 7003
        returncode = 0

        def communicate(self, *, timeout: float) -> tuple[str, str]:
            return "not json", ""

        def poll(self) -> int:
            return 0

    def fake_popen(_command: list[str], **_kwargs: object) -> FakeProcess:
        return FakeProcess()

    result = run_isolated_paddle_ocr(
        b"\x89PNG\r\n\x1a\nfixture",
        isolated_python=Path("C:/isolated/python.exe"),
        worker_script=Path("C:/worker/ocr_worker.py"),
        popen=fake_popen,
    )

    assert result.status == "execution_failed"
    assert not result.available
    assert result.text == ""
    assert "invalid JSON" in result.reason


def test_paddle_worker_forces_conservative_cpu_configuration(tmp_path: Path, monkeypatch, capsys) -> None:
    observed: dict[str, object] = {}

    class FakePaddleOCR:
        def __init__(self, **kwargs: object) -> None:
            observed["kwargs"] = kwargs

        def predict(self, _image: str) -> list[object]:
            return []

    script_path = BACKEND_ROOT / "scripts" / "run_paddle_ocr_worker.py"
    spec = importlib.util.spec_from_file_location("test_paddle_worker", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    image_path = tmp_path / "scan.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
    monkeypatch.setitem(sys.modules, "paddleocr", type("PaddleModule", (), {"PaddleOCR": FakePaddleOCR}))

    assert module.main(["--image", str(image_path)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "executed"
    assert observed["kwargs"] == {
        "device": "cpu",
        "cpu_threads": 2,
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": False,
    }


def test_ocr_contract_instantiation() -> None:
    from hospital_ai.evaluation.contracts import (
        ClinicalFieldMatchResult,
        OcrEvaluationSummary,
        OcrVariantMetric,
    )

    match_res = ClinicalFieldMatchResult(
        field_type="dose",
        gold_value="5.0 mg",
        extracted_value="50 mg",
        exact_match=False,
        normalized_match=False,
        decimal_misread_risk=True,
    )
    assert match_res.decimal_misread_risk is True

    metric = OcrVariantMetric(
        variant_name="blur_light",
        page_count=100,
        cer=0.05,
        wer=0.12,
        clinical_field_accuracy=0.92,
        decimal_misread_count=1,
        mean_latency_seconds=0.45,
    )
    assert metric.variant_name == "blur_light"

    summary = OcrEvaluationSummary(
        gold_page_count=100,
        total_variants_evaluated=10,
        overall_cer=0.04,
        overall_wer=0.10,
        overall_clinical_accuracy=0.94,
        variant_metrics=(metric,),
    )
    assert summary.gold_page_count == 100


def test_match_clinical_fields_dosage_and_decimal_misread() -> None:
    from hospital_ai.evaluation.contracts import ClinicalField
    from hospital_ai.evaluation.ocr_evaluation import match_clinical_fields

    gold_fields = (
        ClinicalField(field_type="dose", value="5.0 mg", span_start=0, span_end=6),
        ClinicalField(field_type="mrn", value="MRN-0022", span_start=10, span_end=18),
        ClinicalField(field_type="date", value="2026-07-24", span_start=20, span_end=30),
    )

    # Test 1: Exact match with dosage formatting tolerance (5.0 mg vs 5mg)
    extracted_1 = "Patient MRN0022 took 5mg on 2026-07-24"
    res_1 = match_clinical_fields(gold_fields, extracted_1)
    dose_res = next(r for r in res_1 if r.field_type == "dose")
    assert dose_res.normalized_match is True
    assert dose_res.decimal_misread_risk is False

    # Test 2: Catastrophic decimal misread (5.0 mg read as 50 mg)
    extracted_2 = "Patient MRN0022 took 50 mg on 2026-07-24"
    res_2 = match_clinical_fields(gold_fields, extracted_2)
    dose_res_2 = next(r for r in res_2 if r.field_type == "dose")
    assert dose_res_2.normalized_match is False
    assert dose_res_2.decimal_misread_risk is True


def test_evaluate_ocr_corpus_mock_run(tmp_path: Path) -> None:
    import fitz

    import uuid
    from hospital_ai.evaluation.corpus_manifest import CorpusManifestV2, EvidenceLocator, SourceArtifact
    from hospital_ai.evaluation.ocr_evaluation import evaluate_ocr_corpus, export_ocr_evaluation_markdown

    pdf_file = tmp_path / "docs" / "sample.pdf"
    pdf_file.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    p = doc.new_page(width=300, height=200)
    p.insert_text((50, 50), "MRN-9988 Dose: 10 mg Date: 2026-07-24")
    doc.save(str(pdf_file))
    doc.close()

    manifest = CorpusManifestV2(
        schema_version="2.0",
        artifacts=(
            SourceArtifact(
                canonical_relative_path="docs/sample.pdf",
                source_sha256="a" * 64,
                kind="patient_document",
                mime_type="application/pdf",
                document_type="clinical_note",
                generator="test",
                generator_version="1.0",
                provenance_status="synthesized",
                license_status="permissive",
                patient_id=uuid.uuid4(),
                locator=EvidenceLocator(source_path="docs/sample.pdf"),
            ),
        ),
    )


    summary = evaluate_ocr_corpus(manifest, tmp_path, limit_pages=1, use_mock_ocr=True)
    assert summary.gold_page_count == 1
    assert len(summary.variant_metrics) == 10

    report_path = tmp_path / "report.md"
    export_ocr_evaluation_markdown(summary, report_path)
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "OCR Evaluation Harness Summary" in content
    assert "blur_light" in content




