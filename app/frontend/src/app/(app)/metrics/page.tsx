"use client";

import { useAuth } from "@/lib/auth-context";
import {
  getMetricsSummary,
  hmsHealthCheck,
  listAuditLogs,
  type AuditEntry,
  type MetricsSummary,
} from "@/lib/api-client";
import { useState, useMemo } from "react";

export default function MetricsPage() {
  const { apiUrl, token } = useAuth();
  const opts = useMemo(() => ({ apiUrl, token }), [apiUrl, token]);

  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [hmsOk, setHmsOk] = useState<boolean | null>(null);
  const [recentAudits, setRecentAudits] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchKey, setFetchKey] = useState("");

  const currentKey = `${apiUrl}-${token}`;
  if (currentKey !== fetchKey && apiUrl && token) {
    setFetchKey(currentKey);
    setLoading(true);

    Promise.allSettled([
      getMetricsSummary(opts),
      listAuditLogs(opts),
      hmsHealthCheck(opts),
    ]).then(([summary, audits, health]) => {
      if (summary.status === "fulfilled") setMetrics(summary.value);
      if (audits.status === "fulfilled") {
        setRecentAudits(audits.value.slice(0, 10));
      }
      if (health.status === "fulfilled") setHmsOk(health.value.hms_reachable);
      setLoading(false);
    });
  }

  const cards = [
    { label: "Queries", value: metrics?.total_queries ?? 0, icon: "💬", color: "#60a5fa" },
    {
      label: "Avg Latency",
      value: `${Math.round(metrics?.avg_latency_ms ?? 0)} ms`,
      icon: "⏱️",
      color: "#34d399",
    },
    {
      label: "Time Saved",
      value: `${Math.round((metrics?.total_time_saved_sec ?? 0) / 60)} min`,
      icon: "⏳",
      color: "#f59e0b",
    },
    {
      label: "Cost Saved",
      value: `$${(metrics?.total_cost_saved ?? 0).toFixed(2)}`,
      icon: "💵",
      color: "#22c55e",
    },
    {
      label: "Helpful Rate",
      value: `${Math.round((metrics?.helpful_rate ?? 0) * 100)}%`,
      icon: "👍",
      color: "#a78bfa",
    },
    {
      label: "No Evidence",
      value: `${Math.round((metrics?.no_evidence_rate ?? 0) * 100)}%`,
      icon: "🧭",
      color: "#f87171",
    },
    { label: "Denied Events", value: metrics?.audit_deny_count ?? 0, icon: "🔒", color: "#fb7185" },
    {
      label: "HMS Connection",
      value: hmsOk === null ? "—" : hmsOk ? "Connected" : "Unreachable",
      icon: "🔗",
      color: hmsOk ? "#34d399" : "#f87171",
    },
  ];

  return (
    <div style={{ padding: "1.5rem 2rem", maxWidth: 1200 }}>
      <h1 style={{ fontSize: "1.25rem", fontWeight: 600, margin: "0 0 1.5rem 0", color: "var(--foreground)" }}>
        📊 Metrics Dashboard
      </h1>

      {loading ? (
        <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Loading metrics…</div>
      ) : (
        <>
          {/* Stat cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: "2rem" }}>
            {cards.map((card) => (
              <div key={card.label} style={{
                padding: "1.25rem 1rem",
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius)",
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: "0.75rem" }}>
                  <span style={{ fontSize: "1.25rem" }}>{card.icon}</span>
                  <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{card.label}</span>
                </div>
                <div style={{ fontSize: "1.5rem", fontWeight: 600, color: card.color }}>
                  {card.value}
                </div>
              </div>
            ))}
          </div>

          {/* Recent audit activity */}
          <h2 style={{ fontSize: "1rem", fontWeight: 500, color: "var(--foreground)", marginBottom: "0.75rem" }}>
            Recent Activity
          </h2>
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            overflow: "hidden",
          }}>
            {recentAudits.length === 0 ? (
              <div style={{ padding: "2rem", textAlign: "center", color: "var(--muted)", fontSize: "0.85rem" }}>
                No audit events yet.
              </div>
            ) : (
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border)" }}>
                    {["Action", "Object", "Outcome", "Patient", "Trace ID", "Time"].map((h) => (
                      <th key={h} style={{
                        padding: "0.6rem 0.75rem",
                        textAlign: "left",
                        fontWeight: 500,
                        color: "var(--muted)",
                        fontSize: "0.72rem",
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                      }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {recentAudits.map((a) => (
                    <tr key={a.id} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "0.5rem 0.75rem", color: "var(--foreground)" }}>{a.action}</td>
                      <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)" }}>{a.object_type}</td>
                      <td style={{ padding: "0.5rem 0.75rem" }}>
                        <span style={{
                          padding: "2px 8px",
                          borderRadius: 12,
                          fontSize: "0.72rem",
                          fontWeight: 500,
                          background: a.outcome === "allowed" ? "rgba(52,211,153,0.15)" : "rgba(248,113,113,0.15)",
                          color: a.outcome === "allowed" ? "#34d399" : "#f87171",
                        }}>
                          {a.outcome}
                        </span>
                      </td>
                      <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)", fontFamily: "monospace", fontSize: "0.72rem" }}>
                        {a.patient_id ? a.patient_id.substring(0, 8) + "…" : "—"}
                      </td>
                      <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)", fontFamily: "monospace", fontSize: "0.72rem" }}>
                        {a.trace_id.substring(0, 8)}…
                      </td>
                      <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)", fontSize: "0.75rem" }}>
                        {new Date(a.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
}
