export type UUIDString = string;

export type ChatDataStatus = "verified-backend" | "local-sample-only" | "documented-gap";

export type ChatScope = "general-knowledge" | "patient-linked";

export type PatientPermissionState = "not-required" | "pending" | "allowed" | "denied";

export type MessageRole = "assistant" | "staff" | "system";

export type EvidenceAvailability = "available" | "permission-gated" | "unavailable" | "no-evidence";

export type DataProvenance = {
  status: ChatDataStatus;
  visibleLabel: string;
  sourceLabel: string;
  note: string;
};

export type PatientContext = {
  id: string;
  scope: ChatScope;
  patientId: UUIDString | null;
  displayLabel: string;
  permissionState: PatientPermissionState;
  permissionLabel: string;
  provenance: DataProvenance;
};

export type EvidenceSource = {
  id: string;
  documentId: UUIDString | null;
  title: string;
  page: number | null;
  chunkId: UUIDString | null;
  excerpt: string;
  score: number | null;
  availability: EvidenceAvailability;
  metadata: Record<string, unknown>;
  provenance: DataProvenance;
};

export type SourceCitation = {
  id: string;
  label: string;
  evidenceSourceId: string;
  availability: EvidenceAvailability;
  provenance: DataProvenance;
};

export type AssistantMessage = {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
  scope: ChatScope;
  patientContextId: string | null;
  citations: SourceCitation[];
  confidence: "low" | "medium" | "high" | "unknown";
  disclaimer: string | null;
  provenance: DataProvenance;
};

export type ConversationThread = {
  id: string;
  title: string;
  description: string;
  active: boolean;
  sharedState: "local-only" | "sample-shared" | "backend-persisted";
  updatedAt: string;
  messages: AssistantMessage[];
  patientContextId: string | null;
  provenance: DataProvenance;
};

export type ChatAssistantWorkspaceState = {
  threads: ConversationThread[];
  patientContexts: PatientContext[];
  evidenceSources: EvidenceSource[];
  activeThreadId: string;
  activePatientContextId: string;
};
