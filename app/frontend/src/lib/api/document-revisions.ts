import { apiFetch } from "../api-client";
import { mutationHeaders } from "../idempotency";

export interface DraftPageWrite {
  text: string;
  parent_revision_id: string;
  edit_reason?: string;
}

export interface DraftPageRead {
  page_revision_id: string;
  lock_version: number;
  page_number: number;
  text: string;
  status: string;
}

export interface RevisionSetRead {
  revision_set_id: string;
  document_id: string;
  revision_number: number;
  status: string;
  created_by_user_id: string;
  created_at: string | null;
  submitted_at: string | null;
  approved_by_user_id: string | null;
  approved_at: string | null;
}

export interface ApproveRevisionRequest {
  demo_mode?: boolean;
}

export interface RejectRevisionRequest {
  reason?: string;
}

export interface RestoreRevisionRequest {
  revision_id: string;
  reason?: string;
}

export interface GenerationAcceptedRead {
  generation_id: string;
  state: string;
}

export async function saveDraftPage(
  documentId: string,
  pageNumber: number,
  payload: DraftPageWrite,
  options: { idempotencyKey: string; lockVersion?: number },
): Promise<DraftPageRead> {
  return apiFetch<DraftPageRead>(`/documents/${documentId}/draft/pages/${pageNumber}`, {
    method: "PATCH",
    headers: mutationHeaders(options),
    body: JSON.stringify(payload),
  });
}

export async function submitDraft(
  documentId: string,
  options: { idempotencyKey: string; lockVersion?: number },
): Promise<RevisionSetRead> {
  return apiFetch<RevisionSetRead>(`/documents/${documentId}/draft/submit`, {
    method: "POST",
    headers: mutationHeaders(options),
  });
}

export async function approveRevisionSet(
  documentId: string,
  revisionSetId: string,
  payload: ApproveRevisionRequest,
  options: { idempotencyKey: string; lockVersion?: number },
): Promise<GenerationAcceptedRead> {
  return apiFetch<GenerationAcceptedRead>(
    `/documents/${documentId}/revision-sets/${revisionSetId}/approve`,
    {
      method: "POST",
      headers: mutationHeaders(options),
      body: JSON.stringify(payload),
    },
  );
}

export async function rejectRevisionSet(
  documentId: string,
  revisionSetId: string,
  payload: RejectRevisionRequest,
  options: { idempotencyKey: string; lockVersion?: number },
): Promise<RevisionSetRead> {
  return apiFetch<RevisionSetRead>(
    `/documents/${documentId}/revision-sets/${revisionSetId}/reject`,
    {
      method: "POST",
      headers: mutationHeaders(options),
      body: JSON.stringify(payload),
    },
  );
}

export async function restoreRevision(
  documentId: string,
  revisionSetId: string,
  payload: RestoreRevisionRequest,
  options: { idempotencyKey: string; lockVersion?: number },
): Promise<DraftPageRead> {
  return apiFetch<DraftPageRead>(
    `/documents/${documentId}/revision-sets/${revisionSetId}/restore`,
    {
      method: "POST",
      headers: mutationHeaders(options),
      body: JSON.stringify(payload),
    },
  );
}

export async function listRevisionSets(documentId: string): Promise<RevisionSetRead[]> {
  return apiFetch<RevisionSetRead[]>(`/documents/${documentId}/revision-sets`);
}
