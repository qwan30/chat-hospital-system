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

export interface DocumentIntelligenceResponse {
  document_id: string;
  status: string;
  facts_count: number;
  review_items_count: number;
}

export const getDocumentIntelligence = async (
  documentId: string,
): Promise<DocumentIntelligenceResponse> => {
  return apiFetch<DocumentIntelligenceResponse>(`/documents/${documentId}/intelligence`);
};

export interface ClinicalFactRead {
  id: string;
  fact_type: string;
  raw_value: string;
  normalized_value: string | null;
  confidence: number | null;
  source_page: number | null;
  bounding_box: { top: number; left: number; width: number; height: number } | null;
  status: string;
}

export interface DocumentFactsResponse {
  document_id: string;
  facts: ClinicalFactRead[];
}

export const getDocumentFacts = async (documentId: string): Promise<DocumentFactsResponse> => {
  return apiFetch<DocumentFactsResponse>(`/documents/${documentId}/facts`);
};

export interface ReviewItemRead {
  id: string;
  fact_id: string | null;
  field_name: string;
  original_value: string | null;
  suggested_value: string | null;
  review_status: string;
}

export interface DocumentReviewItemsResponse {
  document_id: string;
  review_items: ReviewItemRead[];
}

export const getDocumentReviewItems = async (
  documentId: string,
): Promise<DocumentReviewItemsResponse> => {
  return apiFetch<DocumentReviewItemsResponse>(`/documents/${documentId}/review-items`);
};

export interface ReviewItemPatchRequest {
  action: "approve" | "reject" | "correct";
  value?: any;
  reason: string;
  version: number;
  fact_type?: string;
}

export interface ReviewItemPatchResponse {
  review_item_id: string;
  status: string;
}

export const patchReviewItem = async (
  documentId: string,
  reviewItemId: string,
  payload: ReviewItemPatchRequest,
): Promise<ReviewItemPatchResponse> => {
  return apiFetch<ReviewItemPatchResponse>(
    `/documents/${documentId}/review-items/${reviewItemId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
};
