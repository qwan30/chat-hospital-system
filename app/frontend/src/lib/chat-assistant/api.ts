import type {
  AssistantMessage,
  ChatScope,
  DataProvenance,
  PatientContext,
  SourceCitation,
  UUIDString,
} from "./types";

export type BackendChatRequest = {
  patient_id: UUIDString;
  question: string;
  top_k: number;
};

export type BackendChatCitation = {
  evidence_id: string;
  document_id: UUIDString;
  document_title: string;
  page: number;
  chunk_id: UUIDString;
  score: number;
  content?: string | null;
  metadata: Record<string, unknown>;
};

export type BackendChatResponse = {
  query_id: UUIDString;
  answer: string;
  citations: BackendChatCitation[];
  confidence: string;
  disclaimer: string;
};

export type ChatSubmitReadiness =
  | { ready: true; request: BackendChatRequest }
  | { ready: false; reason: string; scope: ChatScope };

const backendVerifiedProvenance: DataProvenance = {
  status: "verified-backend",
  visibleLabel: "Backend verified",
  sourceLabel: "Patient-scoped chat API",
  note: "Current backend route accepts patient_id, question, and top_k after permission validation.",
};

export function prepareVerifiedBackendChatRequest(
  context: PatientContext,
  question: string,
  topK = 5,
): ChatSubmitReadiness {
  if (context.scope !== "patient-linked") {
    return {
      ready: false,
      reason: "General hospital knowledge has no verified backend chat contract yet.",
      scope: context.scope,
    };
  }

  if (context.permissionState !== "allowed") {
    return {
      ready: false,
      reason: "Patient-linked chat requires allowed permission before sending patient_id.",
      scope: context.scope,
    };
  }

  if (!context.patientId) {
    return {
      ready: false,
      reason: "Patient-linked chat requires a selected patient_id.",
      scope: context.scope,
    };
  }

  return {
    ready: true,
    request: {
      patient_id: context.patientId,
      question,
      top_k: topK,
    },
  };
}

export function mapBackendChatResponseToAssistantMessage(
  response: BackendChatResponse,
  scope: ChatScope,
  patientContextId: string | null,
): AssistantMessage {
  return {
    id: response.query_id,
    role: "assistant",
    content: response.answer,
    createdAt: new Date().toISOString(),
    scope,
    patientContextId,
    confidence: normalizeConfidence(response.confidence),
    disclaimer: response.disclaimer,
    provenance: backendVerifiedProvenance,
    citations: response.citations.map(mapBackendCitation),
  };
}

function mapBackendCitation(citation: BackendChatCitation): SourceCitation {
  return {
    id: citation.evidence_id,
    label: `${citation.document_title} p. ${citation.page}`,
    evidenceSourceId: citation.evidence_id,
    availability: "available",
    provenance: backendVerifiedProvenance,
  };
}

function normalizeConfidence(confidence: string): AssistantMessage["confidence"] {
  if (confidence === "low" || confidence === "medium" || confidence === "high") {
    return confidence;
  }

  return "unknown";
}
