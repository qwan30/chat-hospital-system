import { describe, expect, it, vi, afterEach } from "vitest";
import { streamChat } from "./stream-client";

/**
 * Build a mock fetch Response object that yields SSE chunks via a
 * ReadableStream.
 */
function mockOkResponse(chunks: string[]) {
  const encoder = new TextEncoder();
  return {
    ok: true,
    status: 200,
    text: vi.fn(),
    body: new ReadableStream({
      start(controller) {
        for (const chunk of chunks) {
          controller.enqueue(encoder.encode(chunk));
        }
        controller.close();
      },
    }),
  };
}

function mockErrorResponse(status: number, text: string) {
  return {
    ok: false,
    status,
    statusText: text,
    text: () => Promise.resolve(text),
    body: null,
  };
}

// ---------------------------------------------------------------------------
// streamChat
// ---------------------------------------------------------------------------
describe("streamChat", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("posts to the exact provided API base and preserves the bearer header", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        mockOkResponse(['data: {"type":"done","query_id":"q1","validation":"passed"}\n']),
      );
    vi.stubGlobal("fetch", fetchMock);

    await streamChat("/api", "token123", { question: "Hi" });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/chat/stream",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Accept: "text/event-stream",
          Authorization: "Bearer token123",
          "Content-Type": "application/json",
        }),
      }),
    );
  });

  it("parses token SSE event and calls onEvent callback", async () => {
    const sse =
      'data: {"type":"token","sequence":1,"validation_mode":"sentence_buffered","content":"Hello"}\n' +
      'data: {"type":"done","query_id":"q1","validation":"passed"}\n';

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockOkResponse([sse])));

    const onEvent = vi.fn();
    const result = await streamChat("http://api", "token123", { question: "Hi" }, onEvent);

    expect(onEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "token",
        content: "Hello",
        sequence: 1,
      }),
    );
    expect(result.answer).toBe("Hello");
  });

  it("accumulates multiple token events into result.answer", async () => {
    const sse =
      'data: {"type":"token","sequence":1,"validation_mode":"sentence_buffered","content":"Hello"}\n' +
      'data: {"type":"token","sequence":2,"validation_mode":"sentence_buffered","content":" world"}\n' +
      'data: {"type":"done","query_id":"q1","validation":"passed"}\n';

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockOkResponse([sse])));

    const result = await streamChat("http://api", "token123", { question: "Hi" });
    expect(result.answer).toBe("Hello world");
  });

  it("handles citations event and stores citations in result", async () => {
    const citations = [
      {
        evidence_id: "e1",
        document_id: "d1",
        document_title: "Clinical Note",
        page: 3,
        score: 0.95,
      },
    ];
    const sse =
      `data: ${JSON.stringify({ type: "citations", data: citations })}\n` +
      'data: {"type":"done","query_id":"q1","validation":"passed"}\n';

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockOkResponse([sse])));

    const onEvent = vi.fn();
    const result = await streamChat("http://api", "token123", { question: "Hi" }, onEvent);

    expect(result.citations).toEqual(citations);
    expect(onEvent).toHaveBeenCalledWith({
      type: "citations",
      citations,
    });
  });

  it("forwards processing status stages without treating them as answer text", async () => {
    const sse =
      'data: {"type":"status","stage":"retrieving"}\n' +
      'data: {"type":"status","stage":"validating_citations"}\n' +
      'data: {"type":"done","query_id":"q1","validation":"passed"}\n';
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockOkResponse([sse])));

    const onEvent = vi.fn();
    const result = await streamChat("http://api", "token123", { question: "Hi" }, onEvent);

    expect(onEvent).toHaveBeenCalledWith({ type: "status", stage: "retrieving" });
    expect(onEvent).toHaveBeenCalledWith({ type: "status", stage: "validating_citations" });
    expect(result.answer).toBe("");
  });

  it("sets error field on error event", async () => {
    const sse =
      'data: {"type":"error","message":"LLM timeout"}\n' +
      'data: {"type":"done","query_id":"q1","validation":"failed"}\n';

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockOkResponse([sse])));

    const onEvent = vi.fn();
    const result = await streamChat("http://api", "token123", { question: "Hi" }, onEvent);

    expect(result.error).toBe("LLM timeout");
    expect(onEvent).toHaveBeenCalledWith({
      type: "error",
      message: "LLM timeout",
    });
  });

  it("stops reading when the caller aborts", async () => {
    const controller = new AbortController();
    controller.abort();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockOkResponse([])));

    await expect(
      streamChat("http://api", "token123", { question: "Hi" }, undefined, controller.signal),
    ).rejects.toMatchObject({
      name: "AbortError",
    });
  });

  it("throws on non-ok HTTP response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(mockErrorResponse(500, "Internal Server Error")),
    );

    await expect(streamChat("http://api", "token123", { question: "Hi" })).rejects.toThrow(
      /Chat stream failed with status: 500/,
    );
  });

  it("rejects out-of-order validated chunks", async () => {
    const sse =
      'data: {"type":"token","sequence":2,"content":"bad","validation_mode":"sentence_buffered"}\n';
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockOkResponse([sse])));
    await expect(streamChat("http://api", null, { question: "test" })).rejects.toThrow(
      "Invalid SSE token sequence",
    );
  });

  it("rejects tokens without sentence_buffered validation mode", async () => {
    const sse =
      'data: {"type":"token","sequence":1,"content":"bad","validation_mode":"unvalidated"}\n';
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockOkResponse([sse])));
    await expect(streamChat("http://api", null, { question: "test" })).rejects.toThrow(
      "Invalid SSE token sequence",
    );
  });

  it("captures graph explanation events", async () => {
    const sse =
      'data: {"type":"graph_explanation","data":{"rationale":"Path from drug to condition","paths":[]}}\n' +
      'data: {"type":"done","query_id":"q1","validation":"passed","persistence_status":"completed"}\n';
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockOkResponse([sse])));
    const onEvent = vi.fn();
    const result = await streamChat("http://api", "token123", { question: "Why?" }, onEvent);
    expect(result.graphExplanation).toEqual({
      rationale: "Path from drug to condition",
      paths: [],
    });
    expect(onEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "graph_explanation",
        graphExplanation: { rationale: "Path from drug to condition", paths: [] },
      }),
    );
  });

  it("distinguishes completed, interrupted, and error states", async () => {
    const sseCompleted = 'data: {"type":"done","query_id":"q1","persistence_status":"completed"}\n';
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockOkResponse([sseCompleted])));
    let result = await streamChat("http://api", "token", { question: "test" });
    expect(result.status).toBe("completed");

    const sseInterrupted =
      'data: {"type":"token","sequence":1,"content":"hello","validation_mode":"sentence_buffered"}\n';
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockOkResponse([sseInterrupted])));
    result = await streamChat("http://api", "token", { question: "test" });
    expect(result.status).toBe("interrupted");
  });
});
