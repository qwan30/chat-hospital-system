import { apiFetch, apiFetchBlob } from "../api-client";

export interface DocumentRead {
  id: string;
  patient_id: string;
  uploaded_by: string;
  title: string;
  document_type: string;
  storage_uri: string;
  mime_type: string;
  status: string;
  page_count: number | null;
  ocr_error: string | null;
  created_at: string;
}

export interface DocumentListResponse {
  items: DocumentRead[];
}

export interface DocumentProcessingEventRead {
  id: string;
  attempt: number;
  sequence: number;
  stage: "upload" | "ocr" | "index" | "ready";
  state: "started" | "completed" | "failed";
  progress_current: number | null;
  progress_total: number | null;
  error_code: "OCR_FAILED" | "INDEX_FAILED" | null;
  created_at: string;
}

export interface DocumentDetailRead extends DocumentRead {
  processing_events: DocumentProcessingEventRead[];
}

export interface DocumentPageRead {
  id: string;
  document_id: string;
  page_number: number;
  ocr_text: string;
  ocr_confidence: number | null;
}

export interface DocumentSearchRequest {
  patient_id: string;
  query: string;
  top_k?: number;
}

export interface EvidenceRead {
  evidence_id: string;
  document_id: string;
  document_title: string;
  page: number;
  chunk_id: string;
  score: number;
  content: string | null;
  metadata: Record<string, any>;
}

export interface DocumentSearchResponse {
  items: EvidenceRead[];
}

export const listDocuments = async (params?: {
  patient_id?: string;
  status?: string;
  limit?: number;
}): Promise<DocumentListResponse> => {
  const queryParams = new URLSearchParams();
  if (params?.patient_id) queryParams.append("patient_id", params.patient_id);
  if (params?.status) queryParams.append("status", params.status);
  if (params?.limit) queryParams.append("limit", params.limit.toString());

  const queryString = queryParams.toString();
  const path = queryString ? `/documents?${queryString}` : "/documents";

  return apiFetch<DocumentListResponse>(path);
};

export const getDocument = async (id: string): Promise<DocumentDetailRead> => {
  return apiFetch<DocumentDetailRead>(`/documents/${id}`);
};

export const getDocumentBlob = async (id: string): Promise<Blob> => {
  return apiFetchBlob(`/documents/${id}/content`);
};

export const getDocumentPage = async (
  documentId: string,
  pageNumber: number,
): Promise<DocumentPageRead> => {
  return apiFetch<DocumentPageRead>(`/documents/${documentId}/pages/${pageNumber}`);
};

export const retryIndex = async (id: string): Promise<DocumentRead> => {
  return apiFetch<DocumentRead>(`/documents/${id}/retry-index`, {
    method: "POST",
  });
};

export const searchDocuments = async (
  payload: DocumentSearchRequest,
): Promise<DocumentSearchResponse> => {
  return apiFetch<DocumentSearchResponse>("/documents/search", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const uploadDocument = async (
  patientId: string,
  title: string,
  documentType: string,
  file: File,
): Promise<DocumentRead> => {
  const formData = new FormData();
  formData.append("patient_id", patientId);
  formData.append("title", title);
  formData.append("document_type", documentType);
  formData.append("file", file);

  return apiFetch<DocumentRead>("/documents", {
    method: "POST",
    body: formData,
  });
};
