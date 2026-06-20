import { apiFetch } from "../api-client";

export interface ChatRequest {
  message: string;
  patient_id?: string;
  document_ids?: string[];
  thread_id?: string;
}

export interface ChatResponse {
  answer: string;
  thread_id: string;
  citations: any[];
}

export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
