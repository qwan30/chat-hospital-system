import { apiFetch } from "@/lib/api-client";
export interface EvidenceRead {
  id: string;
  document_id: string;
  source: string;
  snippet: string;
  relevance: number;
}

export interface ChatThreadRead {
  id: string;
  scope: "general" | "patient-linked";
  patient_id?: string | null;
  title: string;
  visibility: "private" | "shared";
  status: "active" | "archived";
  owner_user_id: string;
  created_trace_id: string;
  last_message_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageRead {
  id: string;
  thread_id: string;
  scope: "general" | "patient-linked";
  patient_id?: string | null;
  role: "user" | "assistant" | "system";
  content: string;
  patient_permission_state: "not-required" | "pending" | "allowed" | "denied";
  citations: EvidenceRead[];
  meta: Record<string, unknown>;
  sender_user_id?: string | null;
  ai_query_id?: string | null;
  trace_id: string;
  created_at: string;
}

export interface ChatThreadDetail extends ChatThreadRead {
  messages: ChatMessageRead[];
}

export interface ChatThreadListResponse {
  items: ChatThreadRead[];
}

export async function listChatThreads(): Promise<ChatThreadRead[]> {
  const res = await apiFetch<ChatThreadListResponse>("/chat-threads", { method: "GET" });
  return res.items;
}

export async function createChatThread(payload: {
  scope: "general" | "patient-linked";
  patient_id?: string | null;
  title: string;
  visibility?: "private" | "shared";
}): Promise<ChatThreadRead> {
  return apiFetch<ChatThreadRead>("/chat-threads", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getChatThread(threadId: string): Promise<ChatThreadDetail> {
  return apiFetch<ChatThreadDetail>(`/chat-threads/${threadId}`, { method: "GET" });
}

export async function listThreadMessages(threadId: string): Promise<ChatMessageRead[]> {
  const res = await apiFetch<{ items: ChatMessageRead[] }>(`/chat-threads/${threadId}/messages`, {
    method: "GET",
  });
  return res.items;
}
