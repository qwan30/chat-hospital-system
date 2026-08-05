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
  graphExplanation?: unknown;
  status: "completed" | "interrupted" | "error";
}

export type StreamStatusStage =
  | "retrieving"
  | "preparing_answer"
  | "validating_citations"
  | "complete";

export type StreamCallback = (event: {
  type: "token" | "citations" | "metadata" | "status" | "done" | "error" | "graph_explanation";
  sequence?: number;
  content?: string;
  citations?: StreamCitation[];
  confidence?: string;
  queryId?: string;
  validation?: string;
  model?: string;
  message?: string;
  stage?: StreamStatusStage;
  graphExplanation?: unknown;
  status?: "completed" | "interrupted" | "error";
}) => void;

/**
 * Map p-001..p-012 shorthand slugs to their backend UUIDs.
 * Mirrors the same mapping used in apiFetch() (api-client.ts).
 */
function mapSlugToUuid(value: string | undefined): string | undefined {
  if (!value) return value;
  return value.replace(/\b(p-0(0[1-9]|1[0-2]))\b/g, (match) => {
    const num = parseInt(match.substring(2), 10);
    return "20000000-0000-0000-0000-" + num.toString().padStart(12, "0");
  });
}

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

  // Resolve any p-001..p-012 slugs to backend UUIDs (same as apiFetch does)
  const resolvedPatientId = mapSlugToUuid(body.patient_id);
  const resolvedContextPatientId = mapSlugToUuid(body.context?.patient_id);

  // Build the resolved context object
  const resolvedContext = body.context
    ? { ...body.context, patient_id: resolvedContextPatientId }
    : undefined;

  const internalController = new AbortController();
  const onExternalAbort = () => internalController.abort();
  if (abortSignal) {
    abortSignal.addEventListener("abort", onExternalAbort);
  }

  let watchdogTimer: ReturnType<typeof setTimeout> | undefined;
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
        context: resolvedContext,
        patient_id: resolvedPatientId || undefined,
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
    let lastSequence = 0;
    const result: StreamResult = {
      answer: "",
      citations: [],
      confidence: "low",
      queryId: "",
      validation: "unknown",
      status: "interrupted",
    };

    while (true) {
      if (abortSignal?.aborted) {
        throw new DOMException("The user aborted a request.", "AbortError");
      }
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

        let data: { [key: string]: unknown };
        try {
          data = JSON.parse(jsonStr);
        } catch {
          continue;
        }

        if (typeof data !== "object" || data === null) continue;

        switch (data.type) {
          case "token": {
            const seq = Number(data.sequence);
            if (data.validation_mode !== "sentence_buffered" || seq !== lastSequence + 1) {
              throw new Error("Invalid SSE token sequence");
            }
            lastSequence = seq;
            const contentStr = typeof data.content === "string" ? data.content : "";
            result.answer += contentStr;
            onEvent?.({ type: "token", sequence: seq, content: contentStr });
            break;
          }
          case "citations": {
            const citationsList = Array.isArray(data.data) ? (data.data as StreamCitation[]) : [];
            result.citations = citationsList;
            onEvent?.({ type: "citations", citations: citationsList });
            break;
          }
          case "metadata": {
            const conf = typeof data.confidence === "string" ? data.confidence : "low";
            const mod = typeof data.model === "string" ? data.model : undefined;
            result.confidence = conf;
            result.model = mod;
            onEvent?.({ type: "metadata", confidence: conf, model: mod });
            break;
          }
          case "status": {
            onEvent?.({ type: "status", stage: data.stage as StreamStatusStage });
            break;
          }
          case "graph_explanation": {
            result.graphExplanation = data.data;
            onEvent?.({ type: "graph_explanation", graphExplanation: data.data });
            break;
          }
          case "done": {
            result.queryId = typeof data.query_id === "string" ? data.query_id : "";
            result.validation = typeof data.validation === "string" ? data.validation : "unknown";
            const permStatus =
              typeof data.persistence_status === "string"
                ? (data.persistence_status as "completed" | "interrupted" | "error")
                : "completed";
            result.status = permStatus;
            onEvent?.({
              type: "done",
              queryId: result.queryId,
              validation: result.validation,
              status: result.status,
            });
            break;
          }
          case "error": {
            const msg = typeof data.message === "string" ? data.message : "Stream error";
            result.error = msg;
            result.status = "error";
            onEvent?.({ type: "error", message: msg });
            break;
          }
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
