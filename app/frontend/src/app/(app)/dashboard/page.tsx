"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { getDashboardSummary, type DashboardSummary } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Clock, DollarSign, FileText, Users, Plus } from "lucide-react";
import { DashboardErrorState } from "@/components/empty/DashboardErrorState";

export default function DashboardPage() {
  const { apiUrl, token } = useAuth();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!apiUrl || !token) return;
    setLoading(true);
    getDashboardSummary({ apiUrl, token })
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [apiUrl, token]);

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-h1 text-text-strong">Dashboard</h1>
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-[120px] rounded-xl" />)}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <DashboardErrorState
          primaryAction={{ label: "Retry", onClick: () => { setError(""); setLoading(true); getDashboardSummary({ apiUrl, token }).then((d) => { setData(d); setLoading(false); }).catch((e) => { setError(e.message); setLoading(false); }); } }}
          secondaryAction={{ label: "View logs", onClick: () => console.log("Logs") }}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[24px] font-bold text-text-strong mb-1">Welcome back, Dr. Chen 👋</h1>
          <p className="text-[14px] text-text-muted">Here's what's happening with your patients today.</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-[13px] font-bold hover:bg-primary-700 transition-colors">
          <Plus className="w-4 h-4" />
          Add Patient
        </button>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <MetricCard icon={Clock} label="Hours Saved" value={`${data?.metrics?.hours_saved || 0}h`} trend="↑" trendColor="text-success-600" />
        <MetricCard icon={DollarSign} label="Cost Saved" value={`$${data?.metrics?.cost_saved_usd || 0}`} trend="↑" trendColor="text-success-600" />
        <MetricCard icon={FileText} label="Documents" value={String(data?.document_stats?.indexed || 0)} detail={`${data?.document_stats?.processing || 0} processing`} />
        <MetricCard icon={Users} label="Patients" value={String(data?.recent_patients?.length || 0)} />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card className="col-span-2">
          <CardHeader><CardTitle className="text-h4">Recent Patients</CardTitle></CardHeader>
          <CardContent>
            {data?.recent_patients?.length ? (
              <div className="space-y-2">
                {data.recent_patients.slice(0, 5).map((p) => (
                  <div key={p.id} className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-bg-surface-tint transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-[12px] font-semibold">
                        {p.full_name?.split(" ").map((n: string) => n[0]).join("").toUpperCase()}
                      </div>
                      <span className="text-body-strong text-text-default">{p.full_name}</span>
                    </div>
                    <span className="text-caption text-text-muted">MRN: {p.mrn}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-caption text-text-muted py-4 text-center">No recent patients</p>
            )}
          </CardContent>
        </Card>
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle className="text-h4">Document Status</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-3">
                <StatusRow label="Indexed" value={data?.document_stats?.indexed || 0} color="bg-success-600" />
                <StatusRow label="Processing" value={data?.document_stats?.processing || 0} color="bg-warning-500" />
                <StatusRow label="Failed" value={data?.document_stats?.failed || 0} color="bg-danger-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-h4">System Health</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-3">
                <StatusRow label="HMS API" value={data?.systems_health?.hms_api === "ok" ? "Online" : "Offline"} color={data?.systems_health?.hms_api === "ok" ? "bg-success-600" : "bg-danger-600"} />
                <StatusRow label="Ollama" value={data?.systems_health?.ollama_inference === "ok" ? "Online" : "Offline"} color={data?.systems_health?.ollama_inference === "ok" ? "bg-success-600" : "bg-danger-600"} />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, trend, trendColor, detail }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string; trend?: string; trendColor?: string; detail?: string }) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-caption text-text-muted">{label}</span>
          <Icon className="w-4 h-4 text-text-subtle" />
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-metric text-text-strong">{value}</span>
          {trend && <span className={`text-[13px] font-semibold ${trendColor || "text-text-muted"}`}>{trend}</span>}
        </div>
        {detail && <p className="text-[11px] text-text-subtle mt-1">{detail}</p>}
      </CardContent>
    </Card>
  );
}

function StatusRow({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${color}`} />
        <span className="text-caption text-text-muted">{label}</span>
      </div>
      <span className="text-caption-strong text-text-default">{value}</span>
    </div>
  );
}
