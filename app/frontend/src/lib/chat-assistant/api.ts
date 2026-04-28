import type {
  AssistantMessage,
  ChatScope,
  ConversationParticipant,
  ConversationThread,
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

export type BackendThreadWorkspaceArtifacts = {
  thread: ConversationThread;
  evidenceSources: EvidenceSource[];
};

export type BackendThreadScope = "general" | "patient-linked";
export type BackendThreadVisibility = "private" | "shared";
export type BackendThreadStatus = "active" | "archived";
export type BackendParticipantAccessLevel = "owner" | "write" | "read";
export type BackendMessageRole = "user" | "assistant" | "system";
export type BackendPatientPermissionState = "not-required" | "pending" | "allowed" | "denied";

export type BackendChatThread = {
  id: UUIDString;
  title: string;
  scope: BackendThreadScope;
  patient_id: UUIDString | null;
  visibility: BackendThreadVisibility;
  status: BackendThreadStatus;
  owner_user_id: UUIDString;
  created_trace_id: string;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
};

export type BackendChatMessage = {
  id: UUIDString;
  thread_id: UUIDString;
  sender_user_id: UUIDString | null;
  ai_query_id: UUIDString | null;
  patient_id: UUIDString | null;
  role: BackendMessageRole;
  scope: BackendThreadScope;
  content: string;
  patient_permission_state: BackendPatientPermissionState;
  citations: BackendChatCitation[];
  metadata: Record<string, unknown>;
  trace_id: string;
  created_at: string;
};

export type BackendChatThreadDetail = BackendChatThread & {
  participants: BackendChatParticipant[];
  messages: BackendChatMessage[];
};

export type BackendChatParticipant = {
  id: UUIDString;
  thread_id: UUIDString;
  user_id: UUIDString;
  access_level: BackendParticipantAccessLevel;
  can_share: boolean;
  added_by_user_id: UUIDString;
  created_trace_id: string;
  last_read_at: string | null;
  created_at: string;
  updated_at: string;
};

export type BackendChatThreadCreateRequest = {
  title: string;
  scope?: BackendThreadScope;
  patient_id?: UUIDString | null;
  visibility?: BackendThreadVisibility;
};

export type BackendChatThreadUpdateRequest = {
  title?: string;
  visibility?: BackendThreadVisibility;
  status?: BackendThreadStatus;
};

export type BackendThreadMessageRequest = {
  question: string;
  top_k?: number;
};

export type BackendThreadMessageResponse = {
  user_message: BackendChatMessage;
  assistant_message: BackendChatMessage;
};

export type BackendChatParticipantCreateRequest = {
  user_id: UUIDString;
  access_level?: Exclude<BackendParticipantAccessLevel, "owner">;
  can_share?: boolean;
};

export type BackendChatParticipantUpdateRequest = {
  access_level?: Exclude<BackendParticipantAccessLevel, "owner">;
  can_share?: boolean;
};

export type BackendListResponse<T> = {
  items: T[];
};

export type BackendThreadApiConfig = {
  baseUrl?: string;
  token?: string;
  fetcher?: typeof fetch;
};

export type ChatSubmitReadiness =
  | { ready: true; request: BackendChatRequest }
  | { ready: false; reason: string; scope: ChatScope };

export type ThreadMessageSubmitReadiness =
  | { ready: true; request: BackendThreadMessageRequest }
  | { ready: false; reason: string; scope: ChatScope };

const backendVerifiedProvenance: DataProvenance = {
  status: "verified-backend",
  visibleLabel: "Backend verified",
  sourceLabel: "Patient-scoped chat API",
  note: "Current backend route accepts patient_id, question, and top_k after permission validation.",
};

const backendThreadProvenance: DataProvenance = {
  status: "verified-backend",
  visibleLabel: "Backend persisted",
  sourceLabel: "Persisted chat thread API",
  note: "Thread list, messages, and sharing state are loaded from the backend chat-thread API.",
};

const generalKnowledgeProvenance: DataProvenance = {
  status: "verified-backend",
  visibleLabel: "Backend verified",
  sourceLabel: "Approved general knowledge API",
  note: "General answers use backend-approved non-PHI knowledge sources and do not require patient context.",
};

const hmsAppointmentProvenance: DataProvenance = {
  status: "verified-backend",
  visibleLabel: "HMS-derived",
  sourceLabel: "HMS appointment evidence",
  note: "Appointment evidence is imported from the HMS appointment contract and remains patient-permission gated.",
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

export function mapBackendChatThreadToConversationThread(
  thread: BackendChatThread,
  messages: BackendChatMessage[] = [],
  participants: BackendChatParticipant[] = [],
): ConversationThread {
  const scope = mapBackendThreadScope(thread.scope);
  const participantCount = participants.length;

  return {
    id: thread.id,
    title: thread.title,
    description:
      thread.scope === "patient-linked"
        ? "Persisted patient-linked backend thread"
        : "Persisted general hospital knowledge thread",
    scope,
    active: thread.status === "active",
    sharedState: "backend-persisted",
    updatedAt: thread.last_message_at ?? thread.updated_at,
    messages: messages.map(mapBackendChatMessageToAssistantMessage),
    patientContextId: thread.patient_id,
    participants: participants.map(mapBackendParticipantToConversationParticipant),
    provenance: {
      ...backendThreadProvenance,
      note:
        participantCount > 0
          ? `${backendThreadProvenance.note} Participants loaded: ${participantCount}.`
          : backendThreadProvenance.note,
    },
  };
}

export function mapBackendChatThreadDetailToConversationThread(
  detail: BackendChatThreadDetail,
): ConversationThread {
  return mapBackendChatThreadToConversationThread(detail, detail.messages, detail.participants);
}

export function mapBackendChatThreadDetailToWorkspaceArtifacts(
  detail: BackendChatThreadDetail,
): BackendThreadWorkspaceArtifacts {
  const messageArtifacts = detail.messages.map(mapBackendChatMessageToChatArtifacts);
  const evidenceSources = dedupeEvidenceSources(messageArtifacts.flatMap((artifact) => artifact.evidenceSources));
  const thread = mapBackendChatThreadToConversationThread(detail, [], detail.participants);

  return {
    evidenceSources,
    thread: {
      ...thread,
      messages: messageArtifacts.map((artifact) => artifact.message),
    },
  };
}

export function mapBackendChatMessageToChatArtifacts(message: BackendChatMessage): BackendChatArtifacts {
  const evidenceSources = message.citations.map(mapBackendCitationToEvidenceSource);

  return {
    evidenceSources,
    message: {
      id: message.id,
      role: mapBackendMessageRole(message.role),
      content: message.content,
      createdAt: message.created_at,
      scope: mapBackendThreadScope(message.scope),
      patientContextId: message.patient_id,
      confidence: normalizeConfidence(String(message.metadata.confidence ?? "unknown")),
      disclaimer: typeof message.metadata.disclaimer === "string" ? message.metadata.disclaimer : null,
      provenance: message.scope === "general" ? generalKnowledgeProvenance : backendVerifiedProvenance,
      citations: evidenceSources.map(mapEvidenceSourceToCitation),
    },
  };
}

export function mapBackendChatMessageToAssistantMessage(message: BackendChatMessage): AssistantMessage {
  return mapBackendChatMessageToChatArtifacts(message).message;
}

export async function listBackendChatThreads(config: BackendThreadApiConfig = {}): Promise<BackendChatThread[]> {
  const response = await requestBackendJson<BackendListResponse<BackendChatThread>>(config, "/chat-threads");
  return response.items;
}

export function createBackendChatThread(
  payload: BackendChatThreadCreateRequest,
  config: BackendThreadApiConfig = {},
): Promise<BackendChatThread> {
  return requestBackendJson(config, "/chat-threads", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getBackendChatThread(
  threadId: UUIDString,
  config: BackendThreadApiConfig = {},
): Promise<BackendChatThreadDetail> {
  return requestBackendJson(config, `/chat-threads/${threadId}`);
}

export function updateBackendChatThread(
  threadId: UUIDString,
  payload: BackendChatThreadUpdateRequest,
  config: BackendThreadApiConfig = {},
): Promise<BackendChatThread> {
  return requestBackendJson(config, `/chat-threads/${threadId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function archiveBackendChatThread(
  threadId: UUIDString,
  config: BackendThreadApiConfig = {},
): Promise<BackendChatThread> {
  return requestBackendJson(config, `/chat-threads/${threadId}`, {
    method: "DELETE",
  });
}

export function askBackendThreadMessage(
  threadId: UUIDString,
  payload: BackendThreadMessageRequest,
  config: BackendThreadApiConfig = {},
): Promise<BackendThreadMessageResponse> {
  return requestBackendJson(config, `/chat-threads/${threadId}/messages`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function prepareBackendThreadMessageRequest(
  thread: ConversationThread | undefined,
  context: PatientContext | undefined,
  question: string,
  topK = 5,
): ThreadMessageSubmitReadiness {
  const normalizedQuestion = question.trim();
  if (!thread) {
    return {
      ready: false,
      reason: "Create or select a persisted backend thread before submitting a question.",
      scope: context?.scope ?? "general-knowledge",
    };
  }

  if (!thread.active) {
    return {
      ready: false,
      reason: "Archived chat threads cannot accept new questions.",
      scope: thread.scope,
    };
  }

  if (!normalizedQuestion) {
    return {
      ready: false,
      reason: "Question must include non-whitespace text before chat submission.",
      scope: thread.scope,
    };
  }

  if (!Number.isInteger(topK) || topK < 1 || topK > 20) {
    return {
      ready: false,
      reason: "topK must be an integer between 1 and 20 before chat submission.",
      scope: thread.scope,
    };
  }

  if (thread.scope === "general-knowledge") {
    return {
      ready: true,
      request: {
        question: normalizedQuestion,
        top_k: topK,
      },
    };
  }

  if (!context || context.scope !== "patient-linked") {
    return {
      ready: false,
      reason: "Patient-linked thread submission requires the matching patient context.",
      scope: "patient-linked",
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

  if (!context.patientId || context.patientId !== thread.patientContextId) {
    return {
      ready: false,
      reason: "Patient-linked chat requires the selected patient context to match the backend thread patient_id.",
      scope: context.scope,
    };
  }

  return {
    ready: true,
    request: {
      question: normalizedQuestion,
      top_k: topK,
    },
  };
}

export async function listBackendThreadMessages(
  threadId: UUIDString,
  config: BackendThreadApiConfig = {},
): Promise<BackendChatMessage[]> {
  const response = await requestBackendJson<BackendListResponse<BackendChatMessage>>(
    config,
    `/chat-threads/${threadId}/messages`,
  );
  return response.items;
}

export async function listBackendThreadParticipants(
  threadId: UUIDString,
  config: BackendThreadApiConfig = {},
): Promise<BackendChatParticipant[]> {
  const response = await requestBackendJson<BackendListResponse<BackendChatParticipant>>(
    config,
    `/chat-threads/${threadId}/participants`,
  );
  return response.items;
}

export function addBackendThreadParticipant(
  threadId: UUIDString,
  payload: BackendChatParticipantCreateRequest,
  config: BackendThreadApiConfig = {},
): Promise<BackendChatParticipant> {
  return requestBackendJson(config, `/chat-threads/${threadId}/participants`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateBackendThreadParticipant(
  threadId: UUIDString,
  participantId: UUIDString,
  payload: BackendChatParticipantUpdateRequest,
  config: BackendThreadApiConfig = {},
): Promise<BackendChatParticipant> {
  return requestBackendJson(config, `/chat-threads/${threadId}/participants/${participantId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function removeBackendThreadParticipant(
  threadId: UUIDString,
  participantId: UUIDString,
  config: BackendThreadApiConfig = {},
): Promise<BackendChatParticipant> {
  return requestBackendJson(config, `/chat-threads/${threadId}/participants/${participantId}`, {
    method: "DELETE",
  });
}

function mapBackendCitationToEvidenceSource(citation: BackendChatCitation): EvidenceSource {
  const provenance =
    citation.metadata.source_system === "hospital-management-system"
      ? hmsAppointmentProvenance
      : citation.metadata.approved_non_phi === true
        ? generalKnowledgeProvenance
        : backendVerifiedProvenance;

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
    provenance,
  };
}

async function requestBackendJson<T>(
  config: BackendThreadApiConfig,
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const fetcher = config.fetcher ?? fetch;
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("content-type")) {
    headers.set("content-type", "application/json");
  }
  if (config.token && !headers.has("authorization")) {
    headers.set("authorization", `Bearer ${config.token}`);
  }

  const response = await fetcher(`${normalizeBaseUrl(config.baseUrl)}/api/v1${path}`, {
    ...init,
    headers,
  });
  if (!response.ok) {
    throw new Error(await describeBackendError(response));
  }
  return (await response.json()) as T;
}

async function describeBackendError(response: Response): Promise<string> {
  try {
    await response.json();
  } catch {
    // Keep raw backend details out of the rendered client error message.
  }
  if (response.status === 401) {
    return "Hospital assistant API authentication failed. Check the bearer token.";
  }
  if (response.status === 403) {
    return "Hospital assistant API access was denied for this request.";
  }
  if (response.status === 404) {
    return "Hospital assistant API resource was not found.";
  }
  if (response.status >= 500) {
    return "Hospital assistant API is unavailable. Try again later or check backend logs.";
  }
  return `Hospital assistant API request failed with status ${response.status}.`;
}

function normalizeBaseUrl(baseUrl: string | undefined): string {
  return baseUrl ? baseUrl.replace(/\/$/, "") : "";
}

function mapBackendThreadScope(scope: BackendThreadScope): ChatScope {
  return scope === "patient-linked" ? "patient-linked" : "general-knowledge";
}

function mapBackendMessageRole(role: BackendMessageRole): AssistantMessage["role"] {
  if (role === "assistant" || role === "system") {
    return role;
  }
  return "staff";
}

function mapBackendParticipantToConversationParticipant(
  participant: BackendChatParticipant,
): ConversationParticipant {
  return {
    id: participant.id,
    userId: participant.user_id,
    accessLevel: participant.access_level,
    canShare: participant.can_share,
    lastReadAt: participant.last_read_at,
  };
}

function mapEvidenceSourceToCitation(source: EvidenceSource): SourceCitation {
  return {
    id: source.id,
    label: source.page ? `${source.title} p. ${source.page}` : source.title,
    evidenceSourceId: source.id,
    availability: source.availability,
    provenance: source.provenance,
  };
}

function dedupeEvidenceSources(sources: EvidenceSource[]): EvidenceSource[] {
  const seen = new Map<string, EvidenceSource>();
  for (const source of sources) {
    seen.set(source.id, source);
  }
  return Array.from(seen.values());
}

function normalizeConfidence(confidence: string): AssistantMessage["confidence"] {
  if (confidence === "low" || confidence === "medium" || confidence === "high") {
    return confidence;
  }

  return "unknown";
}
