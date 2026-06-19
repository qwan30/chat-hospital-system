import { ShieldAlert } from "lucide-react";

export function SafetyFooter() {
  return (
    <div className="mt-8 flex items-center justify-center gap-2 border-t border-border/60 pt-4 text-xs text-muted-foreground">
      <ShieldAlert className="h-3.5 w-3.5" />
      AI can make mistakes. Verify important information.
    </div>
  );
}
