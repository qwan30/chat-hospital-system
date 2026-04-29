"use client";

import { useAuth } from "@/lib/auth-context";
import { listPatients, listDocuments, listAuditLogs, hmsHealthCheck, hmsSyncFull, type Patient, type DocumentItem, type AuditEntry, type HmsSyncResult } from "@/lib/api-client";
import { useState, useMemo, useCallback } from "react";

type TabId = "overview" | "patients" | "hms" | "system";

const TAB_LABELS: { id: TabId; label: string; icon: string }[] = [
  { id: "overview", label: "Overview", icon: "📊" },
  { id: "patients", label: "Patients", icon: "🩺" },
  { id: "hms", label: "HMS Sync", icon: "🔗" },
  { id: "system", label: "System", icon: "⚙️" },
];

export default function AdminPage() {
  const { apiUrl, token, user } = useAuth();
  const opts = useMemo(() => ({ apiUrl, token }), [apiUrl, token]);

  const [tab, setTab] = useState<TabId>("overview");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [auditCount, setAuditCount] = useState(0);
  const [recentAudits, setRecentAudits] = useState<AuditEntry[]>([]);
  const [hmsOk, setHmsOk] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchKey, setFetchKey] = useState("");
  const [syncStatus, setSyncStatus] = useState<Record<string, string>>({});

  const currentKey = `${apiUrl}-${token}`;
  if (currentKey !== fetchKey && apiUrl && token) {
    setFetchKey(currentKey);
    setLoading(true);

    Promise.allSettled([
      listPatients(opts),
      listDocuments(opts),
      listAuditLogs(opts),
      hmsHealthCheck(opts),
    ]).then(([pats, docs, audits, health]) => {
      if (pats.status === "fulfilled") setPatients(pats.value);
      if (docs.status === "fulfilled") setDocuments(docs.value);
      if (audits.status === "fulfilled") {
        setAuditCount(audits.value.length);
        setRecentAudits(audits.value.slice(0, 5));
      }
      if (health.status === "fulfilled") setHmsOk(health.value.hms_reachable);
      setLoading(false);
    });
  }

  const handleSync = useCallback(async (patientId: string) => {
    setSyncStatus((prev) => ({ ...prev, [patientId]: "syncing" }));
    try {
      const result: HmsSyncResult = await hmsSyncFull(opts, patientId);
      setSyncStatus((prev) => ({
        ...prev,
        [patientId]: `✓ Synced ${result.synced?.total ?? 0} records`,
      }));
    } catch (err: unknown) {
      setSyncStatus((prev) => ({
        ...prev,
        [patientId]: `✗ ${err instanceof Error ? err.message : "Sync failed"}`,
      }));
    }
  }, [opts]);

  if (user?.role !== "admin" && user?.role !== "security") {
    return (
      <div style={{ padding: "2rem", color: "var(--muted)" }}>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#f87171", marginBottom: 8 }}>
          ⛔ Access Denied
        </h1>
        <p style={{ fontSize: "0.85rem" }}>
          Admin panel requires <code>admin</code> or <code>security</code> role.
        </p>
      </div>
    );
  }

  const cardStyle: React.CSSProperties = {
    padding: "1.25rem 1rem",
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius)",
  };

  return (
    <div style={{ padding: "1.5rem 2rem", maxWidth: 1400 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 600, color: "var(--foreground)", margin: 0 }}>
          🛡️ Admin Panel
        </h1>
        <span style={{
          padding: "2px 8px",
          borderRadius: 12,
          fontSize: "0.72rem",
          fontWeight: 500,
          background: "rgba(168,85,247,0.15)",
          color: "#a855f7",
        }}>
          {user?.role}
        </span>
      </div>

      {/* Tab navigation */}
      <div style={{
        display: "flex",
        gap: 4,
        borderBottom: "1px solid var(--border)",
        marginBottom: "1.5rem",
      }}>
        {TAB_LABELS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              padding: "0.6rem 1rem",
              background: tab === t.id ? "var(--surface-elevated)" : "transparent",
              border: "none",
              borderBottom: tab === t.id ? "2px solid var(--brand)" : "2px solid transparent",
              color: tab === t.id ? "var(--foreground)" : "var(--muted)",
              cursor: "pointer",
              fontSize: "0.85rem",
              fontWeight: tab === t.id ? 500 : 400,
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Loading admin data…</div>
      ) : (
        <>
          {/* ─── Overview Tab ─── */}
          {tab === "overview" && (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: "2rem" }}>
                <div style={cardStyle}>
                  <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginBottom: "0.5rem" }}>👥 Patients</div>
                  <div style={{ fontSize: "1.5rem", fontWeight: 600, color: "#60a5fa" }}>{patients.length}</div>
                </div>
                <div style={cardStyle}>
                  <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginBottom: "0.5rem" }}>📄 Documents</div>
                  <div style={{ fontSize: "1.5rem", fontWeight: 600, color: "#34d399" }}>{documents.length}</div>
                </div>
                <div style={cardStyle}>
                  <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginBottom: "0.5rem" }}>🔒 Audit Events</div>
                  <div style={{ fontSize: "1.5rem", fontWeight: 600, color: "#a78bfa" }}>{auditCount}</div>
                </div>
                <div style={cardStyle}>
                  <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginBottom: "0.5rem" }}>🔗 HMS Status</div>
                  <div style={{ fontSize: "1.5rem", fontWeight: 600, color: hmsOk ? "#34d399" : "#f87171" }}>
                    {hmsOk === null ? "—" : hmsOk ? "Online" : "Offline"}
                  </div>
                </div>
              </div>

              {/* Recent activity */}
              <h2 style={{ fontSize: "1rem", fontWeight: 500, color: "var(--foreground)", marginBottom: "0.75rem" }}>
                Recent Audit Activity
              </h2>
              <div style={{ ...cardStyle, overflow: "hidden", padding: 0 }}>
                {recentAudits.length === 0 ? (
                  <div style={{ padding: "2rem", textAlign: "center", color: "var(--muted)", fontSize: "0.85rem" }}>
                    No audit events yet.
                  </div>
                ) : (
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid var(--border)" }}>
                        {["Action", "Object", "Outcome", "Time"].map((h) => (
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

          {/* ─── Patients Tab ─── */}
          {tab === "patients" && (
            <div style={{ ...cardStyle, overflow: "hidden", padding: 0 }}>
              {patients.length === 0 ? (
                <div style={{ padding: "2rem", textAlign: "center", color: "var(--muted)", fontSize: "0.85rem" }}>
                  No patients found.
                </div>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      {["MRN", "Name", "DOB", "Department", "Patient ID"].map((h) => (
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
                    {patients.map((p) => (
                      <tr key={p.id} style={{ borderBottom: "1px solid var(--border)" }}>
                        <td style={{ padding: "0.5rem 0.75rem", color: "var(--foreground)", fontFamily: "monospace", fontSize: "0.8rem" }}>
                          {p.mrn}
                        </td>
                        <td style={{ padding: "0.5rem 0.75rem", color: "var(--foreground)", fontWeight: 500 }}>
                          {p.full_name}
                        </td>
                        <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)" }}>
                          {p.dob || "—"}
                        </td>
                        <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)" }}>
                          {p.department || "—"}
                        </td>
                        <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)", fontFamily: "monospace", fontSize: "0.72rem" }}>
                          {p.id.substring(0, 8)}…
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* ─── HMS Sync Tab ─── */}
          {tab === "hms" && (
            <>
              <div style={{ ...cardStyle, marginBottom: "1.5rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: "0.5rem" }}>
                  <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>HMS Connection:</span>
                  <span style={{
                    padding: "2px 10px",
                    borderRadius: 12,
                    fontSize: "0.75rem",
                    fontWeight: 500,
                    background: hmsOk ? "rgba(52,211,153,0.15)" : "rgba(248,113,113,0.15)",
                    color: hmsOk ? "#34d399" : "#f87171",
                  }}>
                    {hmsOk === null ? "Unknown" : hmsOk ? "Connected" : "Unreachable"}
                  </span>
                </div>
                <p style={{ fontSize: "0.8rem", color: "var(--muted)", margin: 0 }}>
                  Sync clinical data from the Hospital Management System. Each sync fetches appointments, lab results, and medical records.
                </p>
              </div>

              <h2 style={{ fontSize: "1rem", fontWeight: 500, color: "var(--foreground)", marginBottom: "0.75rem" }}>
                Sync by Patient
              </h2>
              <div style={{ ...cardStyle, overflow: "hidden", padding: 0 }}>
                {patients.length === 0 ? (
                  <div style={{ padding: "2rem", textAlign: "center", color: "var(--muted)", fontSize: "0.85rem" }}>
                    No patients available for sync.
                  </div>
                ) : (
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid var(--border)" }}>
                        {["Patient", "MRN", "Status", "Action"].map((h) => (
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
                      {patients.map((p) => (
                        <tr key={p.id} style={{ borderBottom: "1px solid var(--border)" }}>
                          <td style={{ padding: "0.5rem 0.75rem", color: "var(--foreground)", fontWeight: 500 }}>
                            {p.full_name}
                          </td>
                          <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)", fontFamily: "monospace", fontSize: "0.8rem" }}>
                            {p.mrn}
                          </td>
                          <td style={{ padding: "0.5rem 0.75rem", color: "var(--muted)", fontSize: "0.8rem" }}>
                            {syncStatus[p.id] || "Ready"}
                          </td>
                          <td style={{ padding: "0.5rem 0.75rem" }}>
                            <button
                              onClick={() => handleSync(p.id)}
                              disabled={syncStatus[p.id] === "syncing"}
                              style={{
                                padding: "0.3rem 0.6rem",
                                fontSize: "0.75rem",
                                background: syncStatus[p.id] === "syncing" ? "var(--surface-elevated)" : "var(--brand)",
                                color: "white",
                                border: "none",
                                borderRadius: "var(--radius)",
                                cursor: syncStatus[p.id] === "syncing" ? "not-allowed" : "pointer",
                                opacity: syncStatus[p.id] === "syncing" ? 0.6 : 1,
                              }}
                            >
                              {syncStatus[p.id] === "syncing" ? "Syncing…" : "Sync Now"}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          )}

          {/* ─── System Tab ─── */}
          {tab === "system" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div style={cardStyle}>
                <h3 style={{ fontSize: "0.85rem", fontWeight: 500, color: "var(--foreground)", margin: "0 0 0.75rem 0" }}>
                  Environment
                </h3>
                <div style={{ display: "grid", gap: "0.5rem", fontSize: "0.82rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "var(--muted)" }}>API Base URL</span>
                    <span style={{ color: "var(--foreground)", fontFamily: "monospace", fontSize: "0.75rem" }}>{apiUrl}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "var(--muted)" }}>Auth Mode</span>
                    <span style={{ color: "var(--foreground)" }}>Bearer Token (Dev)</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "var(--muted)" }}>Current User</span>
                    <span style={{ color: "var(--foreground)" }}>{user?.full_name || "—"}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "var(--muted)" }}>Role</span>
                    <span style={{
                      padding: "1px 6px",
                      borderRadius: 8,
                      fontSize: "0.72rem",
                      background: "rgba(168,85,247,0.15)",
                      color: "#a855f7",
                    }}>
                      {user?.role || "—"}
                    </span>
                  </div>
                </div>
              </div>

              <div style={cardStyle}>
                <h3 style={{ fontSize: "0.85rem", fontWeight: 500, color: "var(--foreground)", margin: "0 0 0.75rem 0" }}>
                  Data Summary
                </h3>
                <div style={{ display: "grid", gap: "0.5rem", fontSize: "0.82rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "var(--muted)" }}>Total Patients</span>
                    <span style={{ color: "var(--foreground)" }}>{patients.length}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "var(--muted)" }}>Total Documents</span>
                    <span style={{ color: "var(--foreground)" }}>{documents.length}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "var(--muted)" }}>Indexed Documents</span>
                    <span style={{ color: "var(--foreground)" }}>
                      {documents.filter((d) => d.status === "indexed").length}
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "var(--muted)" }}>HMS Documents</span>
                    <span style={{ color: "var(--foreground)" }}>
                      {documents.filter((d) => d.document_type.startsWith("hms_")).length}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
