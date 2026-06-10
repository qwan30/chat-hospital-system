import { Skeleton } from "@/components/ui/skeleton";

export function SkeletonThreadCard() {
  return (
    <div className="p-4 rounded-xl border border-border-subtle space-y-3">
      <div className="flex items-center gap-3"><Skeleton className="h-8 w-8 rounded-full" /><div className="space-y-1.5"><Skeleton className="h-3 w-32" /><Skeleton className="h-2.5 w-20" /></div></div>
      <Skeleton className="h-3 w-full" />
    </div>
  );
}
