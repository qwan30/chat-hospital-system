import { apiFetch, apiFetchBlob, getStoredApiUrl, getToken } from "../api-client";
import { mutationHeaders } from "../idempotency";

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
  metadata: Record<string, unknown>;
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

export const retryIndex = async (
  id: string,
  options: { idempotencyKey: string; lockVersion?: number },
): Promise<DocumentRead> => {
  return apiFetch<DocumentRead>(`/documents/${id}/retry-index`, {
    method: "POST",
    headers: mutationHeaders(options),
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
  page_revision_id?: string;
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
  value?: unknown;
  reason: string;
  version?: number;
  fact_type?: string;
  page_revision_id: string;
}

export interface ReviewItemPatchResponse {
  review_item_id: string;
  status: string;
}

export const patchReviewItem = async (
  documentId: string,
  reviewItemId: string,
  payload: ReviewItemPatchRequest,
  options: { idempotencyKey: string; lockVersion?: number },
): Promise<ReviewItemPatchResponse> => {
  return apiFetch<ReviewItemPatchResponse>(
    `/documents/${documentId}/review-items/${reviewItemId}`,
    {
      method: "PATCH",
      headers: mutationHeaders(options),
      body: JSON.stringify(payload),
    },
  );
};

export interface UploadSessionCreate {
  patient_id: string;
  title?: string;
  document_type?: string;
  filename: string;
  expected_size: number;
  expected_sha256: string;
  claimed_mime_type: string;
}

export interface UploadSessionRead {
  document_id: string;
  upload_id: string;
  object_key: string;
  presigned_url: string | null;
  required_headers: Record<string, string>;
  state: string;
}

export interface UploadFinalizeResult {
  id: string;
  document_id: string;
  state: string;
  reason?: string;
}

export const createUploadSession = async (
  payload: UploadSessionCreate,
  options: { idempotencyKey: string; lockVersion?: number },
): Promise<UploadSessionRead> => {
  return apiFetch<UploadSessionRead>("/documents/upload-sessions", {
    method: "POST",
    headers: mutationHeaders(options),
    body: JSON.stringify(payload),
  });
};

export const finalizeUpload = async (
  documentId: string,
  uploadId: string,
  options?: { idempotencyKey?: string },
): Promise<UploadFinalizeResult> => {
  return apiFetch<UploadFinalizeResult>(`/documents/${documentId}/uploads/${uploadId}/finalize`, {
    method: "POST",
    headers: options?.idempotencyKey ? { "Idempotency-Key": options.idempotencyKey } : undefined,
  });
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function localUploadUrl(objectKey: string): string {
  const encodedKey = objectKey.split("/").map(encodeURIComponent).join("/");
  return `${getStoredApiUrl()}/documents/upload-objects/${encodedKey}`;
}

export function putPresignedObject(
  upload: UploadSessionRead & { upload_url?: string }, // Handle both presigned_url and upload_url if there's inconsistency
  file: File,
  onProgress: (percent: number) => void,
): Promise<void> {
  return new Promise((resolve, reject) => {
    if (upload.required_headers?.["If-None-Match"] !== "*") {
      reject(new Error("Upload contract must require If-None-Match: *"));
      return;
    }

    const xhr = new XMLHttpRequest();
    const isLocalUpload = upload.presigned_url?.startsWith("local://") === true;
    const url = isLocalUpload
      ? localUploadUrl(upload.object_key)
      : upload.presigned_url || upload.upload_url;
    if (!url) return reject(new Error("No upload URL provided"));

    xhr.open("PUT", url, true);
    if (isLocalUpload) {
      const token = getToken();
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }
    for (const [name, value] of Object.entries(upload.required_headers || {})) {
      xhr.setRequestHeader(name, value);
    }

    xhr.upload.onprogress = ({ loaded, total }) => {
      if (total > 0) onProgress(Math.round((loaded / total) * 100));
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(
          new ApiError(
            xhr.status,
            xhr.status === 412 ? "Immutable object key already exists" : "Object upload failed",
          ),
        );
      }
    };

    xhr.onerror = () => reject(new ApiError(0, "Object upload failed"));
    xhr.send(file);
  });
}
