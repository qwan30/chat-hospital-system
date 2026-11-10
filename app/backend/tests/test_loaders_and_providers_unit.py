"""Unit tests for document loaders, LLM providers, and embedding providers."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

import httpx
import pytest

from hospital_ai.core.errors import ExternalServiceError
from hospital_ai.services.embedding.ollama_provider import OllamaEmbedding
from hospital_ai.services.embedding.openai_provider import OpenAIEmbedding
from hospital_ai.services.llm.base import LLMMessage
from hospital_ai.services.llm.gemini_provider import GeminiLLM
from hospital_ai.services.llm.ollama_provider import OllamaLLM
from hospital_ai.services.llm.openai_provider import OpenAILLM
from hospital_ai.services.loaders.excel_loader import ExcelLoader
from hospital_ai.services.loaders.html_loader import HtmlLoader
from hospital_ai.services.loaders.text_loader import TextLoader

_ORIG_ASYNC_CLIENT_INIT = httpx.AsyncClient.__init__


def _patch_async_client(monkeypatch: pytest.MonkeyPatch, handler: Any) -> None:
    transport = httpx.MockTransport(handler)

    def _custom_init(self: httpx.AsyncClient, *args: Any, **kwargs: Any) -> None:
        kwargs["transport"] = transport
        _ORIG_ASYNC_CLIENT_INIT(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", _custom_init)


def test_text_loader_loads_markdown_and_supported_extensions(tmp_path: Path) -> None:
    loader = TextLoader()
    assert ".md" in loader.supported_extensions()
    assert ".hl7" in loader.supported_extensions()

    md_file = tmp_path / "discharge_note.md"
    md_file.write_text("# Discharge Summary\nPatient stable on Metformin 500mg.", encoding="utf-8")

    pages = loader.load(md_file)
    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Metformin 500mg" in pages[0].text
    assert pages[0].confidence == 1.0


def test_html_loader_strips_scripts_and_handles_errors(tmp_path: Path) -> None:
    loader = HtmlLoader()
    assert ".html" in loader.supported_extensions()

    missing = tmp_path / "missing.html"
    with pytest.raises(ExternalServiceError, match="not found"):
        loader.load(missing)

    empty_html = tmp_path / "empty.html"
    empty_html.write_text("<html><head><script>alert(1)</script></head><body>   </body></html>", encoding="utf-8")
    with pytest.raises(ExternalServiceError, match="no extractable text"):
        loader.load(empty_html)

    valid_html = tmp_path / "report.html"
    valid_html.write_text(
        "<html><head><title>Echo Report</title><style>body{color:red}</style></head>"
        "<body><header>Nav</header><main><p>LVEF is 55%</p></main><script>evil()</script></body></html>",
        encoding="utf-8",
    )
    pages = loader.load(valid_html)
    assert len(pages) == 1
    assert "LVEF is 55%" in pages[0].text
    assert "evil()" not in pages[0].text


def test_excel_loader_extracts_sheets_and_handles_missing_or_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loader = ExcelLoader()
    assert ".xlsx" in loader.supported_extensions()

    with pytest.raises(ExternalServiceError, match="not found"):
        loader.load(tmp_path / "nonexistent.xlsx")

    corrupt_file = tmp_path / "corrupt.xlsx"
    corrupt_file.write_bytes(b"not-a-zip")

    fake_openpyxl = types.ModuleType("openpyxl")

    def _raise_corrupt(*_args: Any, **_kwargs: Any) -> Any:
        raise ValueError("corrupt workbook")

    fake_openpyxl.load_workbook = _raise_corrupt  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "openpyxl", fake_openpyxl)
    with pytest.raises(ExternalServiceError, match="Failed to open Excel file"):
        loader.load(corrupt_file)

    class _FakeWorksheet:
        def __init__(self, rows: list[tuple[Any, ...]]) -> None:
            self._rows = rows

        def iter_rows(self, values_only: bool = True) -> list[tuple[Any, ...]]:
            assert values_only is True
            return self._rows

    class _FakeWorkbook:
        def __init__(self, sheets: dict[str, list[tuple[Any, ...]]]) -> None:
            self._sheets = sheets
            self.sheetnames = list(sheets.keys())
            self.closed = False

        def __getitem__(self, name: str) -> _FakeWorksheet:
            return _FakeWorksheet(self._sheets[name])

        def close(self) -> None:
            self.closed = True

    empty_wb_path = tmp_path / "empty.xlsx"
    empty_wb_path.write_bytes(b"placeholder")
    fake_openpyxl.load_workbook = lambda *_a, **_k: _FakeWorkbook({"Sheet1": [(None, "")]})  # type: ignore[attr-defined]
    with pytest.raises(ExternalServiceError, match="contains no data"):
        loader.load(empty_wb_path)

    valid_wb_path = tmp_path / "labs.xlsx"
    valid_wb_path.write_bytes(b"placeholder")
    fake_openpyxl.load_workbook = lambda *_a, **_k: _FakeWorkbook(  # type: ignore[attr-defined]
        {"Chemistry": [("Test", "Value", "Unit"), ("Potassium", 4.2, "mmol/L")]}
    )

    pages = loader.load(valid_wb_path)
    assert len(pages) == 1
    assert pages[0].metadata == {"sheet_name": "Chemistry"}
    assert "Potassium | 4.2 | mmol/L" in pages[0].text


@pytest.mark.asyncio
async def test_openai_llm_generate_stream_and_error(monkeypatch: pytest.MonkeyPatch) -> None:
    llm = OpenAILLM(api_key="sk-test", base_url="https://api.openai.test/v1", model="gpt-4o-mini")
    assert llm.provider_name() == "openai"
    assert llm.model_name() == "gpt-4o-mini"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("Authorization") == "Bearer sk-test"
        if b'"stream":true' in request.content or b'"stream": true' in request.content:
            sse_body = (
                'data: {"choices":[{"delta":{"content":"Hello "}}]}\n\n'
                "data: {invalid-json}\n\n"
                'data: {"choices":[{"delta":{"content":"world"}}]}\n\n'
                "data: [DONE]\n\n"
            )
            return httpx.Response(200, text=sse_body)
        return httpx.Response(
            200,
            json={
                "model": "gpt-4o-mini",
                "choices": [{"message": {"content": "Clinical answer"}, "finish_reason": "stop"}],
                "usage": {"total_tokens": 12},
            },
        )

    _patch_async_client(monkeypatch, handler)
    messages = [LLMMessage(role="user", content="Check potassium")]
    res = await llm.generate(messages, temperature=0.1, max_tokens=64)
    assert res.text == "Clinical answer"
    assert res.finish_reason == "stop"

    chunks = [chunk async for chunk in llm.stream(messages, temperature=0.1, max_tokens=64)]
    assert "".join(chunks) == "Hello world"

    def err_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    _patch_async_client(monkeypatch, err_handler)
    with pytest.raises(ExternalServiceError, match="OpenAI chat request failed"):
        await llm.generate(messages)
    with pytest.raises(ExternalServiceError, match="OpenAI streaming request failed"):
        _ = [c async for c in llm.stream(messages)]


@pytest.mark.asyncio
async def test_ollama_llm_generate_stream_and_error(monkeypatch: pytest.MonkeyPatch) -> None:
    llm = OllamaLLM(base_url="http://ollama.test:11434", model="qwen2.5:7b")
    assert llm.provider_name() == "ollama"
    assert llm.model_name() == "qwen2.5:7b"

    def handler(request: httpx.Request) -> httpx.Response:
        if b'"stream":true' in request.content or b'"stream": true' in request.content:
            ndjson = (
                "\n"
                "{bad-json}\n"
                '{"message":{"content":"Patient "},"done":false}\n'
                '{"message":{"content":"stable."},"done":true}\n'
            )
            return httpx.Response(200, text=ndjson)
        return httpx.Response(
            200,
            json={"model": "qwen2.5:7b", "message": {"content": "Ollama response"}, "done_reason": "stop"},
        )

    _patch_async_client(monkeypatch, handler)
    messages = [LLMMessage(role="user", content="Status?")]
    res = await llm.generate(messages, temperature=0.0, max_tokens=50)
    assert res.text == "Ollama response"

    streamed = [c async for c in llm.stream(messages, max_tokens=50)]
    assert "".join(streamed) == "Patient stable."

    _patch_async_client(monkeypatch, lambda _r: httpx.Response(200, json={"message": {}}))
    with pytest.raises(ExternalServiceError, match="did not include message content"):
        await llm.generate(messages)

    _patch_async_client(monkeypatch, lambda _r: httpx.Response(503, text="unavailable"))
    with pytest.raises(ExternalServiceError, match="Ollama chat request failed"):
        await llm.generate(messages)
    with pytest.raises(ExternalServiceError, match="Ollama streaming request failed"):
        _ = [c async for c in llm.stream(messages)]


@pytest.mark.asyncio
async def test_gemini_llm_generate_stream_and_error(monkeypatch: pytest.MonkeyPatch) -> None:
    llm = GeminiLLM(api_key="gem-key", model="gemini-2.0-flash")
    assert llm.provider_name() == "gemini"
    assert llm.model_name() == "gemini-2.0-flash"

    def handler(request: httpx.Request) -> httpx.Response:
        if "streamGenerateContent" in str(request.url):
            sse = (
                "event: message\n"
                "data: \n"
                "data: {broken}\n"
                'data: {"candidates":[{"content":{"parts":[{"text":"Normal "}]}}]}\n'
                'data: {"candidates":[{"content":{"parts":[{"text":"sinus rhythm"}]}}]}\n'
            )
            return httpx.Response(200, text=sse)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {"parts": [{"text": "Sinus rhythm"}]},
                    }
                ],
                "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 3, "totalTokenCount": 8},
            },
        )

    _patch_async_client(monkeypatch, handler)
    messages = [
        LLMMessage(role="system", content="You are a clinical assistant."),
        LLMMessage(role="assistant", content="Prior context"),
        LLMMessage(role="user", content="ECG reading?"),
    ]
    res = await llm.generate(messages, temperature=0.2, max_tokens=100)
    assert res.text == "Sinus rhythm"
    assert res.usage["total_tokens"] == 8

    empty_payload = llm._build_payload([LLMMessage(role="system", content="Sys only")], 0.0, None)
    assert empty_payload["contents"][0]["parts"][0]["text"] == "Hello"

    streamed = [c async for c in llm.stream(messages, max_tokens=100)]
    assert "".join(streamed) == "Normal sinus rhythm"

    _patch_async_client(monkeypatch, lambda _r: httpx.Response(429, text="rate limited"))
    with pytest.raises(ExternalServiceError, match="Gemini chat request failed"):
        await llm.generate(messages)
    with pytest.raises(ExternalServiceError, match="Gemini streaming request failed"):
        _ = [c async for c in llm.stream(messages)]


@pytest.mark.asyncio
async def test_openai_and_ollama_embedding_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    oai = OpenAIEmbedding(api_key="sk-emb", base_url="https://api.openai.test/v1", dims=3)
    assert oai.provider_name() == "openai"
    assert oai.model_name() == "text-embedding-3-small"
    assert oai.dimensions() == 3
    assert await oai.embed_many([]) == []

    _patch_async_client(
        monkeypatch,
        lambda _r: httpx.Response(
            200,
            json={
                "data": [
                    {"index": 1, "embedding": [0.4, 0.5, 0.6]},
                    {"index": 0, "embedding": [0.1, 0.2, 0.3]},
                ]
            },
        ),
    )
    vecs = await oai.embed_many(["first", "second"])
    assert vecs == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    _patch_async_client(monkeypatch, lambda _r: httpx.Response(200, json={"data": [{"index": 0, "embedding": [0.1]}]}))
    with pytest.raises(ExternalServiceError, match="returned 1 embeddings for 2 inputs"):
        await oai.embed_many(["a", "b"])

    _patch_async_client(monkeypatch, lambda _r: httpx.Response(500, text="err"))
    with pytest.raises(ExternalServiceError, match="OpenAI embedding request failed"):
        await oai.embed("a")

    ollama = OllamaEmbedding(base_url="http://ollama.test:11434", dims=2)
    assert ollama.provider_name() == "ollama"
    assert ollama.model_name() == "nomic-embed-text"
    assert ollama.dimensions() == 2
    assert await ollama.embed_many([]) == []

    _patch_async_client(monkeypatch, lambda _r: httpx.Response(200, json={"embeddings": [[1, 2]]}))
    assert await ollama.embed("hello") == [1.0, 2.0]

    _patch_async_client(monkeypatch, lambda _r: httpx.Response(200, json={"embeddings": []}))
    with pytest.raises(ExternalServiceError, match="Ollama returned 0 embeddings"):
        await ollama.embed("hello")

    _patch_async_client(monkeypatch, lambda _r: httpx.Response(502, text="bad gateway"))
    with pytest.raises(ExternalServiceError, match="Ollama embedding request failed"):
        await ollama.embed("hello")
