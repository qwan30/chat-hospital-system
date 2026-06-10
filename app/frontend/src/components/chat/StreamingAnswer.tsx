import { Skeleton } from "@/components/ui/skeleton";
import { Sparkles } from "lucide-react";

export function StreamingAnswer() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-lg bg-primary-100 flex items-center justify-center flex-shrink-0 mt-1">
        <Sparkles className="w-4 h-4 text-primary-600 animate-pulse" />
      </div>
      <div className="flex-1 space-y-3 max-w-[75%]">
        <div className="p-4 bg-bg-surface rounded-xl border border-border-subtle space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-11/12" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-5/6" />
        </div>
        <p className="text-[11px] text-text-subtle">Generating response...</p>
      </div>
    </div>
  );
}
