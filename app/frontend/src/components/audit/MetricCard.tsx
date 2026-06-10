import { Card, CardContent } from "@/components/ui/card";
import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";

interface AuditMetricCardProps { icon: LucideIcon; label: string; value: string; trend?: "up" | "down"; trendValue?: string; }

export function AuditMetricCard({ icon: Icon, label, value, trend, trendValue }: AuditMetricCardProps) {
  return (
    <Card><CardContent className="p-5">
      <div className="flex items-center justify-between mb-3"><span className="text-caption text-text-muted">{label}</span><Icon className="w-4 h-4 text-text-subtle" /></div>
      <div className="flex items-baseline gap-2"><span className="text-metric text-text-strong">{value}</span>
        {trend && <span className={"text-[12px] font-semibold flex items-center gap-0.5 " + (trend === "up" ? "text-success-600" : "text-danger-600")}>{trend === "up" ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}{trendValue}</span>}
      </div>
    </CardContent></Card>
  );
}
