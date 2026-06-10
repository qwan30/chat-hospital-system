import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function BarVolumeChart({ title = "Queries by Department" }: { title?: string }) {
  return (
    <Card><CardHeader><CardTitle className="text-h4">{title}</CardTitle></CardHeader>
      <CardContent><div className="h-[200px] bg-bg-surface-tint rounded-xl border border-border-subtle flex items-center justify-center"><p className="text-[13px] text-text-muted">Chart: Bar chart by department</p></div></CardContent>
    </Card>
  );
}
