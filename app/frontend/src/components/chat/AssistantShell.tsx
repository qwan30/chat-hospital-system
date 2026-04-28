"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChatComposer, type ComposerSubmitState } from "@/components/chat/ChatComposer";
import { ChatTranscript } from "@/components/chat/ChatTranscript";
import { ConversationSidebar } from "@/components/chat/ConversationSidebar";
import { EvidencePanel } from "@/components/chat/EvidencePanel";
import { PatientContextGate } from "@/components/chat/PatientContextGate";
import {
  addBackendThreadParticipant,
  archiveBackendChatThread,
  askBackendThreadMessage,
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

    setComposerSubmitState({ status: "loading", message: "Saving question and backend answer to the active thread." });
    void (async () => {
      try {
        await askBackendThreadMessage(activeThread.id, readiness.request, apiConfig);
        await loadWorkspace(activeThread.id);
        setComposerSubmitState({
          status: "ready",
          message: "Persisted backend answer saved to this thread.",
          request: readiness.request,
        });
      } catch (error) {
        setComposerSubmitState({
          status: "error",
          message: safeErrorMessage(error, "Unable to save backend thread message."),
        });
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
                <Badge className="border-[#34d399]/30 text-[#34d399]">General knowledge backend</Badge>
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
          <ChatTranscript activeThread={activeThread} />
          <ChatComposer
            activeContext={activePatientContext}
            isSubmitting={composerSubmitState.status === "loading"}
            onSubmitQuestion={handleSubmitQuestion}
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
