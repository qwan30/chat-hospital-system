import { apiFetch, type ApiClientOptions, type DocumentItem, type ListEnvelope } from "@/lib/api-client";

export interface DocumentUploadResponse {
  id: string;
  status: string;
  message: string;
}

export interface OCRStatusResponse {
  document_id: string;
  status: string;
  ocr_confidence: number;
  page_count: number;
  sections: { text: string; confidence: number }[];
}

export interface SemanticSearchResponse {
  query: string;
  results: { document_id: string; document_title: string; chunk: string; score: number }[];
}

export function listDocuments(opts: ApiClientOptions, params?: Record<string, string>): Promise<DocumentItem[]> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return apiFetch<ListEnvelope<DocumentItem>>("/documents" + qs, { ...opts, method: "GET" }).then((d) => d.items);
}

export function getDocument(opts: ApiClientOptions, docId: string): Promise<DocumentItem> {
  return apiFetch<DocumentItem>("/documents/" + docId, { ...opts, method: "GET" });
}

export function uploadDocument(opts: ApiClientOptions, formData: FormData): Promise<DocumentUploadResponse> {
  return apiFetch<DocumentUploadResponse>("/documents", { ...opts, method: "POST", body: formData, headers: {} });
}

export function getOCRStatus(opts: ApiClientOptions, docId: string): Promise<OCRStatusResponse> {
  return apiFetch<OCRStatusResponse>("/documents/" + docId + "/ocr-status", { ...opts, method: "GET" });
}

export function semanticSearch(opts: ApiClientOptions, query: string): Promise<SemanticSearchResponse> {
  return apiFetch<SemanticSearchResponse>("/documents/search/semantic?q=" + encodeURIComponent(query), { ...opts, method: "GET" });
}
