import { apiFetch } from "../api-client";

// ── Types matching backend schemas/search.py ─────────────────────────

export interface SearchPatient {
  id: string;
  full_name: string;
  mrn: string;
  dob: string | null;
  department: string | null;
  status: string;
}

export interface SearchDocument {
  id: string;
  title: string;
  document_type: string;
  patient_id: string;
}

export interface SearchThread {
  id: string;
  title: string | null;
  patient_id: string;
}

export interface GlobalSearchResponse {
  patients: SearchPatient[];
  documents: SearchDocument[];
  threads: SearchThread[];
}

// ── API call ─────────────────────────────────────────────────────────

export async function globalSearch(query: string): Promise<GlobalSearchResponse> {
  if (!query || query.trim().length < 2) {
    return { patients: [], documents: [], threads: [] };
  }
  return apiFetch<GlobalSearchResponse>(`/search/global?q=${encodeURIComponent(query.trim())}`);
}
