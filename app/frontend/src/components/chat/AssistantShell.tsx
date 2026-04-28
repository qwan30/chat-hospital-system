"use client";

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { ChatComposer, type ComposerSubmitState } from "@/components/chat/ChatComposer";
import { ChatTranscript } from "@/components/chat/ChatTranscript";
import { ConversationSidebar } from "@/components/chat/ConversationSidebar";
import { EvidencePanel } from "@/components/chat/EvidencePanel";
import { PatientContextGate } from "@/components/chat/PatientContextGate";
import { prepareVerifiedBackendChatRequest, sampleWorkspaceState, type ChatSubmitReadiness } from "@/lib/chat-assistant";

export function AssistantShell() {
  const [activeThreadId, setActiveThreadId] = useState(sampleWorkspaceState.activeThreadId);
  const [activePatientContextId, setActivePatientContextId] = useState(sampleWorkspaceState.activePatientContextId);
  const [composerSubmitState, setComposerSubmitState] = useState<ComposerSubmitState>({
    status: "idle",
    message: "Submit a question to validate whether the selected scope can use the patient chat backend.",
  });

  const activeThread = useMemo(
    () => sampleWorkspaceState.threads.find((thread) => thread.id === activeThreadId) ?? sampleWorkspaceState.threads[0],
    [activeThreadId],
  );
  const activePatientContext = useMemo(
    () =>
      sampleWorkspaceState.patientContexts.find((context) => context.id === activePatientContextId) ??
      sampleWorkspaceState.patientContexts[0],
    [activePatientContextId],
  );
  const activeEvidenceSources = useMemo(() => {
    if (!activeThread) {
      return [];
    }

    const citationSourceIds = new Set(
      activeThread.messages.flatMap((message) => message.citations.map((citation) => citation.evidenceSourceId)),
    );

    return sampleWorkspaceState.evidenceSources.filter((source) => citationSourceIds.has(source.id));
  }, [activeThread]);

  function handleSelectThread(threadId: string) {
    const nextThread = sampleWorkspaceState.threads.find((thread) => thread.id === threadId);

    if (!nextThread) {
      return;
    }

    setActiveThreadId(nextThread.id);
    setActivePatientContextId(nextThread.patientContextId ?? sampleWorkspaceState.activePatientContextId);
  }

  function handleSelectFirstThread() {
    handleSelectThread(sampleWorkspaceState.activeThreadId);
  }

  function handleSubmitQuestion(question: string): ChatSubmitReadiness {
    if (!activePatientContext) {
      const readiness: ChatSubmitReadiness = {
        ready: false,
        reason: "Select a chat scope before submitting a question.",
        scope: "general-knowledge",
      };

      setComposerSubmitState({ status: "error", message: readiness.reason });
      return readiness;
    }

    const readiness = prepareVerifiedBackendChatRequest(activePatientContext, question);
    if (!readiness.ready) {
      setComposerSubmitState({ status: "blocked", message: readiness.reason });
      return readiness;
    }

    setComposerSubmitState({
      status: "ready",
      message: "Backend-ready patient chat request prepared. API submission remains deferred until live wiring.",
      request: readiness.request,
    });
    return readiness;
  }

  return (
    <main className="min-h-dvh bg-[#08090a] text-[#f7f8f8]">
      <div className="grid min-h-dvh grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)_360px]">
        <ConversationSidebar
          activeThread={activeThread}
          activeThreadId={activeThreadId}
          onSelectFirstThread={handleSelectFirstThread}
          onSelectThread={handleSelectThread}
          threads={sampleWorkspaceState.threads}
        />

        <section className="order-1 flex min-h-[76dvh] min-w-0 flex-col bg-[#0f1011] lg:order-2 lg:min-h-dvh">
          <header className="flex min-h-16 flex-col justify-center gap-3 border-b border-white/10 px-4 py-4 md:flex-row md:items-center md:justify-between md:px-5">
            <div className="min-w-0">
              <p className="text-xs font-medium uppercase text-[#8a8f98]">Kotaemon-style assistant</p>
              <h1 className="text-lg font-semibold text-white">Ask hospital questions with cited evidence</h1>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge>General scope ready</Badge>
              <Badge className="border-[#34d399]/30 text-[#34d399]">Patient gate visible</Badge>
            </div>
          </header>

          <PatientContextGate
            activeContext={activePatientContext}
            activeContextId={activePatientContextId}
            contexts={sampleWorkspaceState.patientContexts}
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
