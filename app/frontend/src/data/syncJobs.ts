export interface SyncJob {
  id: string;
  source: string;
  scope: string;
  status: "success" | "running" | "failed" | "retrying";
  records: number;
  failed: number;
  durationMs: number;
  ts: string;
}

export const syncJobs: SyncJob[] = [
  { id: "j-001", source: "HMS · Patients", scope: "Cardiology · 4N", status: "success", records: 142, failed: 0, durationMs: 1240, ts: "2026-06-12T16:00:00Z" },
  { id: "j-002", source: "HMS · Encounters", scope: "Last 24h", status: "running", records: 0, failed: 0, durationMs: 0, ts: "2026-06-12T16:08:00Z" },
  { id: "j-003", source: "HMS · Labs", scope: "Last 6h", status: "failed", records: 84, failed: 6, durationMs: 2400, ts: "2026-06-12T15:30:00Z" },
  { id: "j-004", source: "HMS · Medications", scope: "Full", status: "success", records: 4920, failed: 0, durationMs: 12200, ts: "2026-06-12T03:00:00Z" },
  { id: "j-005", source: "HMS · Documents", scope: "Last 12h", status: "retrying", records: 38, failed: 2, durationMs: 5800, ts: "2026-06-12T14:00:00Z" },
];

export interface DlqRecord {
  id: string;
  source: string;
  recordType: string;
  recordId: string;
  error: string;
  attempts: number;
  lastAttempt: string;
}

export const dlqRecords: DlqRecord[] = [
  { id: "dlq-001", source: "HMS · Labs", recordType: "LabResult", recordId: "LR-99281", error: "Missing required field: reference_range", attempts: 3, lastAttempt: "2026-06-12T15:30:00Z" },
  { id: "dlq-002", source: "HMS · Labs", recordType: "LabResult", recordId: "LR-99283", error: "Unknown LOINC code 99999-9", attempts: 3, lastAttempt: "2026-06-12T15:30:00Z" },
  { id: "dlq-003", source: "HMS · Documents", recordType: "Document", recordId: "DOC-44120", error: "Empty document body returned by HMS API", attempts: 2, lastAttempt: "2026-06-12T14:00:00Z" },
  { id: "dlq-004", source: "HMS · Medications", recordType: "MedOrder", recordId: "MO-77019", error: "Patient ID mismatch", attempts: 5, lastAttempt: "2026-06-12T11:14:00Z" },
];

export function getSyncJob(id: string) {
  return syncJobs.find((j) => j.id === id);
}