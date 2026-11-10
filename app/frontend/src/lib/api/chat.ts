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
  const payload = {
    question: request.message,
    patient_id: request.patient_id,
    thread_id: request.thread_id,
    ...(request.document_ids
      ? { context: { patient_id: request.patient_id, document_ids: request.document_ids } }
      : {}),
  };
  return apiFetch<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
