import { Skeleton } from "@/components/ui/skeleton";

export function SkeletonTableRow({ cols = 6 }: { cols?: number }) {
  return (
    <div className="flex items-center gap-4 py-3 px-3 border-b border-border-subtle">
      {Array.from({ length: cols }, (_, i) => <Skeleton key={i} className="h-3 flex-1" />)}
    </div>
  );
}
