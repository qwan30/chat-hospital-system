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

  it("parses token SSE event and calls onEvent callback", async () => {
    const sse =
      'data: {"type":"token","content":"Hello"}\n' +
      'data: {"type":"done","query_id":"q1","validation":"passed"}\n';

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockOkResponse([sse])));

    const onEvent = vi.fn();
    const result = await streamChat("http://api", "token123", { question: "Hi" }, onEvent);

    expect(onEvent).toHaveBeenCalledWith({
      type: "token",
      content: "Hello",
    });
    expect(result.answer).toBe("Hello");
  });

  it("accumulates multiple token events into result.answer", async () => {
    const sse =
      'data: {"type":"token","content":"Hello"}\n' +
      'data: {"type":"token","content":" world"}\n' +
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
      /Chat stream failed: 500/,
    );
  });
});
