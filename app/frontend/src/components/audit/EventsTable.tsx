import { Badge } from "@/components/ui/badge";

interface AuditEvent { id: string; timestamp: string; user: string; role: string; patient: string; action: string; resource: string; outcome: string; }

interface EventsTableProps { events: AuditEvent[]; onRowClick?: (event: AuditEvent) => void; }

export function EventsTable({ events, onRowClick }: EventsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead><tr className="border-b border-border-subtle">
          {["Timestamp", "User", "Role", "Patient", "Action", "Resource", "Outcome"].map((h) => <th key={h} className="text-left py-3 px-3 text-[12px] font-semibold text-text-muted">{h}</th>)}
        </tr></thead>
        <tbody>
          {events.map((e) => (
            <tr key={e.id} onClick={() => onRowClick?.(e)} className="border-b border-border-subtle hover:bg-bg-surface-tint transition-colors cursor-pointer">
              <td className="py-3 px-3 text-[12px] text-text-muted font-mono">{e.timestamp}</td>
              <td className="py-3 px-3 text-[13px] text-text-default font-medium">{e.user}</td>
              <td className="py-3 px-3 text-[12px] text-text-muted">{e.role}</td>
              <td className="py-3 px-3 text-[13px] text-text-default">{e.patient}</td>
              <td className="py-3 px-3 text-[13px] text-text-default">{e.action}</td>
              <td className="py-3 px-3 text-[12px] text-text-muted">{e.resource}</td>
              <td className="py-3 px-3"><Badge variant="outline" className={e.outcome === "allowed" ? "bg-success-50 text-success-600" : "bg-danger-50 text-danger-600"}>{e.outcome}</Badge></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
