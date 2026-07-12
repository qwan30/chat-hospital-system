/**
 * SSE streaming client for the chat endpoint.
 *
 * Backend endpoint: POST /api/v1/chat/stream
 * SSE events:
 *   data: {"type":"token","content":"..."}
 *   data: {"type":"citations","data":[...]}
 *   data: {"type":"metadata","confidence":"...","pipeline":"...","model":"..."}
 *   data: {"type":"done","query_id":"...","validation":"passed|failed"}
 *   data: {"type":"error","message":"..."}
 */

export interface StreamCitation {
  evidence_id: string;
  document_id: string;
  document_title: string;
  page: number;
  score: number;
  content?: string;
}

export interface StreamResult {
  answer: string;
  citations: StreamCitation[];
  confidence: string;
  queryId: string;
  validation: string;
  model?: string;
  error?: string;
}

export type StreamCallback = (event: {
  type: "token" | "citations" | "metadata" | "done" | "error";
  content?: string;
  citations?: StreamCitation[];
  confidence?: string;
  queryId?: string;
  validation?: string;
  model?: string;
  message?: string;
}) => void;

export async function streamChat(
  apiUrl: string,
  token: string | null,
  body: {
    message?: string;
    question?: string; // legacy support
    context?: {
      patient_id?: string;
      document_ids?: string[];
    };
    patient_id?: string;
    thread_id?: string;
    top_k?: number;
    pipeline?: string;
    mode?: string;
    simulate?: string;
  },
  onEvent?: StreamCallback,
  abortSignal?: AbortSignal,
): Promise<StreamResult> {
  const base = apiUrl.replace(/\/+$/, "");
  const url = `${base}/chat/stream`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const internalController = new AbortController();
  const onExternalAbort = () => internalController.abort();
  if (abortSignal) {
    abortSignal.addEventListener("abort", onExternalAbort);
  }

  let watchdogTimer: ReturnType<typeof setTimeout>;
  let timeoutTriggered = false;

  const resetWatchdog = () => {
    if (watchdogTimer) clearTimeout(watchdogTimer);
    watchdogTimer = setTimeout(() => {
      timeoutTriggered = true;
      internalController.abort();
      onEvent?.({ type: "error", message: "Stream timed out after 30s of inactivity." });
    }, 30000);
  };

  try {
    resetWatchdog();
    const response = await fetch(url, {
      method: "POST",
      headers,
      signal: internalController.signal,
      body: JSON.stringify({
        message: body.message || body.question,
        context: body.context || undefined,
        patient_id: body.patient_id || undefined,
        thread_id: body.thread_id || undefined,
        top_k: body.top_k ?? 5,
        pipeline: body.pipeline || "default",
        mode: body.mode || undefined,
        simulate: body.simulate || undefined,
      }),
    });

    if (!response.ok) {
      const errText = await response.text().catch(() => "Unknown error");
      throw new Error(`Chat stream failed: ${response.status} ${errText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    let buffer = "";
    const result: StreamResult = {
      answer: "",
      citations: [],
      confidence: "low",
      queryId: "",
      validation: "unknown",
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      resetWatchdog();

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const jsonStr = line.slice(6).trim();
        if (!jsonStr) continue;

        try {
          const data = JSON.parse(jsonStr);
          switch (data.type) {
            case "token":
              result.answer += data.content || "";
              onEvent?.({ type: "token", content: data.content });
              break;
            case "citations":
              result.citations = data.data || [];
              onEvent?.({ type: "citations", citations: data.data });
              break;
            case "metadata":
              result.confidence = data.confidence || "low";
              result.model = data.model;
              onEvent?.({ type: "metadata", confidence: data.confidence, model: data.model });
              break;
            case "done":
              result.queryId = data.query_id || "";
              result.validation = data.validation || "unknown";
              onEvent?.({ type: "done", queryId: data.query_id, validation: data.validation });
              break;
            case "error":
              result.error = data.message;
              onEvent?.({ type: "error", message: data.message });
              break;
          }
        } catch {
          // skip unparseable lines
        }
      }
    }

    return result;
  } catch (error) {
    if (timeoutTriggered) {
      throw new Error("Stream timeout");
    }
    throw error;
  } finally {
    if (watchdogTimer) clearTimeout(watchdogTimer);
    if (abortSignal) {
      abortSignal.removeEventListener("abort", onExternalAbort);
    }
  }
}
