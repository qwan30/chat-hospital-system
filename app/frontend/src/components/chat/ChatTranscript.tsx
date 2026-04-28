import { Bot, LockKeyhole, UserRound } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { SourceCitation } from "@/components/chat/SourceCitation";
import { sampleWorkspaceState } from "@/lib/chat-assistant";

export function ChatTranscript() {
  const activeThread =
    sampleWorkspaceState.threads.find((thread) => thread.id === sampleWorkspaceState.activeThreadId) ??
    sampleWorkspaceState.threads[0];

  return (
    <div className="flex-1 min-w-0 overflow-y-auto px-4 py-5 md:px-5">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-5">
        {activeThread.messages.map((message) => {
          const isAssistant = message.role === "assistant";

          return (
            <article
              key={message.id}
              className={
                isAssistant
                  ? "max-w-3xl rounded-md border border-white/10 bg-white/[0.03] p-4"
                  : "ml-auto max-w-2xl rounded-md border border-[#5e6ad2]/30 bg-[#5e6ad2]/10 p-4"
              }
            >
              <div
                className={
                  "mb-3 flex flex-wrap items-center gap-2 text-sm " +
                  (isAssistant ? "text-[#a3a7ad]" : "text-[#cfd3ff]")
                }
              >
                {isAssistant ? <Bot className="size-4 text-[#828fff]" /> : <UserRound className="size-4" />}
                <span>{isAssistant ? "Assistant answer" : "Staff question"}</span>
                <Badge>{message.provenance.visibleLabel}</Badge>
                {isAssistant ? <Badge>Confidence: {message.confidence}</Badge> : null}
              </div>
              <p className={isAssistant ? "text-sm leading-6 text-[#e2e4e7]" : "text-sm leading-6 text-[#eef0ff]"}>
                {message.content}
              </p>
              {isAssistant && message.disclaimer ? (
                <p className="mt-3 rounded-md border border-[#fbbf24]/20 bg-[#fbbf24]/10 px-3 py-2 text-xs leading-5 text-[#fde68a]">
                  {message.disclaimer}
                </p>
              ) : null}
              {message.citations.length > 0 ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  {message.citations.map((citation) => (
                    <SourceCitation key={citation.id} citation={citation} />
                  ))}
                </div>
              ) : null}
            </article>
          );
        })}

        <article className="max-w-3xl rounded-md border border-[#f87171]/30 bg-[#f87171]/10 p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-medium text-[#fecaca]">
            <LockKeyhole className="size-4" />
            Patient-linked evidence remains gated
          </div>
          <p className="text-sm leading-6 text-[#f5b4b4]">
            Patient context can be selected in later story beads, but denied or pending permission states must not show
            patient evidence or citations.
          </p>
        </article>
      </div>
    </div>
  );
}
