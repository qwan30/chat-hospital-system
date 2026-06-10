import { Skeleton } from "@/components/ui/skeleton";

export function SkeletonCitationCard() {
  return (
    <div className="p-3 rounded-lg border border-border-subtle space-y-2">
      <div className="flex items-center justify-between"><Skeleton className="h-3 w-28" /><Skeleton className="h-4 w-10 rounded" /></div>
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-2.5 w-16" />
    </div>
  );
}
