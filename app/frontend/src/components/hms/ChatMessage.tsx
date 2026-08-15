import { cn } from "@/lib/utils";
import { Sparkles, User } from "lucide-react";
import { CitationChip } from "./CitationChip";
import type { ReactNode } from "react";
import { GraphExplanationPanel } from "./GraphExplanationPanel";
import type { StreamCitation } from "@/lib/stream-client";

export interface ChatCitationRef {
  n: number;
  sourceId: string;
}

export interface ChatMessageData {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: ChatCitationRef[];
  rawCitations?: StreamCitation[];
  evidenceById?: Record<
    string,
    { id?: string; n?: number; sourceId?: string; document_id?: string; [key: string]: unknown }
  >;
  graphExplanation?: unknown;
  streamingMode?: string;
  isStreaming?: boolean;
  time?: string;
  extra?: ReactNode;
}

export interface MarkdownRendererProps {
  content: string;
  allowHtml?: boolean;
  allowedProtocols?: string[];
  renderCitation?: (id: string, n?: number) => ReactNode;
  citations?: ChatCitationRef[];
  evidenceById?: Record<
    string,
    { id?: string; n?: number; sourceId?: string; document_id?: string; [key: string]: unknown }
  >;
}

export function MarkdownRenderer({
  content,
  allowHtml = false,
  allowedProtocols = ["http", "https"],
  renderCitation,
  citations,
  evidenceById,
}: MarkdownRendererProps) {
  // React renders this value as a text child, so markup is escaped instead of
  // being interpreted by the browser. Regex-based HTML sanitization is
  // incomplete for malformed and nested markup and must not be used here.
  const sanitized = content;

  const parts = sanitized.split(/(\[[a-zA-Z0-9_-]+\])/g);

  return (
    <div className="whitespace-pre-wrap leading-relaxed">
      {parts.map((part, index) => {
        const match = part.match(/^\[([a-zA-Z0-9_-]+)\]$/);
        if (match) {
          const rawId = match[1];
          let nVal = Number(rawId);
          if (isNaN(nVal)) {
            const numMatch = rawId.match(/\d+/);
            if (numMatch) nVal = Number(numMatch[0]);
            else nVal = Math.floor(index / 2) + 1;
          }
          if (renderCitation) {
            return (
              <span key={index} className="inline-block mx-0.5">
                {renderCitation(rawId, !isNaN(nVal) ? nVal : undefined)}
              </span>
            );
          }
          if (evidenceById && evidenceById[rawId]) {
            const ev = evidenceById[rawId];
            return (
              <CitationChip
                key={index}
                n={ev.n ?? nVal}
                sourceId={ev.sourceId ?? ev.document_id ?? ev.id ?? ""}
                evidence={ev}
                className="mx-0.5"
              />
            );
          }
          if (!isNaN(nVal) && citations) {
            const cit = citations.find((c) => c.n === nVal);
            if (cit) {
              return (
                <CitationChip key={index} n={cit.n} sourceId={cit.sourceId} className="mx-0.5" />
              );
            }
          }
          return (
            <CitationChip
              key={index}
              n={!isNaN(nVal) ? nVal : 1}
              sourceId={rawId}
              className="mx-0.5"
            />
          );
        }
        return <span key={index}>{part}</span>;
      })}
    </div>
  );
}

export function ChatMessage({
  msg,
  isError,
  errorControls,
}: {
  msg: ChatMessageData;
  isError?: boolean;
  errorControls?: ReactNode;
}) {
  const isAssistant = msg.role === "assistant";

  const renderContent = () => {
    if (!isAssistant) {
      return <p className="whitespace-pre-wrap">{msg.content}</p>;
    }

    return (
      <div className="space-y-3">
        <MarkdownRenderer
          content={msg.content}
          allowHtml={false}
          allowedProtocols={["http", "https"]}
          citations={msg.citations}
          evidenceById={msg.evidenceById}
          renderCitation={(id, n) => {
            if (msg.evidenceById && msg.evidenceById[id]) {
              const ev = msg.evidenceById[id];
              return (
                <CitationChip
                  evidence={ev}
                  n={ev.n ?? n}
                  sourceId={ev.sourceId ?? ev.document_id ?? ev.id ?? id}
                />
              );
            }
            const nVal = Number(id);
            if (!isNaN(nVal) && msg.citations) {
              const cit = msg.citations.find((c) => c.n === nVal);
              if (cit) {
                return <CitationChip n={cit.n} sourceId={cit.sourceId} />;
              }
            }
            return <CitationChip n={n ?? 1} sourceId={id} />;
          }}
        />
        <GraphExplanationPanel explanation={msg.graphExplanation} />
        {(msg.isStreaming || msg.streamingMode) && (
          <div className="pt-1 text-[11px] font-medium text-muted-foreground flex items-center gap-1.5 border-t border-border/40">
            <span
              className="inline-block w-2 h-2 rounded-full bg-ai animate-pulse"
              aria-hidden="true"
            />
            <span>Validated sentence streaming</span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      data-msg-role={msg.role}
      data-msg-id={msg.id}
      className={cn("flex gap-3", isAssistant ? "" : "flex-row-reverse")}
    >
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isAssistant ? "bg-ai/10 text-ai" : "bg-primary text-primary-foreground",
        )}
      >
        {isAssistant ? <Sparkles className="h-4 w-4" /> : <User className="h-4 w-4" />}
      </div>
      <div className={cn("max-w-[80%]", isAssistant ? "" : "items-end")}>
        <div className="mb-1 flex items-center gap-2 text-xs text-muted-foreground">
          <span className="font-medium text-foreground">{isAssistant ? "HMS Copilot" : "You"}</span>
          {msg.time ? <span>· {msg.time}</span> : null}
        </div>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm",
            isAssistant
              ? "border bg-card text-card-foreground"
              : "bg-primary text-primary-foreground",
            isError && "border border-destructive",
          )}
        >
          {renderContent()}
          {msg.extra}
          {errorControls && <div className="mt-3">{errorControls}</div>}
        </div>
      </div>
    </div>
  );
}
