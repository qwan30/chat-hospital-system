import type {
  ChatAssistantWorkspaceState,
  DataProvenance,
  EvidenceSource,
  PatientContext,
} from "./types";

export const localSampleProvenance: DataProvenance = {
  status: "local-sample-only",
  visibleLabel: "Local sample",
  sourceLabel: "Frontend sample data",
  note: "This is synthetic UI data for Phase 1 and is not persisted or read from a hospital system.",
};

export const documentedGapProvenance: DataProvenance = {
  status: "documented-gap",
  visibleLabel: "Documented gap",
  sourceLabel: "Missing backend contract",
  note: "This capability is visible for planning only and must not be presented as live hospital data.",
};

export const verifiedBackendProvenance: DataProvenance = {
  status: "verified-backend",
  visibleLabel: "Backend verified",
  sourceLabel: "Patient-scoped chat API",
  note: "The current backend supports patient-scoped chat only after permission validation.",
};

export const samplePatientContexts: PatientContext[] = [
  {
    id: "general-knowledge",
    scope: "general-knowledge",
    patientId: null,
    displayLabel: "General hospital knowledge",
    permissionState: "not-required",
    permissionLabel: "No patient selected",
    provenance: documentedGapProvenance,
  },
  {
    id: "patient-pending-sample",
    scope: "patient-linked",
    patientId: "11111111-1111-4111-8111-111111111111",
    displayLabel: "Synthetic patient context",
    permissionState: "pending",
    permissionLabel: "Permission check pending",
    provenance: localSampleProvenance,
  },
  {
    id: "patient-allowed-sample",
    scope: "patient-linked",
    patientId: "44444444-4444-4444-8444-444444444444",
    displayLabel: "Synthetic allowed context",
    permissionState: "allowed",
    permissionLabel: "Permission allowed",
    provenance: localSampleProvenance,
  },
  {
    id: "patient-denied-sample",
    scope: "patient-linked",
    patientId: "22222222-2222-4222-8222-222222222222",
    displayLabel: "Synthetic denied context",
    permissionState: "denied",
    permissionLabel: "Permission denied",
    provenance: localSampleProvenance,
  },
];

export const sampleEvidenceSources: EvidenceSource[] = [
  {
    id: "evidence-local-policy-transfer",
    documentId: null,
    title: "Ward transfer policy excerpt",
    page: 12,
    chunkId: null,
    excerpt:
      "Transfer requests should include receiving unit confirmation, attending approval, and current observation needs.",
    score: 0.82,
    availability: "available",
    metadata: {
      documentType: "policy",
      mock: true,
    },
    provenance: localSampleProvenance,
  },
  {
    id: "evidence-patient-chart-gated",
    documentId: "33333333-3333-4333-8333-333333333333",
    title: "Patient-linked chart evidence",
    page: null,
    chunkId: null,
    excerpt: "Hidden until backend permission filtering confirms access.",
    score: null,
    availability: "permission-gated",
    metadata: {
      requiresPermission: true,
      mock: true,
    },
    provenance: localSampleProvenance,
  },
  {
    id: "evidence-general-gap",
    documentId: null,
    title: "General hospital knowledge citation",
    page: null,
    chunkId: null,
    excerpt: "Unavailable until a general-scope chat API exists.",
    score: null,
    availability: "unavailable",
    metadata: {
      backendContract: "missing",
    },
    provenance: documentedGapProvenance,
  },
];

export const sampleWorkspaceState: ChatAssistantWorkspaceState = {
  activeThreadId: "thread-local-policy",
  activePatientContextId: "general-knowledge",
  patientContexts: samplePatientContexts,
  evidenceSources: sampleEvidenceSources,
  threads: [
    {
      id: "thread-local-policy",
      title: "Ward transfer policy",
      description: "General knowledge sample, not persisted",
      active: true,
      sharedState: "local-only",
      updatedAt: "2026-04-28T06:00:00.000Z",
      patientContextId: null,
      provenance: localSampleProvenance,
      messages: [
        {
          id: "msg-local-staff-transfer",
          role: "staff",
          content: "What is the ward transfer policy for a patient-linked question?",
          createdAt: "2026-04-28T06:00:00.000Z",
          scope: "general-knowledge",
          patientContextId: null,
          citations: [],
          confidence: "unknown",
          disclaimer: null,
          provenance: localSampleProvenance,
        },
        {
          id: "msg-local-assistant-transfer",
          role: "assistant",
          content:
            "Use the general policy workflow for transfer steps. Select patient context and pass permission validation before showing patient-linked evidence.",
          createdAt: "2026-04-28T06:00:10.000Z",
          scope: "general-knowledge",
          patientContextId: null,
          confidence: "medium",
          disclaimer: "Sample response for UI validation only. Verify clinical guidance before use.",
          provenance: localSampleProvenance,
          citations: [
            {
              id: "citation-local-policy-transfer",
              label: "Policy sample p. 12",
              evidenceSourceId: "evidence-local-policy-transfer",
              availability: "available",
              provenance: localSampleProvenance,
            },
            {
              id: "citation-patient-chart-gated",
              label: "Patient chart gated",
              evidenceSourceId: "evidence-patient-chart-gated",
              availability: "permission-gated",
              provenance: localSampleProvenance,
            },
          ],
        },
      ],
    },
    {
      id: "thread-local-permission",
      title: "Patient context review",
      description: "Permission-state sample, not persisted",
      active: false,
      sharedState: "sample-shared",
      updatedAt: "2026-04-28T05:45:00.000Z",
      patientContextId: "patient-pending-sample",
      provenance: localSampleProvenance,
      messages: [],
    },
  ],
};
