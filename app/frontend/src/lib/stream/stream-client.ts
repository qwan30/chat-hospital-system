export interface StreamCallbacks {
  onChunk: (chunk: string) => void;
  onCitation: (citation: { evidence_id: string; document_title: string; page: number; score: number }) => void;
  onDone: (fullText: string) => void;
  onError: (error: Error) => void;
}

export class StreamClient {
  private abortController: AbortController | null = null;

  async streamChat(
    url: string,
    token: string,
    body: { question: string; patient_id?: string; thread_id?: string },
    callbacks: StreamCallbacks
  ): Promise<void> {
    this.abortController = new AbortController();
    let fullText = "";

    try {
      const response = await fetch(url + "/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
        body: JSON.stringify(body),
        signal: this.abortController.signal,
      });

      if (!response.ok) {
        throw new Error("Stream error: " + response.status);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              callbacks.onDone(fullText);
              return;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.type === "chunk") {
                fullText += parsed.content;
                callbacks.onChunk(parsed.content);
              } else if (parsed.type === "citation") {
                callbacks.onCitation(parsed.citation);
              }
            } catch {
              // skip malformed lines
            }
          }
        }
      }
      callbacks.onDone(fullText);
    } catch (error) {
      if (error instanceof Error && error.name !== "AbortError") {
        callbacks.onError(error);
      }
    }
  }

  abort(): void {
    this.abortController?.abort();
  }
}
