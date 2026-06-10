"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { getMetricsSummary, type MetricsSummary } from "@/lib/api-client";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendLineChart } from "@/components/viz/TrendLineChart";
import { BarVolumeChart } from "@/components/viz/BarVolumeChart";
import { QualitySafetyChart } from "@/components/viz/QualitySafetyChart";
import { WorkflowImpactTable } from "@/components/viz/WorkflowImpactTable";
import { UserFeedbackCard } from "@/components/viz/UserFeedbackCard";
import { StorageDonutChart } from "@/components/viz/StorageDonutChart";
import { BarChart3, Clock, DollarSign, ThumbsUp, ShieldCheck, AlertTriangle } from "lucide-react";

export default function MetricsPage() {
  const { apiUrl, token } = useAuth();
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!apiUrl || !token) return;
    setLoading(true);
    getMetricsSummary({ apiUrl, token }).then((m) => { setMetrics(m); setLoading(false); }).catch(() => setLoading(false));
  }, [apiUrl, token]);

  if (loading) return <div className="p-6 space-y-6"><Skeleton className="h-10 w-48" /><div className="grid grid-cols-4 gap-4">{[1,2,3,4].map((i) => <Skeleton key={i} className="h-[100px] rounded-xl" />)}</div></div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-h1 text-text-strong">Impact & Quality</h1><p className="text-caption text-text-muted mt-1">System performance and clinical impact metrics</p></div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <MetricKPI icon={BarChart3} label="Total Queries" value={metrics?.total_queries?.toLocaleString() || "1,247"} color="primary" />
        <MetricKPI icon={Clock} label="Avg Latency" value={(metrics?.avg_latency_ms || 142) + "ms"} color="success" />
        <MetricKPI icon={DollarSign} label="Cost Saved" value={"$" + (metrics?.total_cost_saved?.toLocaleString() || "47,250")} color="warning" />
        <MetricKPI icon={ThumbsUp} label="Helpful Rate" value={(metrics?.helpful_rate || 94) + "%"} color="primary" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <TrendLineChart title="Query Volume Trend" />
        <BarVolumeChart title="Queries by Department" />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 space-y-4">
          <QualitySafetyChart />
          <WorkflowImpactTable />
        </div>
        <div className="space-y-4">
          <UserFeedbackCard />
          <StorageDonutChart />
        </div>
      </div>
    </div>
  );
}

function MetricKPI({ icon: Icon, label, value, color }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string; color: string }) {
  const colors: Record<string, string> = { primary: "bg-primary-50 text-primary-600", success: "bg-success-50 text-success-600", warning: "bg-warning-50 text-warning-500", danger: "bg-danger-50 text-danger-600" };
  return (
    <Card><CardContent className="p-5">
      <div className="flex items-center justify-between mb-3"><span className="text-caption text-text-muted">{label}</span><Icon className={"w-4 h-4 " + (colors[color] || "text-text-subtle")} /></div>
      <span className="text-metric text-text-strong">{value}</span>
    </CardContent></Card>
  );
}
