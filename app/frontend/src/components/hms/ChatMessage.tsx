import { cn } from "@/lib/utils";
import { Sparkles, User } from "lucide-react";
import { CitationChip } from "./CitationChip";
import type { ReactNode } from "react";

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
  time?: string;
  extra?: ReactNode;
}

export function ChatMessage({ msg, isError, errorControls }: { msg: ChatMessageData; isError?: boolean; errorControls?: ReactNode }) {
  const isAssistant = msg.role === "assistant";

  // Render assistant content with inline [n] markers replaced by chips
  const renderContent = () => {
    if (!msg.citations?.length) return <p className="whitespace-pre-wrap">{msg.content}</p>;
    const parts = msg.content.split(/(\[\d+\])/g);
    return (
      <p className="whitespace-pre-wrap leading-relaxed">
        {parts.map((p, i) => {
          const m = p.match(/^\[(\d+)\]$/);
          if (m) {
            const n = Number(m[1]);
            const c = msg.citations!.find((c) => c.n === n);
            if (c) return <CitationChip key={i} n={n} sourceId={c.sourceId} className="mx-0.5" />;
          }
          return <span key={i}>{p}</span>;
        })}
      </p>
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
