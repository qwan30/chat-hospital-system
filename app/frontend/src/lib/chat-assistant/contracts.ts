import type { ChatDataStatus, ChatScope, PatientPermissionState } from "./types";

export type ContractStatus = ChatDataStatus;

export type AssistantScope = ChatScope;

export type PermissionState = PatientPermissionState;

export type ContractInventoryItem = {
  id: string;
  label: string;
  status: ContractStatus;
  source: string;
  implementationRule: string;
};

export type ChatAssistantRequest = {
  scope: AssistantScope;
  question: string;
  patientId?: string;
  topK?: number;
};

export type ChatAssistantCitation = {
  evidenceId: string;
  documentId: string;
  documentTitle: string;
  page: number;
  chunkId: string;
  score: number;
  content?: string;
  metadata: Record<string, unknown>;
};

export type ChatAssistantResponse = {
  queryId: string;
  answer: string;
  citations: ChatAssistantCitation[];
  confidence: "low" | "medium" | "high" | string;
  disclaimer: string;
};

export type ChatAssistantUiBoundary = {
  permissionState: PermissionState;
  dataStatus: ContractStatus;
  label: string;
};

export const chatAssistantContractInventory = [
  {
    id: "patient-scoped-chat",
    label: "Patient-scoped chat request and cited answer",
    status: "verified-backend",
    source: "app/backend/src/hospital_ai/api/routes/chat.py and schemas/chat.py",
    implementationRule:
      "Use only when a patientId is selected; request body is patient_id, question, and top_k.",
  },
  {
    id: "patient-permission-check",
    label: "Patient read permission gate",
    status: "verified-backend",
    source: "app/backend/src/hospital_ai/services/permissions.py",
    implementationRule:
      "Show patient-linked answers and citations only after permission is allowed; denied state must block PHI evidence.",
  },
  {
    id: "permission-filtered-citations",
    label: "Permission-filtered citation evidence",
    status: "verified-backend",
    source: "app/backend/src/hospital_ai/services/retrieval.py and schemas/documents.py",
    implementationRule:
      "Citation UI may show evidence_id, document_id, document_title, page, chunk_id, score, content, and metadata returned by the backend.",
  },
  {
    id: "shared-conversation-threads",
    label: "Shared conversation threads",
    status: "verified-backend",
    source: "app/backend/src/hospital_ai/api/routes/chat_threads.py and schemas/chat_threads.py",
    implementationRule:
      "Thread lists, messages, sharing labels, and participant actions must use /api/v1/chat-threads with bearer auth.",
  },
  {
    id: "general-hospital-knowledge",
    label: "General hospital knowledge chat",
    status: "verified-backend",
    source: "app/backend/src/hospital_ai/services/general_knowledge.py",
    implementationRule:
      "General-scope prompts must go through persisted general chat threads and may cite only approved non-PHI knowledge sources.",
  },
  {
    id: "hms-integration-data",
    label: "HMS appointment summary evidence",
    status: "verified-backend",
    source: "app/backend/src/hospital_ai/api/routes/hms.py and services/hms_appointments.py",
    implementationRule:
      "Only imported synthetic or de-identified appointment summaries are connected; citations must preserve HMS source_system, source_family, source_record_id, and patient permission metadata.",
  },
] satisfies ContractInventoryItem[];

export const chatAssistantUiBoundaries = [
  {
    permissionState: "not-required",
    dataStatus: "verified-backend",
    label: "General knowledge mode: backend-approved non-PHI retrieval does not require patient context.",
  },
  {
    permissionState: "pending",
    dataStatus: "verified-backend",
    label: "Patient mode: wait for backend permission validation before showing PHI evidence.",
  },
  {
    permissionState: "allowed",
    dataStatus: "verified-backend",
    label: "Patient mode: backend-backed answer and citations may be displayed.",
  },
  {
    permissionState: "denied",
    dataStatus: "verified-backend",
    label: "Patient mode: block answer content and citations; show access-denied state.",
  },
] satisfies ChatAssistantUiBoundary[];
