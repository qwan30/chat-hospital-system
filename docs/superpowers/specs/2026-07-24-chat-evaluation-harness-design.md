# Chat Evaluation Harness & Approved LLM Judge / Observer Design Spec

> **Date:** 2026-07-24  
> **Target Branch:** `feat/chat-eval-harness-llm-judge`  
> **Scope:** Fix deterministic chat gate failures (`sse_transport_coverage`), implement live SSE stream evaluation, integrate an approved PHI-safe LLM Judge & Observer, and resolve 0.0 metric reporting across the RAG Chat benchmark suite.

---

## 1. Executive Summary & Problem Statement

### 1.1 Current Limitations
1. **Deterministic Gate Failure (`sse_transport_coverage`):**  
   The existing `ProductChatAdapter` sets `stream_safety_outcome="not_evaluated"` because it calls non-streaming `ChatService.answer()`. However, `runner.py` explicitly gates `component == "chat"` on `stream_safety_outcome != "not_evaluated"`, causing mandatory gate failure.
2. **0.0 Metric Reporting in Live Lane:**  
   In live evaluations (`--lane live`), `Faithfulness`, `Relevance`, and `Citation Precision/Recall` report `0.00` with status `FAILED`. This stems from a mismatch between raw LLM output text formatting and rigid citation/term substring matching, combined with the lack of an active, approved LLM Judge engine.
3. **HIPAA & PHI Security Risk:**  
   Sending raw patient queries and retrieved clinical chunks to third-party LLM judges risks leaking Protected Health Information (PHI). An automated pre-judge PHI redaction engine is required.

### 1.2 Target Objectives
- Achieve 100% Pass Rate on Chat benchmark cases in deterministic mode.
- Resolve `sse_transport_coverage` by evaluating both non-streaming and Server-Sent Events (SSE) chat streams.
- Introduce an isolated, Pydantic-backed `LLMJudge` engine with PHI redaction and deterministic fallback options.
- Parse citations (markdown links `[doc_title](chunk_id)`, `[E1]`, and numeric locators) into valid `cited_chunk_ids` for accurate Citation Precision/Recall.
- Align quality gates strictly with official project standards defined in [test-plan.md](file:///d:/projects/chatbot-hospital-system/docs/09-testing/test-plan.md): **Faithfulness ≥ 90%**, **Citation Rate ≥ 95%**, **Safe Refusal Rate ≥ 90%**, **Context Leakage = 0%**.

### 1.3 Full Benchmark Dataset & Corpus Scope
- **Benchmark Suite (`rag_benchmark_v2.jsonl`):** Executes evaluation across all **300 real clinical test cases** in the project, encompassing multi-hop graph queries, patient scope security adversaries, single-doc lab checks, and clinical absence checks.
- **Corpus Materialization (`corpus_manifest_v2.json`):** Leverages the full synthetic hospital document corpus (all patient records, lab reports, discharge summaries) materialized in SQLite evaluation memory.
- **Suite Execution Modes:**
  - `--suite release`: Runs full evaluation across **all 300 benchmark cases**.
  - `--suite smoke`: Fast developer sanity check running a 10-case stratified subset (< 15 seconds).

---

## 2. System Architecture

```
                                ┌────────────────────────────────────────────────────────┐
                                │ CLI: python scripts/run_ai_evaluation.py               │
                                │      --components chat --lane deterministic|live       │
                                └───────────────────────────┬────────────────────────────┘
                                                            │
                       ┌────────────────────────────────────┴────────────────────────────────────┐
                       ▼                                                                         ▼
┌───────────────────────────────────────────┐                             ┌───────────────────────────────────────────┐
│        Deterministic Lane Adapter         │                             │            Live Lane Adapter              │
├───────────────────────────────────────────┤                             ├───────────────────────────────────────────┤
│ • ProductChatAdapter                      │                             │ • ProductLiveChatAdapter                  │
│ • SSE Stream Safety Evaluator             │                             │ • Live Citation & Token Extractor         │
│ • InMemoryEvaluationObserver              │                             │ • PHI Redaction Pre-Processor Engine      │
│ • sse_transport_coverage = "answered"     │                             │ • Pydantic Structured LLM Judge Engine    │
└───────────────────────────────────────────┘                             └───────────────────────────────────────────┘
```

---

## 3. Detailed Component & File Plan

| File Path | Responsibility | Action |
|---|---|---|
| `app/backend/src/hospital_ai/evaluation/product_chat_adapter.py` | Deterministic Chat Adapter | [MODIFY] Add SSE stream safety evaluation logic so `stream_safety_outcome` is populated (`"answered"` or `"refused"`). |
| `app/backend/src/hospital_ai/evaluation/citation_parser.py` | Citation Extraction Engine | [NEW] Implement regex & AST citation parser to extract chunk/locator IDs from markdown and plain-text responses. |
| `app/backend/src/hospital_ai/evaluation/llm_judge.py` | LLM Judge & PHI Redactor | [NEW] Implement `LLMJudge` using Pydantic JSON schema (`faithfulness`, `relevance`, `reasoning`), PHI masking gate, and fallback terms matcher. |
| `app/backend/src/hospital_ai/evaluation/runner.py` | Evaluation Runner & Scoring | [MODIFY] Integrate citation parser and LLM Judge scoring into the `chat` evaluation pipeline. |
| `app/backend/scripts/run_ai_evaluation.py` | Evaluation Runner CLI | [MODIFY] Support `--llm-judge-provider local|cloud|stub` flags. |
| `app/backend/tests/evaluation/test_product_chat_adapter.py` | Chat Adapter Unit Tests | [MODIFY] Add test cases for SSE stream evaluation and citation parsing. |
| `app/backend/tests/evaluation/test_llm_judge.py` | LLM Judge Unit Tests | [NEW] Test PHI redaction, JSON schema parsing, and fallback evaluation behavior. |
| `docs/09-testing/chat-evaluation-harness-20260724.md` | Public Evaluation Report | [NEW] Publish final Chat evaluation metrics report upon completion. |

---

## 4. Technical Specifications

### 4.1 Citation Parser (`citation_parser.py`)
```python
from uuid import UUID
import re

CITATION_REGEX = re.compile(
    r'\[(?:E|EVIDENCE-)?([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\]|'
    r'\[([^\]]+)\]\((?:[^\)]*?chunk_id=)?([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\)'
)

def extract_cited_chunk_ids(answer_text: str, available_chunks: dict[str, UUID]) -> set[UUID]:
    """Extract cited UUIDs from answer text matching markdown links, explicit UUIDs, or locators."""
    ...
```

### 4.2 PHI Masking & LLM Judge (`llm_judge.py`)
```python
from pydantic import BaseModel, Field

class LLMJudgeScore(BaseModel):
    faithfulness: float = Field(ge=0.0, le=1.0, description="Factuality of answer against context")
    relevance: float = Field(ge=0.0, le=1.0, description="Relevance of answer to patient question")
    reasoning: str = Field(description="Step-by-step reasoning for the scores")

def redact_patient_phi(text: str) -> str:
    """Mask HIPAA 18 identifiers (Patient Names, Record IDs, DOBs) with placeholders."""
    ...
```

### 4.3 API Key & Environment Configuration
- **Deterministic Lane (`--lane deterministic`):** **No API Keys required** ($0 API cost). Runs 100% locally using in-memory SQLite, stub chat generator, and deterministic embeddings.
- **Gemini Cloud Live Lane (`--llm-judge-provider gemini` - RECOMMENDED):** Requires `GEMINI_API_KEY` configured in environment or `app/backend/.env`. Zero disk footprint, fast 1-2s latency, and strict Pydantic JSON schema support.
- **Local Live Lane (`--llm-judge-provider local`):** Connects to local Ollama/vLLM instance via `OLLAMA_BASE_URL` (default: `http://localhost:11434`). Requires 4-8 GB local model download (Not recommended if disk space is low).
- **Other Cloud Live Lane (`--llm-judge-provider cloud`):** Requires `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.

---

## 5. Verification Plan

### Automated Verification
1. **Unit Test Suite:**
   - Run `cd app/backend && pytest tests/evaluation/test_product_chat_adapter.py tests/evaluation/test_llm_judge.py -v`
2. **Deterministic Chat Suite:**
   - Run `cd app/backend && python scripts/run_ai_evaluation.py --suite release --lane deterministic --components chat --output-dir evaluation-artifacts/chat-deterministic`
   - Target: All cases pass, `sse_transport_coverage` passes, zero leakage.
3. **Live Chat Suite with LLM Judge:**
   - Run `cd app/backend && python scripts/run_ai_evaluation.py --suite release --lane live --components chat --retrieval-mode hybrid --output-dir evaluation-artifacts/chat-live`
   - Target: Faithfulness >= 0.90, Relevance >= 0.90, Citation Precision >= 0.85.
