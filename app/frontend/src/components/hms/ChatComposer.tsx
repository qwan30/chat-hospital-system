import {
  useState,
  useRef,
  type FormEvent,
  type ReactNode,
  type ChangeEvent,
  type KeyboardEvent,
} from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Paperclip, Send, X, FileText } from "lucide-react";

export function ChatComposer({
  onSend,
  contextNode,
  disabled,
  disabledHint,
  value: controlledValue,
  onValueChange,
  allowAttachment = false,
}: {
  onSend: (text: string, file?: File) => void | Promise<void>;
  contextNode?: ReactNode;
  disabled?: boolean;
  disabledHint?: string;
  value?: string;
  onValueChange?: (text: string) => void;
  allowAttachment?: boolean;
}) {
  const [internalText, setInternalText] = useState("");
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isControlled = controlledValue !== undefined;
  const text = isControlled ? controlledValue : internalText;

  const setText = (v: string) => {
    if (isControlled) onValueChange?.(v);
    else setInternalText(v);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (disabled || isSubmitting) return;
    if (!text.trim() && !attachedFile) return;

    const payloadText = text.trim();
    const payloadFile = attachedFile || undefined;

    setText("");
    setAttachedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";

    setIsSubmitting(true);
    try {
      await onSend(payloadText, payloadFile);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setAttachedFile(e.target.files[0]);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(e);
    }
  };

  return (
    <form
      onSubmit={submit}
      className="rounded-2xl border bg-card p-3 shadow-sm focus-within:ring-2 focus-within:ring-ring/40"
    >
      {contextNode ? (
        <div className="mb-2 flex flex-wrap items-center gap-2">{contextNode}</div>
      ) : null}

      {attachedFile && (
        <div className="mb-2 flex items-center gap-2 rounded-md border bg-muted/50 px-3 py-2 text-sm">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="flex-1 truncate font-medium">{attachedFile.name}</span>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-6 w-6 rounded-full"
            aria-label={`Remove attached file ${attachedFile.name}`}
            onClick={() => {
              setAttachedFile(null);
              if (fileInputRef.current) fileInputRef.current.value = "";
            }}
          >
            <X className="h-3 w-3" aria-hidden="true" />
          </Button>
        </div>
      )}

      <Textarea
        value={text}
        aria-label="Message input"
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={Math.max(2, Math.min(6, text.split("\n").length))}
        placeholder={
          disabled || isSubmitting
            ? (disabledHint ?? "Waiting for current response…")
            : "Ask anything about the indexed knowledge base..."
        }
        disabled={disabled || isSubmitting}
        className="min-h-[44px] resize-none border-0 bg-transparent p-2 shadow-none focus-visible:ring-0"
      />
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 text-muted-foreground">
          {allowAttachment && (
            <>
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                aria-label="File upload input"
                onChange={handleFileChange}
                accept=".txt,.pdf,.md,.csv,.json"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-8 px-2"
                disabled={disabled || isSubmitting}
                aria-label="Attach file"
                onClick={() => fileInputRef.current?.click()}
              >
                <Paperclip className="h-4 w-4" aria-hidden="true" />
              </Button>
            </>
          )}
          <span className="text-xs">
            {disabled
              ? (disabledHint ?? "Streaming response…")
              : "Cited answers only · ⇧↵ for newline"}
          </span>
        </div>
        <Button
          type="submit"
          size="sm"
          disabled={disabled || isSubmitting || (!text.trim() && !attachedFile)}
        >
          <Send className="mr-1 h-3.5 w-3.5" /> Send
        </Button>
      </div>
    </form>
  );
}
