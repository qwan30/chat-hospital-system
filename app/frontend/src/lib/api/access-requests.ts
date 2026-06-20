import { apiFetch } from "../api-client";

export interface AccessRequestCreate {
  patient_id: string;
  justification: string;
}

export interface AccessRequestResponse {
  id: string;
  message: string;
  patient_id: string;
  status: string;
}

export interface AccessRequestListItem {
  id: string;
  patient_id: string;
  patient_name: string;
  patient_mrn: string;
  requester_id: string;
  requester_name: string;
  requester_role: string;
  status: string;
  justification: string;
  created_at: string;
}

export interface AccessRequestDetail extends AccessRequestListItem {
  reviewed_by_name: string | null;
  reviewed_at: string | null;
  review_notes: string | null;
}

export interface AccessRequestReview {
  status: "approved" | "denied" | "pending_info";
  notes?: string;
}

export const createAccessRequest = async (
  payload: AccessRequestCreate,
): Promise<AccessRequestResponse> => {
  return apiFetch<AccessRequestResponse>("/access-requests", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const listAccessRequests = async (): Promise<AccessRequestListItem[]> => {
  return apiFetch<AccessRequestListItem[]>("/access-requests");
};

export const getAccessRequest = async (id: string): Promise<AccessRequestDetail> => {
  return apiFetch<AccessRequestDetail>(`/access-requests/${id}`);
};

export const reviewAccessRequest = async (
  id: string,
  payload: AccessRequestReview,
): Promise<AccessRequestResponse> => {
  return apiFetch<AccessRequestResponse>(`/access-requests/${id}/review`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
};
