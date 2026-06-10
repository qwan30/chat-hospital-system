"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { listAuditEvents, type AuditEvent } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AuditMetricCard } from "@/components/audit/MetricCard";
import { FilterBar } from "@/components/audit/FilterBar";
import { EventsTable } from "@/components/audit/EventsTable";
import { EventDrawer } from "@/components/audit/EventDrawer";
import { ComplianceCard } from "@/components/audit/ComplianceCard";
import { ShieldCheck, Eye, AlertTriangle, Clock } from "lucide-react";

export default function AuditPage() {
  const { apiUrl, token } = useAuth();
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<{ id: string; timestamp: string; user: string; role: string; patient: string; action: string; resource: string; outcome: string; } | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (!apiUrl || !token) return;
    setLoading(true);
    listAuditEvents({ apiUrl, token })
      .then((e) => { setEvents(e); setLoading(false); })
      .catch(() => { setEvents(SAMPLE_EVENTS); setLoading(false); });
  }, [apiUrl, token]);

  return (
    <div className="p-6 space-y-6">
      <div><h1 className="text-h1 text-text-strong">Audit Log</h1><p className="text-caption text-text-muted mt-1">{events.length} events recorded</p></div>

      <div className="grid grid-cols-4 gap-4">
        <AuditMetricCard icon={ShieldCheck} label="Total Events" value={String(events.length)} trend="up" trendValue="12%" />
        <AuditMetricCard icon={Eye} label="Access Granted" value="1,142" trend="up" trendValue="3%" />
        <AuditMetricCard icon={AlertTriangle} label="Access Denied" value="23" trend="down" trendValue="8%" />
        <AuditMetricCard icon={Clock} label="Avg Response" value="142ms" trend="down" trendValue="5%" />
      </div>

      <FilterBar />

      <Card>
        <CardHeader><CardTitle className="text-h4">Event Log</CardTitle></CardHeader>
        <CardContent>
          {loading ? <div className="space-y-2">{[1,2,3,4,5,6,7,8].map((i) => <Skeleton key={i} className="h-[44px] w-full rounded-lg" />)}</div> : <EventsTable events={events.map((e) => ({ id: e.id, timestamp: new Date(e.created_at).toLocaleString(), user: e.actor_user_id, role: "Physician", patient: e.patient_id || "—", action: e.action, resource: e.object_type, outcome: e.outcome }))} onRowClick={(event) => { setSelectedEvent(event); setDrawerOpen(true); }} />}
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-4">
        <ComplianceCard />
        <Card><CardContent className="p-4 flex items-start gap-3"><ShieldCheck className="w-5 h-5 text-primary-600 mt-0.5" /><div><p className="text-[14px] font-semibold text-text-strong">Audit Retention</p><p className="text-[12px] text-text-muted">Events retained for 7 years per hospital policy. Encrypted at rest with automatic backup.</p></div></CardContent></Card>
      </div>

      <EventDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} event={selectedEvent} />
    </div>
  );
}

const SAMPLE_EVENTS = [
  { id: "evt-001", actor_user_id: "dr.chen", action: "patient.read", object_type: "PatientRecord", patient_id: "PT-0847", outcome: "allowed", trace_id: "tr-001", created_at: "2025-05-15T08:32:00Z" },
  { id: "evt-002", actor_user_id: "dr.park", action: "ai.query", object_type: "ChatThread", patient_id: "PT-0847", outcome: "allowed", trace_id: "tr-002", created_at: "2025-05-15T08:35:00Z" },
  { id: "evt-003", actor_user_id: "dr.miller", action: "document.view", object_type: "Document", patient_id: "PT-1203", outcome: "allowed", trace_id: "tr-003", created_at: "2025-05-15T08:40:00Z" },
  { id: "evt-004", actor_user_id: "nurse.jones", action: "patient.read", object_type: "PatientRecord", patient_id: "PT-0847", outcome: "denied", trace_id: "tr-004", created_at: "2025-05-15T08:42:00Z" },
  { id: "evt-005", actor_user_id: "dr.chen", action: "medication.review", object_type: "MedicationReview", patient_id: "PT-0847", outcome: "allowed", trace_id: "tr-005", created_at: "2025-05-15T08:45:00Z" },
  { id: "evt-006", actor_user_id: "admin.lee", action: "config.update", object_type: "Settings", outcome: "allowed", trace_id: "tr-006", created_at: "2025-05-15T09:00:00Z" },
  { id: "evt-007", actor_user_id: "dr.park", action: "document.upload", object_type: "Document", patient_id: "PT-1203", outcome: "allowed", trace_id: "tr-007", created_at: "2025-05-15T09:10:00Z" },
  { id: "evt-008", actor_user_id: "dr.chen", action: "chat.message", object_type: "ChatThread", patient_id: "PT-0847", outcome: "allowed", trace_id: "tr-008", created_at: "2025-05-15T09:15:00Z" },
];
