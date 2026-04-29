"use client";

import { useAuth } from "@/lib/auth-context";
import { listAuditLogs, type AuditEntry } from "@/lib/api-client";
import { useState, useMemo } from "react";

export default function AuditLogPage() {
  const { apiUrl, token } = useAuth();
  const opts = useMemo(() => ({ apiUrl, token }), [apiUrl, token]);

  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterAction, setFilterAction] = useState("");
  const [filterOutcome, setFilterOutcome] = useState("");
  const [fetchKey, setFetchKey] = useState("");

  const currentKey = `${apiUrl}-${token}-${filterAction}-${filterOutcome}`;

  if (currentKey !== fetchKey && apiUrl && token) {
    setFetchKey(currentKey);
    setLoading(true);
    const params: Record<string, string> = {};
    if (filterAction) params.action = filterAction;
    if (filterOutcome) params.outcome = filterOutcome;
    listAuditLogs(opts, Object.keys(params).length > 0 ? params : undefined)
      .then((data) => {
        setLogs(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }

  function handleRefresh() {
    // Reset fetchKey to force a reload on next render
    setFetchKey("");
  }

  return (
    <div style={{ padding: "1.5rem 2rem", maxWidth: 1400 }}>
      <h1 style={{ fontSize: "1.25rem", fontWeight: 600, margin: "0 0 1.5rem 0", color: "var(--foreground)" }}>
        🔒 Audit Log
      </h1>

      {/* Filters */}
      <div style={{ display: "flex", gap: 12, marginBottom: "1rem" }}>
        <input
          type="text"
          placeholder="Filter by action…"
          value={filterAction}
          onChange={(e) => setFilterAction(e.target.value)}
          style={{
            padding: "0.5rem 0.75rem",
            background: "var(--surface-elevated)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            color: "var(--foreground)",
            fontSize: "0.85rem",
            minWidth: 220,
          }}
        />
        <select
          value={filterOutcome}
          onChange={(e) => setFilterOutcome(e.target.value)}
          style={{
            padding: "0.5rem 0.75rem",
            background: "var(--surface-elevated)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            color: "var(--foreground)",
            fontSize: "0.85rem",
          }}
        >
          <option value="">All outcomes</option>
          <option value="allowed">Allowed</option>
          <option value="denied">Denied</option>
        </select>
        <button
          onClick={handleRefresh}
          style={{
            padding: "0.5rem 0.75rem",
            background: "var(--surface-elevated)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            color: "var(--foreground)",
            fontSize: "0.85rem",
            cursor: "pointer",
          }}
        >
          Refresh
        </button>
      </div>

      {/* Log table */}
      <div style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius)",
        overflow: "hidden",
      }}>
        {loading ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--muted)", fontSize: "0.85rem" }}>
            Loading audit logs…
          </div>
        ) : logs.length === 0 ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--muted)", fontSize: "0.85rem" }}>
            No audit entries match the current filters.
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                {["Time", "User", "Action", "Object Type", "Object ID", "Patient ID", "Outcome", "Trace ID"].map((h) => (
                  <th key={h} style={{
                    padding: "0.6rem 0.75rem",
                    textAlign: "left",
                    fontWeight: 500,
                    color: "var(--muted)",
                    fontSize: "0.72rem",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    whiteSpace: "nowrap",
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {logs.map((entry) => (
                <tr key={entry.id} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)", whiteSpace: "nowrap", fontSize: "0.75rem" }}>
                    {new Date(entry.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: "0.5rem 0.75rem", color: "var(--foreground)", fontFamily: "monospace", fontSize: "0.72rem" }}>
                    {entry.actor_user_id?.substring(0, 8) || "—"}…
                  </td>
                  <td style={{ padding: "0.5rem 0.75rem", color: "var(--foreground)" }}>{entry.action}</td>
                  <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)" }}>{entry.object_type}</td>
                  <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)", fontFamily: "monospace", fontSize: "0.72rem" }}>
                    {entry.object_id ? entry.object_id.substring(0, 8) + "…" : "—"}
                  </td>
                  <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)", fontFamily: "monospace", fontSize: "0.72rem" }}>
                    {entry.patient_id ? entry.patient_id.substring(0, 8) + "…" : "—"}
                  </td>
                  <td style={{ padding: "0.5rem 0.75rem" }}>
                    <span style={{
                      padding: "2px 8px",
                      borderRadius: 12,
                      fontSize: "0.72rem",
                      fontWeight: 500,
                      background: entry.outcome === "allowed" ? "rgba(52,211,153,0.15)" : "rgba(248,113,113,0.15)",
                      color: entry.outcome === "allowed" ? "#34d399" : "#f87171",
                    }}>
                      {entry.outcome}
                    </span>
                  </td>
                  <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)", fontFamily: "monospace", fontSize: "0.72rem" }}>
                    {entry.trace_id.substring(0, 8)}…
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div style={{ marginTop: "0.75rem", fontSize: "0.75rem", color: "var(--muted)" }}>
        {logs.length} entries
      </div>
    </div>
  );
}
