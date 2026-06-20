import { apiFetch } from "../api-client";

export interface PatientRead {
  id: string;
  mrn: string;
  full_name: string;
  dob: string | null;
  department: string | null;
  status: string;
}

export interface PatientSearchResponse {
  items: PatientRead[];
}

export interface PatientOverviewResponse {
  patient_id: string;
  full_name: string;
  mrn: string;
  dob: string | null;
  gender: string | null;
  cccd: string | null;
  blood_type: string | null;
  occupation: string | null;
  allergy_count: number;
  medication_count: number;
  lab_count: number;
  appointment_count: number;
  ai_summary: string | null;
  last_updated: string | null;
}

export interface PatientTimelineEvent {
  event_id: string;
  event_type: string;
  title: string;
  description: string | null;
  timestamp: string;
}

export interface PatientTimelineResponse {
  patient_id: string;
  events: PatientTimelineEvent[];
}

export async function searchPatients(
  query?: string,
  limit: number = 20,
): Promise<PatientSearchResponse> {
  const params = new URLSearchParams();
  if (query) params.append("q", query);
  params.append("limit", limit.toString());
  return apiFetch<PatientSearchResponse>(`/patients/search?${params.toString()}`);
}

export async function getPatient(patientId: string): Promise<PatientRead> {
  return apiFetch<PatientRead>(`/patients/${patientId}`);
}

export async function getPatientOverview(patientId: string): Promise<PatientOverviewResponse> {
  return apiFetch<PatientOverviewResponse>(`/patients/${patientId}/overview`);
}

export async function getPatientTimeline(patientId: string): Promise<PatientTimelineResponse> {
  return apiFetch<PatientTimelineResponse>(`/patients/${patientId}/timeline`);
}

export async function createPatient(patientData: Partial<PatientRead>): Promise<PatientRead> {
  return apiFetch<PatientRead>("/patients", {
    method: "POST",
    body: JSON.stringify(patientData),
  });
}

// ── Medications ────────────────────────────────────────────────────

export interface PatientMedicationItem {
  drug_name: string;
  dose?: string | null;
  route?: string | null;
  frequency?: string | null;
  started?: string | null;
  prescriber?: string | null;
  source_document_id?: string | null;
  source_document_title?: string | null;
}

export interface PatientMedicationResponse {
  patient_id: string;
  medications: PatientMedicationItem[];
}

export async function getPatientMedications(patientId: string): Promise<PatientMedicationResponse> {
  return apiFetch<PatientMedicationResponse>(`/patients/${patientId}/medications`);
}

// ── Labs ────────────────────────────────────────────────────────────

export interface PatientLabItem {
  analyte: string;
  value?: string | null;
  reference_range?: string | null;
  flag?: string | null;
  collected?: string | null;
  source_document_id?: string | null;
  source_document_title?: string | null;
}

export interface PatientLabResponse {
  patient_id: string;
  labs: PatientLabItem[];
}

export async function getPatientLabs(patientId: string): Promise<PatientLabResponse> {
  return apiFetch<PatientLabResponse>(`/patients/${patientId}/labs`);
}

// ── Documents ───────────────────────────────────────────────────────

export interface DocumentRead {
  id: string;
  patient_id: string;
  uploaded_by: string;
  title: string;
  document_type: string;
  storage_uri: string;
  mime_type: string;
  status: string;
  page_count?: number | null;
  ocr_error?: string | null;
  created_at: string;
}

export async function getPatientDocuments(patientId: string): Promise<DocumentRead[]> {
  return apiFetch<DocumentRead[]>(`/patients/${patientId}/documents`);
}
