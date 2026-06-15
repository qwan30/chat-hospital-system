import { AlertTriangle, Loader2, Play, RotateCcw, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { StreamStatus } from "@/hooks/use-stream-text";
import { cn } from "@/lib/utils";

interface Props {
  status: StreamStatus;
  error?: string;
  progress: number;
  total: number;
  onRetry: () => void;
  onResume: () => void;
  onStop: () => void;
  className?: string;
  /** Label shown on the interrupted banner CTA group. */
  resumeLabel?: string;
}

export function StreamingControls({
  status,
  error,
  progress,
  total,
  onRetry,
  onResume,
  onStop,
  className,
  resumeLabel = "Resume from where it stopped",
}: Props) {
  if (status === "streaming") {
    const pct = total > 0 ? Math.min(100, Math.round((progress / total) * 100)) : 0;
    return (
      <div className={cn("mt-2 flex items-center gap-2 text-[11px] text-muted-foreground", className)}>
        <Loader2 className="h-3 w-3 animate-spin text-ai" />
        <span>Streaming… {pct}%</span>
        <Button type="button" size="sm" variant="ghost" className="h-6 px-2 text-[11px]" onClick={onStop}>
          <Square className="mr-1 h-3 w-3" /> Stop
        </Button>
      </div>
    );
  }

  if (status === "interrupted") {
    const pct = total > 0 ? Math.min(100, Math.round((progress / total) * 100)) : 0;
    return (
      <div
        role="alert"
        className={cn(
          "mt-3 flex flex-col gap-2 rounded-lg border border-warning/40 bg-warning/5 p-3 text-xs",
          className,
        )}
      >
        <div className="flex items-start gap-2">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" />
          <div className="flex-1">
            <p className="font-medium text-foreground">Response interrupted at {pct}%</p>
            <p className="mt-0.5 text-muted-foreground">{error ?? "The stream ended unexpectedly."}</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" size="sm" variant="default" className="h-7 px-2.5 text-[11px]" onClick={onResume}>
            <Play className="mr-1 h-3 w-3" /> {resumeLabel}
          </Button>
          <Button type="button" size="sm" variant="outline" className="h-7 px-2.5 text-[11px]" onClick={onRetry}>
            <RotateCcw className="mr-1 h-3 w-3" /> Retry from start
          </Button>
        </div>
      </div>
    );
  }

  return null;
}