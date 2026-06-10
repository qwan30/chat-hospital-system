import { apiFetch, type ApiClientOptions, type Patient, type PatientOverview } from "@/lib/api-client";

export interface PatientSearchParams {
  q?: string;
  department?: string;
  status?: string;
  page?: number;
  limit?: number;
}

export interface PatientListResponse {
  items: Patient[];
  total: number;
}

export interface AISummaryResponse {
  patient_id: string;
  summary: string;
  sections: SummarySection[];
  citations: SummaryCitation[];
  confidence: string;
  generated_at: string;
}

export interface SummarySection {
  title: string;
  content: string;
  citations: number[];
}

export interface SummaryCitation {
  id: number;
  document_title: string;
  page: number;
  content_snippet: string;
  confidence: number;
}

export interface MedicationReviewResponse {
  patient_id: string;
  medications: ReviewedMedication[];
  allergies: AllergyAlert[];
  recommendations: string[];
  citations: SummaryCitation[];
  confidence: string;
}

export interface ReviewedMedication {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  route: string;
  indication: string;
  start_date: string;
  status: string;
  citation_id?: number;
  safety_concern?: string;
}

export interface AllergyAlert {
  id: string;
  allergen: string;
  severity: "high" | "medium" | "low";
  reaction: string;
  recorded_date: string;
}

export function searchPatients(
  opts: ApiClientOptions,
  params?: PatientSearchParams
): Promise<PatientListResponse> {
  const qs = params ? "?" + new URLSearchParams(
    Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])
    )
  ).toString() : "";
  return apiFetch<PatientListResponse>("/patients/search" + qs, { ...opts, method: "GET" });
}

export function getPatientOverview(
  opts: ApiClientOptions,
  patientId: string
): Promise<PatientOverview> {
  return apiFetch<PatientOverview>("/patients/" + patientId + "/overview", { ...opts, method: "GET" });
}

export function generateAISummary(
  opts: ApiClientOptions,
  patientId: string
): Promise<AISummaryResponse> {
  return apiFetch<AISummaryResponse>("/patients/" + patientId + "/ai-summary/generate", {
    ...opts,
    method: "POST",
  });
}

export function getMedicationReview(
  opts: ApiClientOptions,
  patientId: string
): Promise<MedicationReviewResponse> {
  return apiFetch<MedicationReviewResponse>("/patients/" + patientId + "/medication-review", {
    ...opts,
    method: "POST",
  });
}
