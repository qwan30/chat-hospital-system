"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChatComposer, type ComposerSubmitState } from "@/components/chat/ChatComposer";
import { ChatTranscript, type StreamingState } from "@/components/chat/ChatTranscript";
import { ConversationSidebar } from "@/components/chat/ConversationSidebar";
import { EvidencePanel } from "@/components/chat/EvidencePanel";
import { PatientContextGate } from "@/components/chat/PatientContextGate";
import {
  addBackendThreadParticipant,
  archiveBackendChatThread,
  createBackendChatThread,
  getBackendChatThread,
  listBackendChatThreads,
  mapBackendChatThreadDetailToWorkspaceArtifacts,
  mapBackendChatThreadToConversationThread,
  prepareBackendThreadMessageRequest,
  sampleWorkspaceState,
  updateBackendChatThread,
  type BackendThreadApiConfig,
  type ConversationThread,
  type EvidenceSource,
  type PatientContext,
  type ThreadMessageSubmitReadiness,
} from "@/lib/chat-assistant";
import { streamChat, type StreamCitationItem, type StreamMetadataEvent } from "@/lib/chat-assistant/stream-client";

const DEFAULT_API_BASE_URL = process.env.NEXT_PUBLIC_HOSPITAL_AI_API_BASE_URL ?? "http://localhost:8000";

type WorkspaceLoadState =
  | { status: "config-required"; message: string }
  | { status: "loading"; message: string }
  | { status: "ready"; message: string }
  | { status: "empty"; message: string }
  | { status: "error"; message: string };

export function AssistantShell() {
  const [apiBaseUrl, setApiBaseUrl] = useState(DEFAULT_API_BASE_URL);
  const [apiToken, setApiToken] = useState("");
  const [threads, setThreads] = useState<ConversationThread[]>([]);
  const [evidenceSources, setEvidenceSources] = useState<EvidenceSource[]>([]);
  const [activeThreadId, setActiveThreadId] = useState("");
  const [activePatientContextId, setActivePatientContextId] = useState("general-knowledge");
  const [workspaceState, setWorkspaceState] = useState<WorkspaceLoadState>(
    apiToken.trim()
      ? { status: "loading", message: "Loading persisted backend threads." }
      : { status: "config-required", message: "Enter a backend bearer token before loading persisted threads." },
  );
  const [isCreatingThread, setIsCreatingThread] = useState(false);
  const [composerSubmitState, setComposerSubmitState] = useState<ComposerSubmitState>({
    status: "idle",
    message: "Create or select a persisted backend thread before asking a question.",
  });

  // Streaming state
  const [streamingState, setStreamingState] = useState<StreamingState>({
    content: "",
    citations: [],
    metadata: null,
    isStreaming: false,
  });
  const abortControllerRef = useRef<AbortController | null>(null);

  const patientContexts = useMemo(() => buildPatientContextsFromThreads(threads), [threads]);
  const apiConfig = useMemo<BackendThreadApiConfig>(
    () => ({
      baseUrl: apiBaseUrl.trim(),
      token: apiToken.trim(),
    }),
    [apiBaseUrl, apiToken],
  );

  const activeThread = useMemo(
    () => threads.find((thread) => thread.id === activeThreadId),
    [activeThreadId, threads],
  );
  const activePatientContext = useMemo(
    () =>
      patientContexts.find((context) => context.id === activePatientContextId) ??
      patientContexts.find((context) => context.id === "general-knowledge") ??
      patientContexts[0],
    [activePatientContextId, patientContexts],
  );
  const activeEvidenceSources = useMemo(() => {
    if (!activeThread) {
      return [];
    }

    const citationSourceIds = new Set(
      activeThread.messages.flatMap((message) => message.citations.map((citation) => citation.evidenceSourceId)),
    );

    return evidenceSources.filter((source) => citationSourceIds.has(source.id));
  }, [activeThread, evidenceSources]);

  const hydrateThreadDetail = useCallback(
    async (threadId: string) => {
      try {
        const detail = await getBackendChatThread(threadId, apiConfig);
        const artifact = mapBackendChatThreadDetailToWorkspaceArtifacts(detail);
        setThreads((currentThreads) =>
          currentThreads.map((thread) => (thread.id === threadId ? artifact.thread : thread)),
        );
        setEvidenceSources((currentSources) =>
          dedupeEvidenceSources([...currentSources, ...artifact.evidenceSources]),
        );
        return artifact.thread;
      } catch {
        setWorkspaceState({
          status: "ready",
          message: "Thread summaries loaded. Selected thread details could not load; choose another thread or refresh.",
        });
        return undefined;
      }
    },
    [apiConfig],
  );

  const loadWorkspace = useCallback(
    async (preferredThreadId?: string) => {
      if (!apiConfig.token) {
        setThreads([]);
        setEvidenceSources([]);
        setActiveThreadId("");
        setActivePatientContextId("general-knowledge");
        setWorkspaceState({
          status: "config-required",
          message: "Enter a backend bearer token before loading persisted threads.",
        });
        return;
      }

      setWorkspaceState({ status: "loading", message: "Loading persisted backend threads." });
      try {
        const summaries = await listBackendChatThreads(apiConfig);
        const nextThreads = summaries
          .filter((thread) => thread.status === "active")
          .map((thread) => mapBackendChatThreadToConversationThread(thread));
        const preferred =
          (preferredThreadId ? nextThreads.find((thread) => thread.id === preferredThreadId) : undefined) ??
          nextThreads.find((thread) => thread.id === activeThreadId) ??
          nextThreads[0];

        setThreads(nextThreads);
        setEvidenceSources([]);
        setActiveThreadId(preferred?.id ?? "");
        setActivePatientContextId(preferred?.patientContextId ?? "general-knowledge");
        setWorkspaceState(
          nextThreads.length > 0
            ? { status: "ready", message: `Loaded ${nextThreads.length} persisted backend thread(s).` }
            : { status: "empty", message: "No persisted backend threads yet. Create a conversation to begin." },
        );
        if (preferred) {
          void hydrateThreadDetail(preferred.id);
        }
      } catch (error) {
        setWorkspaceState({
          status: "error",
          message: safeErrorMessage(error, "Unable to load persisted backend threads."),
        });
      }
    },
    [activeThreadId, apiConfig, hydrateThreadDetail],
  );

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      void loadWorkspace();
    }, 0);
    return () => window.clearTimeout(timerId);
  }, [loadWorkspace]);

  function handleSelectThread(threadId: string) {
    const nextThread = threads.find((thread) => thread.id === threadId);

    if (!nextThread) {
      return;
    }

    setActiveThreadId(nextThread.id);
    setActivePatientContextId(nextThread.patientContextId ?? "general-knowledge");
    void hydrateThreadDetail(nextThread.id);
  }

  async function handleCreateThread() {
    if (!activePatientContext) {
      setComposerSubmitState({ status: "error", message: "Select a scope before creating a thread." });
      return;
    }

    const isPatientLinked = activePatientContext.scope === "patient-linked";
    if (isPatientLinked && activePatientContext.permissionState !== "allowed") {
      setComposerSubmitState({
        status: "blocked",
        message: "Patient-linked threads require allowed permission before creation.",
      });
      return;
    }

    if (
      isPatientLinked &&
      !window.confirm(
        `Create a patient-linked conversation for ${activePatientContext.displayLabel}? This persists patient-scoped thread metadata in the backend.`,
      )
    ) {
      setComposerSubmitState({
        status: "idle",
        message: "Patient-linked conversation creation canceled before backend persistence.",
      });
      return;
    }

    setIsCreatingThread(true);
    try {
      const created = await createBackendChatThread(
        {
          title: isPatientLinked ? `${activePatientContext.displayLabel} question` : "General hospital question",
          scope: isPatientLinked ? "patient-linked" : "general",
          patient_id: isPatientLinked ? activePatientContext.patientId : null,
          visibility: "private",
        },
        apiConfig,
      );
      setComposerSubmitState({
        status: "idle",
        message: "Created persisted backend thread. Submit a question to save the first message.",
      });
      await loadWorkspace(created.id);
    } catch (error) {
      setComposerSubmitState({
        status: "error",
        message: safeErrorMessage(error, "Unable to create persisted backend thread."),
      });
    } finally {
      setIsCreatingThread(false);
    }
  }

  async function handleRenameThread() {
    if (!activeThread) {
      return;
    }

    const nextTitle = window.prompt("Rename conversation", activeThread.title)?.trim();
    if (!nextTitle || nextTitle === activeThread.title) {
      return;
    }

    try {
      await updateBackendChatThread(activeThread.id, { title: nextTitle }, apiConfig);
      await loadWorkspace(activeThread.id);
    } catch (error) {
      setComposerSubmitState({
        status: "error",
        message: safeErrorMessage(error, "Unable to rename persisted backend thread."),
      });
    }
  }

  async function handleArchiveThread() {
    if (!activeThread || !window.confirm(`Archive "${activeThread.title}"?`)) {
      return;
    }

    try {
      await archiveBackendChatThread(activeThread.id, apiConfig);
      await loadWorkspace();
    } catch (error) {
      setComposerSubmitState({
        status: "error",
        message: safeErrorMessage(error, "Unable to archive persisted backend thread."),
      });
    }
  }

  async function handleShareThread() {
    if (!activeThread) {
      return;
    }

    const userId = window.prompt("User UUID to share with")?.trim();
    if (!userId) {
      return;
    }

    try {
      await addBackendThreadParticipant(
        activeThread.id,
        {
          user_id: userId,
          access_level: "read",
          can_share: false,
        },
        apiConfig,
      );
      await loadWorkspace(activeThread.id);
    } catch (error) {
      setComposerSubmitState({
        status: "error",
        message: safeErrorMessage(error, "Unable to share persisted backend thread."),
      });
    }
  }

  function handleStopStreaming() {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStreamingState((prev) => ({ ...prev, isStreaming: false }));
    setComposerSubmitState({
      status: "idle",
      message: "Streaming stopped by user.",
    });
  }

  function handleSubmitQuestion(question: string): ThreadMessageSubmitReadiness {
    const readiness = prepareBackendThreadMessageRequest(activeThread, activePatientContext, question);
    if (!readiness.ready) {
      setComposerSubmitState({ status: "blocked", message: readiness.reason });
      return readiness;
    }

    if (!activeThread) {
      const blocked: ThreadMessageSubmitReadiness = {
        ready: false,
        reason: "Create or select a persisted backend thread before submitting a question.",
        scope: activePatientContext?.scope ?? "general-knowledge",
      };
      setComposerSubmitState({ status: "blocked", message: blocked.reason });
      return blocked;
    }

    // Add user message immediately for responsiveness
    const userMessageId = `user-${Date.now()}`;
    setThreads((currentThreads) =>
      currentThreads.map((thread) => {
        if (thread.id !== activeThread.id) return thread;
        return {
          ...thread,
          messages: [
            ...thread.messages,
            {
              id: userMessageId,
              role: "staff" as const,
              content: question,
              createdAt: new Date().toISOString(),
              scope: activeThread.scope,
              patientContextId: activeThread.patientContextId,
              citations: [],
              confidence: "unknown" as const,
              disclaimer: null,
              provenance: {
                status: "verified-backend" as const,
                visibleLabel: "User",
                sourceLabel: "User input",
                note: "User submitted question",
              },
            },
          ],
        };
      }),
    );

    // Use streaming endpoint
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setStreamingState({
      content: "",
      citations: [],
      metadata: null,
      isStreaming: true,
    });
    setComposerSubmitState({ status: "streaming", message: "Streaming response from assistant..." });

    void (async () => {
      let streamedCitations: StreamCitationItem[] = [];
      let streamedMetadata: StreamMetadataEvent | null = null;
      let streamedContent = "";

      try {
        await streamChat({
          baseUrl: apiConfig.baseUrl,
          token: apiConfig.token,
          patientId: activeThread.patientContextId ?? "general",
          question,
          topK: readiness.request.top_k ?? 5,
          threadId: activeThread.id,
          onToken: (token) => {
            streamedContent += token;
            setStreamingState((prev) => ({
              ...prev,
              content: streamedContent,
            }));
          },
          onCitations: (citations) => {
            streamedCitations = citations;
            setStreamingState((prev) => ({
              ...prev,
              citations,
            }));
          },
          onMetadata: (meta) => {
            streamedMetadata = meta;
            setStreamingState((prev) => ({
              ...prev,
              metadata: meta,
            }));
          },
          onDone: () => {
            // Stream complete — will be handled in finally block
          },
          onError: (message) => {
            setComposerSubmitState({
              status: "error",
              message: `Streaming error: ${message}`,
            });
          },
          signal: abortController.signal,
        });

        // Streaming completed — add assistant message to thread
        if (streamedContent) {
          setThreads((currentThreads) =>
            currentThreads.map((thread) => {
              if (thread.id !== activeThread.id) return thread;
              return {
                ...thread,
                messages: [
                  ...thread.messages,
                  {
                    id: `assistant-${Date.now()}`,
                    role: "assistant" as const,
                    content: streamedContent,
                    createdAt: new Date().toISOString(),
                    scope: activeThread.scope,
                    patientContextId: activeThread.patientContextId,
                    citations: streamedCitations.map((c) => ({
                      id: c.evidence_id,
                      label: `${c.document_title} p. ${c.page}`,
                      evidenceSourceId: c.evidence_id,
                      availability: "available" as const,
                      provenance: {
                        status: "verified-backend" as const,
                        visibleLabel: "Backend verified",
                        sourceLabel: "Streaming evidence",
                        note: "Citation from streaming response",
                      },
                    })),
                    confidence: (streamedMetadata?.confidence as "low" | "medium" | "high") ?? "unknown",
                    disclaimer: "AI-assisted retrieval; clinical staff must verify before making decisions.",
                    provenance: {
                      status: "verified-backend" as const,
                      visibleLabel: "Backend verified",
                      sourceLabel: "Streaming chat API",
                      note: `Pipeline: ${streamedMetadata?.pipeline ?? "unknown"}, Model: ${streamedMetadata?.model ?? "unknown"}`,
                    },
                  },
                ],
              };
            }),
          );

          // Add evidence sources from citations
          if (streamedCitations.length > 0) {
            setEvidenceSources((currentSources) =>
              dedupeEvidenceSources([
                ...currentSources,
                ...streamedCitations.map((c) => ({
                  id: c.evidence_id,
                  documentId: c.document_id,
                  title: c.document_title,
                  page: c.page,
                  chunkId: null,
                  excerpt: c.content,
                  score: c.score,
                  availability: "available" as const,
                  metadata: {},
                  provenance: {
                    status: "verified-backend" as const,
                    visibleLabel: "Backend verified",
                    sourceLabel: "Streaming evidence",
                    note: "Evidence from streaming response",
                  },
                })),
              ]),
            );
          }
        }

        setComposerSubmitState({
          status: "ready",
          message: "Streaming response complete.",
          request: readiness.request,
        });
      } catch (error) {
        if ((error as Error).name === "AbortError") {
          setComposerSubmitState({
            status: "idle",
            message: "Streaming stopped by user.",
          });
        } else {
          setComposerSubmitState({
            status: "error",
            message: safeErrorMessage(error, "Streaming request failed."),
          });
        }
      } finally {
        setStreamingState({
          content: "",
          citations: [],
          metadata: null,
          isStreaming: false,
        });
        abortControllerRef.current = null;
      }
    })();

    return readiness;
  }

  return (
    <main className="min-h-dvh bg-[#08090a] text-[#f7f8f8]">
      <div className="grid min-h-dvh grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)_360px]">
        <ConversationSidebar
          activeThread={activeThread}
          activeThreadId={activeThreadId}
          isCreatingThread={isCreatingThread}
          onArchiveThread={handleArchiveThread}
          onCreateThread={handleCreateThread}
          onRenameThread={handleRenameThread}
          onSelectThread={handleSelectThread}
          onShareThread={handleShareThread}
          threads={threads}
        />

        <section className="order-1 flex min-h-[76dvh] min-w-0 flex-col bg-[#0f1011] lg:order-2 lg:min-h-dvh">
          <header className="flex min-h-16 flex-col justify-center gap-3 border-b border-white/10 px-4 py-4 md:px-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="min-w-0">
                <p className="text-xs font-medium uppercase text-[#8a8f98]">Kotaemon-style assistant</p>
                <h1 className="text-lg font-semibold text-white">Ask hospital questions with cited evidence</h1>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge>Persisted threads</Badge>
                <Badge className="border-[#34d399]/30 text-[#34d399]">Streaming enabled</Badge>
              </div>
            </div>

            <div className="grid gap-2 rounded-md border border-white/10 bg-[#08090a] p-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] md:items-center">
              <label className="min-w-0 text-xs text-[#9ca3af]">
                <span className="sr-only">Backend base URL</span>
                <input
                  className="h-9 w-full rounded-md border border-white/10 bg-white/[0.03] px-3 text-sm text-white outline-none placeholder:text-[#6f747d]"
                  onChange={(event) => setApiBaseUrl(event.target.value)}
                  placeholder="Backend base URL"
                  value={apiBaseUrl}
                />
              </label>
              <label className="min-w-0 text-xs text-[#9ca3af]">
                <span className="sr-only">Bearer token</span>
                <input
                  className="h-9 w-full rounded-md border border-white/10 bg-white/[0.03] px-3 text-sm text-white outline-none placeholder:text-[#6f747d]"
                  onChange={(event) => setApiToken(event.target.value)}
                  placeholder="Bearer token, for example dev-doctor"
                  type="password"
                  value={apiToken}
                />
              </label>
              <Button size="sm" variant="secondary" type="button" onClick={() => void loadWorkspace()}>
                <RefreshCw className="size-4" />
                Refresh
              </Button>
              <p
                aria-live="polite"
                className={`text-xs md:col-span-3 ${workspaceState.status === "error" ? "text-[#fca5a5]" : "text-[#9ca3af]"}`}
              >
                {workspaceState.message}
              </p>
            </div>
          </header>

          <PatientContextGate
            activeContext={activePatientContext}
            activeContextId={activePatientContextId}
            contexts={patientContexts}
            onSelectContext={setActivePatientContextId}
          />
          {activeThread && activeThread.messages.length === 0 && !streamingState.isStreaming && (
            <SuggestedPrompts
              scope={activePatientContext?.scope ?? "general-knowledge"}
              onSelect={(prompt) => handleSubmitQuestion(prompt)}
            />
          )}
          <ChatTranscript
            activeThread={activeThread}
            streamingState={streamingState}
          />
          <ChatComposer
            activeContext={activePatientContext}
            isSubmitting={composerSubmitState.status === "loading"}
            isStreaming={streamingState.isStreaming}
            onSubmitQuestion={handleSubmitQuestion}
            onStopStreaming={handleStopStreaming}
            submitState={composerSubmitState}
          />
        </section>

        <EvidencePanel
          activeContext={activePatientContext}
          activeThread={activeThread}
          evidenceSources={activeEvidenceSources}
        />
      </div>
    </main>
  );
}

function dedupeEvidenceSources(sources: EvidenceSource[]): EvidenceSource[] {
  const seen = new Map<string, EvidenceSource>();
  for (const source of sources) {
    seen.set(source.id, source);
  }
  return Array.from(seen.values());
}

function buildPatientContextsFromThreads(threads: ConversationThread[]): PatientContext[] {
  const contexts = new Map<string, PatientContext>();
  const generalContext = sampleWorkspaceState.patientContexts.find((context) => context.id === "general-knowledge");
  if (generalContext) {
    contexts.set(generalContext.id, generalContext);
  }

  for (const thread of threads) {
    if (thread.scope !== "patient-linked" || !thread.patientContextId) {
      continue;
    }
    contexts.set(thread.patientContextId, {
      id: thread.patientContextId,
      scope: "patient-linked",
      patientId: thread.patientContextId,
      displayLabel: `Patient ${thread.patientContextId.slice(0, 8)} from persisted threads`,
      permissionState: "allowed",
      permissionLabel: "Backend read allowed",
      provenance: {
        ...thread.provenance,
        sourceLabel: "Persisted patient chat thread",
        note: "This context is derived from backend threads that passed participant and patient permission checks.",
      },
    });
  }

  for (const context of sampleWorkspaceState.patientContexts) {
    if (!contexts.has(context.id)) {
      contexts.set(context.id, context);
    }
  }

  return Array.from(contexts.values());
}

function safeErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

// ── Suggested Prompts ────────────────────────────────────────────────────

const GENERAL_PROMPTS = [
  { icon: "🏥", label: "Hospital policies", prompt: "What are the hospital's visiting hours and patient safety policies?" },
  { icon: "💊", label: "Medication info", prompt: "What are the common drug interactions I should be aware of for elderly patients?" },
  { icon: "📋", label: "Clinical guidelines", prompt: "Summarize the latest clinical guidelines for hypertension management." },
  { icon: "🔬", label: "Lab reference", prompt: "What are the normal reference ranges for a complete blood count (CBC)?" },
];

const PATIENT_PROMPTS = [
  { icon: "📊", label: "Patient summary", prompt: "Give me a comprehensive summary of this patient's medical history." },
  { icon: "💉", label: "Recent labs", prompt: "What are the most recent lab results for this patient?" },
  { icon: "📅", label: "Appointments", prompt: "List all upcoming and recent appointments for this patient." },
  { icon: "💊", label: "Medications", prompt: "What medications is this patient currently taking and are there any interactions?" },
];

function SuggestedPrompts({
  scope,
  onSelect,
}: {
  scope: string;
  onSelect: (prompt: string) => void;
}) {
  const prompts = scope === "patient-linked" ? PATIENT_PROMPTS : GENERAL_PROMPTS;

  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-6">
      <p className="mb-3 text-center text-xs font-medium uppercase tracking-wider text-[#8a8f98]">
        Suggested questions
      </p>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {prompts.map((item) => (
          <button
            key={item.prompt}
            type="button"
            onClick={() => onSelect(item.prompt)}
            className="group flex items-start gap-3 rounded-lg border border-white/10 bg-white/[0.02] px-3.5 py-3 text-left transition-all hover:border-white/20 hover:bg-white/[0.05]"
          >
            <span className="mt-0.5 text-base">{item.icon}</span>
            <div className="min-w-0">
              <span className="block text-sm font-medium text-[#e5e7eb] group-hover:text-white">
                {item.label}
              </span>
              <span className="mt-0.5 block text-xs leading-snug text-[#6f747d] group-hover:text-[#9ca3af]">
                {item.prompt}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
