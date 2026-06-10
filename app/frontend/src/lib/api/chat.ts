import { apiFetch, type ApiClientOptions, type ChatThread, type ChatMessage } from "@/lib/api-client";

export interface ThreadListResponse {
  items: ChatThread[];
  total: number;
}

export interface SendMessageRequest {
  question: string;
  patient_id?: string;
  thread_id?: string;
}

export function listThreads(opts: ApiClientOptions): Promise<ChatThread[]> {
  return apiFetch<ThreadListResponse>("/chat-threads", { ...opts, method: "GET" })
    .then((d) => d.items);
}

export function getThread(opts: ApiClientOptions, threadId: string): Promise<ChatThread> {
  return apiFetch<ChatThread>("/chat-threads/" + threadId, { ...opts, method: "GET" });
}

export function createThread(opts: ApiClientOptions, body: { title: string; patient_id?: string }): Promise<ChatThread> {
  return apiFetch<ChatThread>("/chat-threads", { ...opts, method: "POST", body: JSON.stringify(body) });
}

export function sendChatMessage(opts: ApiClientOptions, body: SendMessageRequest): Promise<ChatMessage> {
  return apiFetch<ChatMessage>("/chat", { ...opts, method: "POST", body: JSON.stringify(body) });
}

export function getThreadMessages(opts: ApiClientOptions, threadId: string): Promise<ChatMessage[]> {
  return apiFetch<{ items: ChatMessage[] }>("/chat-threads/" + threadId + "/messages", { ...opts, method: "GET" })
    .then((d) => d.items);
}
