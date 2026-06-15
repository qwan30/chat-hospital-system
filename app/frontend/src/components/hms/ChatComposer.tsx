import { useState, type FormEvent } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Paperclip, Send, Sparkles } from "lucide-react";

export function ChatComposer({
  onSend,
  context,
  disabled,
  disabledHint,
  value: controlledValue,
  onValueChange,
}: {
  onSend: (text: string) => void;
  context?: string;
  disabled?: boolean;
  disabledHint?: string;
  value?: string;
  onValueChange?: (text: string) => void;
}) {
  const [internalText, setInternalText] = useState("");
  const isControlled = controlledValue !== undefined;
  const text = isControlled ? controlledValue : internalText;
  const setText = (v: string) => {
    if (isControlled) onValueChange?.(v);
    else setInternalText(v);
  };
  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (disabled) return;
    if (!text.trim()) return;
    onSend(text.trim());
    setText("");
  };
  return (
    <form
      onSubmit={submit}
      className="rounded-2xl border bg-card p-3 shadow-sm focus-within:ring-2 focus-within:ring-ring/40"
    >
      {context ? (
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <Badge variant="secondary" className="bg-primary/10 text-primary">
            <Sparkles className="mr-1 h-3 w-3" /> Context: {context}
          </Badge>
        </div>
      ) : null}
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) submit(e);
        }}
        rows={2}
        placeholder={
          disabled
            ? (disabledHint ?? "Waiting for current response…")
            : "Ask anything about the indexed knowledge base..."
        }
        disabled={disabled}
        className="min-h-[44px] resize-none border-0 bg-transparent p-2 shadow-none focus-visible:ring-0"
      />
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 text-muted-foreground">
          <Button type="button" variant="ghost" size="sm" className="h-8 px-2">
            <Paperclip className="h-4 w-4" />
          </Button>
          <span className="text-xs">
            {disabled
              ? (disabledHint ?? "Streaming response…")
              : "Cited answers only · ⇧↵ for newline"}
          </span>
        </div>
        <Button type="submit" size="sm" disabled={disabled || !text.trim()}>
          <Send className="mr-1 h-3.5 w-3.5" /> Send
        </Button>
      </div>
    </form>
  );
}
