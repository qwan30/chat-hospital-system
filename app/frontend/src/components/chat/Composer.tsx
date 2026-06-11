import { useState, useRef } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Paperclip } from "lucide-react";

interface ComposerProps {
  onSubmit: (message: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function Composer({ onSubmit, placeholder = "Ask a clinical question...", disabled }: ComposerProps) {
  const [value, setValue] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    if (!value.trim() || disabled) return;
    onSubmit(value.trim());
    setValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex items-end gap-3 p-3 bg-bg-surface rounded-xl border border-border-default shadow-card">
      <input ref={fileInputRef} type="file" className="hidden" accept=".pdf,.jpg,.png,.txt" onChange={(e) => {
        const file = e.target.files?.[0];
        if (file) toast("File attached", { description: `${file.name} (${(file.size / 1024).toFixed(1)} KB)` });
      }} />
      <button onClick={() => fileInputRef.current?.click()} className="p-2 text-text-subtle hover:text-text-muted hover:bg-bg-surface-tint rounded-lg transition-colors" title="Attach file">
        <Paperclip className="w-4 h-4" />
      </button>
      <Textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className="flex-1 min-h-[44px] max-h-[120px] resize-none border-0 bg-transparent p-0 text-[14px] focus-visible:ring-0 placeholder:text-text-subtle"
        rows={1}
      />
      <Button onClick={handleSubmit} disabled={disabled || !value.trim()} size="icon" className="h-10 w-10 rounded-lg flex-shrink-0">
        <Send className="w-4 h-4" />
      </Button>
    </div>
  );
}
