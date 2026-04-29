/**
 * SSE streaming client for chat completions.
 *
 * Uses the fetch ReadableStream API (not legacy EventSource) for better
 * control over request headers (auth tokens) and POST body support.
 */

export type StreamEventType = "token" | "citations" | "metadata" | "done" | "error";

export interface StreamTokenEvent {
  type: "token";
  content: string;
}

export interface StreamCitationItem {
  evidence_id: string;
  document_id: string;
  document_title: string;
  page: number;
  score: number;
  content: string;
}

export interface StreamCitationsEvent {
  type: "citations";
  data: StreamCitationItem[];
}

export interface StreamMetadataEvent {
  type: "metadata";
  confidence: string;
  pipeline: string;
  model: string;
}

export interface StreamDoneEvent {
  type: "done";
  query_id: string;
}

export interface StreamErrorEvent {
  type: "error";
  message: string;
}

export type StreamEvent =
  | StreamTokenEvent
  | StreamCitationsEvent
  | StreamMetadataEvent
  | StreamDoneEvent
  | StreamErrorEvent;

export interface StreamChatOptions {
  baseUrl?: string;
  token?: string;
  patientId: string;
  question: string;
  topK?: number;
  threadId?: string;
  pipeline?: string;
  onToken?: (content: string) => void;
  onCitations?: (citations: StreamCitationItem[]) => void;
  onMetadata?: (meta: StreamMetadataEvent) => void;
  onDone?: (queryId: string) => void;
  onError?: (message: string) => void;
  signal?: AbortSignal;
}

/**
 * Stream chat response via SSE from the backend.
 *
 * Returns the full accumulated response text.
 */
export async function streamChat(options: StreamChatOptions): Promise<string> {
  const {
    baseUrl = "",
    token,
    patientId,
    question,
    topK = 5,
    threadId,
    pipeline = "auto",
    onToken,
    onCitations,
    onMetadata,
    onDone,
    onError,
    signal,
  } = options;

  const url = `${baseUrl.replace(/\/$/, "")}/api/v1/chat/stream`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const body = JSON.stringify({
    patient_id: patientId,
    question,
    top_k: topK,
    thread_id: threadId || undefined,
    pipeline,
  });

  const response = await fetch(url, {
    method: "POST",
    headers,
    body,
    signal,
  });

  if (!response.ok) {
    const errorMsg = `Streaming request failed: ${response.status} ${response.statusText}`;
    onError?.(errorMsg);
    throw new Error(errorMsg);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Response body is not readable");
  }

  const decoder = new TextDecoder();
  let fullText = "";
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE lines
      const lines = buffer.split("\n");
      buffer = lines.pop() || ""; // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;

        const jsonStr = line.slice(6).trim();
        if (!jsonStr) continue;

        try {
          const event: StreamEvent = JSON.parse(jsonStr);

          switch (event.type) {
            case "token":
              fullText += event.content;
              onToken?.(event.content);
              break;
            case "citations":
              onCitations?.(event.data);
              break;
            case "metadata":
              onMetadata?.(event);
              break;
            case "done":
              onDone?.(event.query_id);
              break;
            case "error":
              onError?.(event.message);
              break;
          }
        } catch {
          // Skip malformed JSON lines
          continue;
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  return fullText;
}
