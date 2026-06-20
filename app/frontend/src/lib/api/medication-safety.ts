import { apiFetch } from "../api-client";

export interface DrugConflict {
  id: string;
  patient: string;
  patientId: string;
  drug: string;
  conflictsWith: string;
  type: "allergy" | "interaction" | "renal" | "duplicate" | string;
  severity: "low" | "moderate" | "high" | "critical" | string;
  rule: string;
  source: string;
  recommendation: string;
  status: "open" | "ack" | "overridden" | string;
  ts: string;
}

export interface DrugWarning {
  drug_name: string;
  interacting_entity: string;
  interaction_type: string;
  severity: string;
  evidence_chunk_id: string;
  message: string;
}

export const getReviewQueue = async (): Promise<DrugConflict[]> => {
  return apiFetch<DrugConflict[]>("/medication-safety/review-queue");
};

export const getConflict = async (id: string): Promise<DrugConflict> => {
  return apiFetch<DrugConflict>(`/medication-safety/conflicts/${id}`);
};

export const getPatientMedicationReview = async (patientId: string): Promise<DrugWarning[]> => {
  return apiFetch<DrugWarning[]>(`/medication-safety/patients/${patientId}/review`);
};
