import { Skeleton } from "@/components/ui/skeleton";
import { Loader2 } from "lucide-react";

export function CitationLoading() {
  return (
    <div className="space-y-3 p-3">
      <div className="flex items-center gap-2 text-[12px] text-text-muted">
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
        Retrieving evidence...
      </div>
      <Skeleton className="h-[72px] w-full rounded-lg" />
      <Skeleton className="h-[72px] w-full rounded-lg" />
      <Skeleton className="h-[72px] w-11/12 rounded-lg" />
    </div>
  );
}
