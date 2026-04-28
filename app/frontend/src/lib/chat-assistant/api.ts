import type {
  AssistantMessage,
  ChatScope,
  DataProvenance,
  EvidenceSource,
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

export type BackendChatArtifacts = {
  message: AssistantMessage;
  evidenceSources: EvidenceSource[];
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
    const permissionReason =
      context.permissionState === "pending"
        ? "Patient-linked chat is blocked while permission validation is pending."
        : context.permissionState === "denied"
          ? "Patient-linked chat is blocked because permission was denied."
          : "Patient-linked chat requires allowed permission before sending patient_id.";

    return {
      ready: false,
      reason: permissionReason,
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

  const normalizedQuestion = question.trim();
  if (!normalizedQuestion) {
    return {
      ready: false,
      reason: "Question must include non-whitespace text before patient chat submission.",
      scope: context.scope,
    };
  }

  if (!Number.isInteger(topK) || topK < 1 || topK > 20) {
    return {
      ready: false,
      reason: "topK must be an integer between 1 and 20 before patient chat submission.",
      scope: context.scope,
    };
  }

  return {
    ready: true,
    request: {
      patient_id: context.patientId,
      question: normalizedQuestion,
      top_k: topK,
    },
  };
}

export function mapBackendChatResponseToAssistantMessage(
  response: BackendChatResponse,
  scope: ChatScope,
  patientContextId: string | null,
): AssistantMessage {
  return mapBackendChatResponseToChatArtifacts(response, scope, patientContextId).message;
}

export function mapBackendChatResponseToChatArtifacts(
  response: BackendChatResponse,
  scope: ChatScope,
  patientContextId: string | null,
  createdAt = new Date().toISOString(),
): BackendChatArtifacts {
  const evidenceSources = response.citations.map(mapBackendCitationToEvidenceSource);

  return {
    evidenceSources,
    message: {
      id: response.query_id,
      role: "assistant",
      content: response.answer,
      createdAt,
      scope,
      patientContextId,
      confidence: normalizeConfidence(response.confidence),
      disclaimer: response.disclaimer,
      provenance: backendVerifiedProvenance,
      citations: evidenceSources.map(mapEvidenceSourceToCitation),
    },
  };
}

function mapBackendCitationToEvidenceSource(citation: BackendChatCitation): EvidenceSource {
  return {
    id: citation.evidence_id,
    documentId: citation.document_id,
    title: citation.document_title,
    page: citation.page,
    chunkId: citation.chunk_id,
    excerpt: citation.content?.trim() || "No excerpt returned by backend.",
    score: citation.score,
    availability: "available",
    metadata: citation.metadata,
    provenance: backendVerifiedProvenance,
  };
}

function mapEvidenceSourceToCitation(source: EvidenceSource): SourceCitation {
  return {
    id: source.id,
    label: source.page ? `${source.title} p. ${source.page}` : source.title,
    evidenceSourceId: source.id,
    availability: source.availability,
    provenance: backendVerifiedProvenance,
  };
}

function normalizeConfidence(confidence: string): AssistantMessage["confidence"] {
  if (confidence === "low" || confidence === "medium" || confidence === "high") {
    return confidence;
  }

  return "unknown";
}
