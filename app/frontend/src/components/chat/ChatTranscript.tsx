import { useEffect, useRef } from "react";
import { Bot, Loader2, LockKeyhole, UserRound } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { SourceCitation } from "@/components/chat/SourceCitation";
import type { ConversationThread, AssistantMessage } from "@/lib/chat-assistant";
import type { StreamCitationItem, StreamMetadataEvent } from "@/lib/chat-assistant/stream-client";

export type StreamingState = {
  content: string;
  citations: StreamCitationItem[];
  metadata: StreamMetadataEvent | null;
  isStreaming: boolean;
};

export function ChatTranscript({
  activeThread,
  streamingState,
}: {
  activeThread: ConversationThread | undefined;
  streamingState?: StreamingState;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [activeThread?.messages.length, streamingState?.content]);

  return (
    <div ref={scrollRef} className="flex-1 min-w-0 overflow-y-auto px-4 py-5 md:px-5">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-5">
        {!activeThread ? (
          <EmptyThreadNotice title="No conversation selected" body="Choose a thread from the sidebar to inspect its messages." />
        ) : null}

        {activeThread && activeThread.messages.length === 0 && !streamingState?.isStreaming ? (
          <EmptyThreadNotice title={activeThread.title} body="This persisted backend thread has no messages yet." />
        ) : null}

        {activeThread?.messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {/* Streaming in-progress message */}
        {streamingState?.isStreaming && streamingState.content && (
          <article className="max-w-3xl rounded-md border border-white/10 bg-white/[0.03] p-4">
            <div className="mb-3 flex flex-wrap items-center gap-2 text-sm text-[#a3a7ad]">
              <Bot className="size-4 text-[#828fff]" />
              <span>Assistant answer</span>
              <Badge>Streaming</Badge>
              {streamingState.metadata && (
                <Badge>Confidence: {streamingState.metadata.confidence}</Badge>
              )}
            </div>
            <p className="text-sm leading-6 text-[#e2e4e7] whitespace-pre-wrap">
              {streamingState.content}
              <TypingCursor />
            </p>
          </article>
        )}

        {/* Typing indicator when streaming has started but no content yet */}
        {streamingState?.isStreaming && !streamingState.content && (
          <article className="max-w-3xl rounded-md border border-white/10 bg-white/[0.03] p-4">
            <div className="mb-3 flex items-center gap-2 text-sm text-[#a3a7ad]">
              <Bot className="size-4 text-[#828fff]" />
              <span>Assistant is thinking</span>
            </div>
            <TypingIndicator />
          </article>
        )}

        <article className="max-w-3xl rounded-md border border-[#f87171]/30 bg-[#f87171]/10 p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-medium text-[#fecaca]">
            <LockKeyhole className="size-4" />
            Patient-linked evidence remains gated
          </div>
          <p className="text-sm leading-6 text-[#f5b4b4]">
            Patient context can be selected for patient-linked backend threads, but denied or pending permission states
            must not show patient evidence or citations.
          </p>
        </article>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: AssistantMessage }) {
  const isAssistant = message.role === "assistant";

  return (
    <article
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
}

function TypingCursor() {
  return (
    <span className="inline-block w-[2px] h-4 ml-0.5 bg-[#828fff] animate-pulse align-text-bottom" />
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 py-1">
      <span className="inline-block size-2 rounded-full bg-[#828fff] animate-[bounce_1.4s_ease-in-out_infinite]" />
      <span className="inline-block size-2 rounded-full bg-[#828fff] animate-[bounce_1.4s_ease-in-out_0.2s_infinite]" />
      <span className="inline-block size-2 rounded-full bg-[#828fff] animate-[bounce_1.4s_ease-in-out_0.4s_infinite]" />
    </div>
  );
}

function EmptyThreadNotice({ title, body }: { title: string; body: string }) {
  return (
    <article className="max-w-3xl rounded-md border border-white/10 bg-white/[0.03] p-4">
      <div className="mb-2 flex items-center gap-2 text-sm font-medium text-[#d0d6e0]">
        <Bot className="size-4 text-[#828fff]" />
        {title}
      </div>
      <p className="text-sm leading-6 text-[#a3a7ad]">{body}</p>
    </article>
  );
}
