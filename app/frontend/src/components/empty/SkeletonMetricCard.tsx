import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";

export function SkeletonMetricCard() {
  return (
    <Card><CardContent className="p-5 space-y-3">
      <div className="flex items-center justify-between"><Skeleton className="h-3 w-20" /><Skeleton className="h-4 w-4 rounded" /></div>
      <Skeleton className="h-8 w-16" />
    </CardContent></Card>
  );
}
