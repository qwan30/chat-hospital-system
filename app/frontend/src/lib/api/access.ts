import { apiFetch, type ApiClientOptions } from "@/lib/api-client";

export interface AccessRequestBody {
  patient_id: string;
  resource: string;
  duration: string;
  urgency: string;
  relationship: string;
  purpose: string;
  justification: string;
}

export interface AccessRequestResponse {
  message: string;
  request_id: string;
  patient_id: string;
  status: string;
  expires_at: string;
}

export function createAccessRequest(opts: ApiClientOptions, body: AccessRequestBody): Promise<AccessRequestResponse> {
  return apiFetch<AccessRequestResponse>("/access-requests", { ...opts, method: "POST", body: JSON.stringify(body) });
}

export function getAccessRequestStatus(opts: ApiClientOptions, requestId: string): Promise<AccessRequestResponse> {
  return apiFetch<AccessRequestResponse>("/access-requests/" + requestId, { ...opts, method: "GET" });
}
