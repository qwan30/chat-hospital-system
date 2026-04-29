/**
 * Unit tests for the SSE streaming chat client.
 *
 * Verifies:
 * - SSE line parsing dispatches to the correct callbacks
 * - Error responses throw and call onError
 * - AbortController cancellation surfaces as AbortError
 * - Malformed JSON lines are silently skipped
 */

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { streamChat, type StreamCitationItem, type StreamMetadataEvent } from "@/lib/chat-assistant/stream-client";

// ── Helpers ────────────────────────────────────────────────────────────

/** Build a fake ReadableStream from SSE lines. */
function makeSseStream(lines: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  const combined = lines.map((l) => l + "\n").join("");
  return new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode(combined));
      controller.close();
    },
  });
}

/** Build a Response object with a given SSE body. */
function fakeResponse(sseLines: string[], status = 200): Response {
  return new Response(makeSseStream(sseLines), {
    status,
    statusText: status === 200 ? "OK" : "Internal Server Error",
    headers: { "Content-Type": "text/event-stream" },
  });
}

// ── Tests ──────────────────────────────────────────────────────────────

describe("streamChat", () => {
  let fetchSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchSpy = vi.spyOn(globalThis, "fetch");
  });

  afterEach(() => {
    fetchSpy.mockRestore();
  });

  it("dispatches token events to onToken callback", async () => {
    const tokens: string[] = [];

    fetchSpy.mockResolvedValueOnce(
      fakeResponse([
        'data: {"type":"token","content":"Hello"}',
        'data: {"type":"token","content":" world"}',
        'data: {"type":"done","query_id":"q1"}',
      ]),
    );

    const result = await streamChat({
      baseUrl: "http://test",
      patientId: "p1",
      question: "test?",
      onToken: (t) => tokens.push(t),
    });

    expect(tokens).toEqual(["Hello", " world"]);
    expect(result).toBe("Hello world");
  });

  it("dispatches citation events to onCitations callback", async () => {
    let receivedCitations: StreamCitationItem[] = [];

    const citations: StreamCitationItem[] = [
      {
        evidence_id: "E1",
        document_id: "d1",
        document_title: "Test Doc",
        page: 1,
        score: 0.9,
        content: "Some evidence",
      },
    ];

    fetchSpy.mockResolvedValueOnce(
      fakeResponse([
        `data: {"type":"citations","data":${JSON.stringify(citations)}}`,
        'data: {"type":"done","query_id":"q1"}',
      ]),
    );

    await streamChat({
      baseUrl: "http://test",
      patientId: "p1",
      question: "test?",
      onCitations: (c) => {
        receivedCitations = c;
      },
    });

    expect(receivedCitations).toHaveLength(1);
    expect(receivedCitations[0].evidence_id).toBe("E1");
    expect(receivedCitations[0].document_title).toBe("Test Doc");
    expect(receivedCitations[0].score).toBe(0.9);
  });

  it("dispatches metadata events to onMetadata callback", async () => {
    let receivedMeta: StreamMetadataEvent | null = null;

    fetchSpy.mockResolvedValueOnce(
      fakeResponse([
        'data: {"type":"metadata","confidence":"high","pipeline":"simple_qa","model":"gpt-4o"}',
        'data: {"type":"done","query_id":"q1"}',
      ]),
    );

    await streamChat({
      baseUrl: "http://test",
      patientId: "p1",
      question: "test?",
      onMetadata: (m) => {
        receivedMeta = m;
      },
    });

    expect(receivedMeta).not.toBeNull();
    expect(receivedMeta!.confidence).toBe("high");
    expect(receivedMeta!.pipeline).toBe("simple_qa");
    expect(receivedMeta!.model).toBe("gpt-4o");
  });

  it("dispatches done event to onDone callback", async () => {
    let doneQueryId = "";

    fetchSpy.mockResolvedValueOnce(
      fakeResponse([
        'data: {"type":"done","query_id":"abc-123"}',
      ]),
    );

    await streamChat({
      baseUrl: "http://test",
      patientId: "p1",
      question: "test?",
      onDone: (qid) => {
        doneQueryId = qid;
      },
    });

    expect(doneQueryId).toBe("abc-123");
  });

  it("calls onError for error events in the stream", async () => {
    let errorMsg = "";

    fetchSpy.mockResolvedValueOnce(
      fakeResponse([
        'data: {"type":"error","message":"Something went wrong"}',
      ]),
    );

    await streamChat({
      baseUrl: "http://test",
      patientId: "p1",
      question: "test?",
      onError: (msg) => {
        errorMsg = msg;
      },
    });

    expect(errorMsg).toBe("Something went wrong");
  });

  it("throws and calls onError on non-200 HTTP responses", async () => {
    let errorMsg = "";

    fetchSpy.mockResolvedValueOnce(
      new Response("Server error", { status: 500, statusText: "Internal Server Error" }),
    );

    await expect(
      streamChat({
        baseUrl: "http://test",
        patientId: "p1",
        question: "test?",
        onError: (msg) => {
          errorMsg = msg;
        },
      }),
    ).rejects.toThrow("Streaming request failed: 500");

    expect(errorMsg).toContain("500");
  });

  it("silently skips malformed JSON lines", async () => {
    const tokens: string[] = [];

    fetchSpy.mockResolvedValueOnce(
      fakeResponse([
        'data: {"type":"token","content":"good"}',
        "data: {invalid-json",
        "data: ",
        'data: {"type":"token","content":"also-good"}',
        'data: {"type":"done","query_id":"q1"}',
      ]),
    );

    await streamChat({
      baseUrl: "http://test",
      patientId: "p1",
      question: "test?",
      onToken: (t) => tokens.push(t),
    });

    expect(tokens).toEqual(["good", "also-good"]);
  });

  it("ignores non-data lines (comments, empty lines)", async () => {
    const tokens: string[] = [];

    fetchSpy.mockResolvedValueOnce(
      fakeResponse([
        ": this is a comment",
        "",
        'data: {"type":"token","content":"valid"}',
        "event: heartbeat",
        'data: {"type":"done","query_id":"q1"}',
      ]),
    );

    await streamChat({
      baseUrl: "http://test",
      patientId: "p1",
      question: "test?",
      onToken: (t) => tokens.push(t),
    });

    expect(tokens).toEqual(["valid"]);
  });

  it("sends correct auth header and request body", async () => {
    fetchSpy.mockResolvedValueOnce(
      fakeResponse(['data: {"type":"done","query_id":"q1"}']),
    );

    await streamChat({
      baseUrl: "http://test",
      token: "my-secret-token",
      patientId: "patient-123",
      question: "What is the protocol?",
      topK: 10,
      threadId: "thread-abc",
      pipeline: "simple_qa",
    });

    expect(fetchSpy).toHaveBeenCalledWith(
      "http://test/api/v1/chat/stream",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: "Bearer my-secret-token",
          "Content-Type": "application/json",
        }),
      }),
    );

    const callArgs = fetchSpy.mock.calls[0];
    const body = JSON.parse(callArgs[1]?.body as string);
    expect(body).toEqual({
      patient_id: "patient-123",
      question: "What is the protocol?",
      top_k: 10,
      thread_id: "thread-abc",
      pipeline: "simple_qa",
    });
  });

  it("handles AbortController signal", async () => {
    const controller = new AbortController();
    controller.abort(); // Pre-abort

    fetchSpy.mockRejectedValueOnce(new DOMException("Aborted", "AbortError"));

    await expect(
      streamChat({
        baseUrl: "http://test",
        patientId: "p1",
        question: "test?",
        signal: controller.signal,
      }),
    ).rejects.toThrow();
  });

  it("handles multi-chunk streaming (split across reads)", async () => {
    const tokens: string[] = [];
    const encoder = new TextEncoder();

    // Simulate data arriving in two separate chunks, splitting a line
    const chunk1 = 'data: {"type":"token","content":"first"}\ndata: {"typ';
    const chunk2 = 'e":"token","content":"second"}\ndata: {"type":"done","query_id":"q1"}\n';

    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode(chunk1));
        controller.enqueue(encoder.encode(chunk2));
        controller.close();
      },
    });

    fetchSpy.mockResolvedValueOnce(
      new Response(stream, {
        status: 200,
        headers: { "Content-Type": "text/event-stream" },
      }),
    );

    const result = await streamChat({
      baseUrl: "http://test",
      patientId: "p1",
      question: "test?",
      onToken: (t) => tokens.push(t),
    });

    expect(tokens).toEqual(["first", "second"]);
    expect(result).toBe("firstsecond");
  });
});
