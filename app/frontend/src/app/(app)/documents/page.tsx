"use client";

import { useAuth } from "@/lib/auth-context";
import { listDocuments, listPatients, uploadDocument, hmsSyncFull, type DocumentItem, type Patient, type HmsSyncResult } from "@/lib/api-client";
import { useState, useMemo, useSyncExternalStore } from "react";

type SyncStatus = { loading: boolean; result?: HmsSyncResult; error?: string };

/** Minimal subscribe/snapshot for triggering a data reload. */
let reloadGeneration = 0;
const reloadListeners = new Set<() => void>();
function subscribeReload(cb: () => void) {
  reloadListeners.add(cb);
  return () => { reloadListeners.delete(cb); };
}
function getReloadSnapshot() { return reloadGeneration; }
function triggerReload() {
  reloadGeneration++;
  reloadListeners.forEach((cb) => cb());
}

export default function DocumentsPage() {
  const { apiUrl, token } = useAuth();
  const opts = useMemo(() => ({ apiUrl, token }), [apiUrl, token]);

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [patientsLoaded, setPatientsLoaded] = useState(false);

  // Upload state
  const [showUpload, setShowUpload] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadPatientId, setUploadPatientId] = useState("");
  const [uploading, setUploading] = useState(false);

  // HMS sync state
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({ loading: false });

  // Use useSyncExternalStore to drive reloads from a generation counter.
  const generation = useSyncExternalStore(subscribeReload, getReloadSnapshot, getReloadSnapshot);

  // Fetch documents reactively (triggered by generation, selectedPatient, or opts change).
  // Using a "fetch during render" pattern that React 18+ supports via useState + key.
  const fetchKey = `${generation}-${selectedPatient}-${apiUrl}-${token}`;
  const [lastFetchKey, setLastFetchKey] = useState("");

  if (fetchKey !== lastFetchKey && apiUrl && token) {
    setLastFetchKey(fetchKey);
    setLoading(true);
    setError("");
    listDocuments(opts, selectedPatient || undefined)
      .then((docs) => {
        setDocuments(docs);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load documents");
        setLoading(false);
      });

    if (!patientsLoaded) {
      setPatientsLoaded(true);
      listPatients(opts).then(setPatients).catch(() => {});
    }
  }

  async function handleUpload() {
    if (!uploadFile || !uploadPatientId) return;
    setUploading(true);
    try {
      await uploadDocument(opts, {
        patient_id: uploadPatientId,
        file: uploadFile,
        title: uploadTitle || uploadFile.name,
      });
      setShowUpload(false);
      setUploadFile(null);
      setUploadTitle("");
      triggerReload();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleHmsSync() {
    if (!selectedPatient) return;
    setSyncStatus({ loading: true });
    try {
      const result = await hmsSyncFull(opts, selectedPatient);
      setSyncStatus({ loading: false, result });
      triggerReload();
    } catch (err: unknown) {
      setSyncStatus({ loading: false, error: err instanceof Error ? err.message : "Sync failed" });
    }
  }

  const statusColor: Record<string, string> = {
    indexed: "#34d399",
    uploaded: "#60a5fa",
    processing: "#fbbf24",
    failed: "#f87171",
  };

  return (
    <div style={{ padding: "1.5rem 2rem", maxWidth: 1200 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 600, margin: 0, color: "var(--foreground)" }}>
          📄 Documents
        </h1>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={handleHmsSync}
            disabled={!selectedPatient || syncStatus.loading}
            style={{
              padding: "0.5rem 1rem",
              fontSize: "0.8rem",
              background: "var(--surface-elevated)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              color: selectedPatient ? "var(--foreground)" : "var(--muted)",
              cursor: selectedPatient ? "pointer" : "not-allowed",
            }}
          >
            {syncStatus.loading ? "Syncing…" : "🔄 Sync from HMS"}
          </button>
          <button
            onClick={() => setShowUpload(!showUpload)}
            style={{
              padding: "0.5rem 1rem",
              fontSize: "0.8rem",
              background: "var(--brand)",
              border: "none",
              borderRadius: "var(--radius)",
              color: "#fff",
              cursor: "pointer",
            }}
          >
            ＋ Upload
          </button>
        </div>
      </div>

      {/* Sync feedback */}
      {syncStatus.result && (
        <div style={{
          padding: "0.6rem 1rem",
          borderRadius: "var(--radius)",
          background: "rgba(52,211,153,0.1)",
          border: "1px solid rgba(52,211,153,0.2)",
          color: "#34d399",
          fontSize: "0.8rem",
          marginBottom: "1rem",
        }}>
          ✓ {syncStatus.result.message}
        </div>
      )}
      {syncStatus.error && (
        <div style={{
          padding: "0.6rem 1rem",
          borderRadius: "var(--radius)",
          background: "rgba(248,113,113,0.1)",
          border: "1px solid rgba(248,113,113,0.2)",
          color: "#f87171",
          fontSize: "0.8rem",
          marginBottom: "1rem",
        }}>
          ✗ {syncStatus.error}
        </div>
      )}

      {/* Patient filter */}
      <div style={{ marginBottom: "1rem" }}>
        <select
          value={selectedPatient}
          onChange={(e) => setSelectedPatient(e.target.value)}
          style={{
            padding: "0.5rem 0.75rem",
            background: "var(--surface-elevated)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            color: "var(--foreground)",
            fontSize: "0.85rem",
            minWidth: 260,
          }}
        >
          <option value="">All patients</option>
          {patients.map((p) => (
            <option key={p.id} value={p.id}>{p.full_name} ({p.mrn})</option>
          ))}
        </select>
      </div>

      {/* Upload dialog */}
      {showUpload && (
        <div style={{
          padding: "1.25rem",
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          marginBottom: "1.25rem",
        }}>
          <h3 style={{ fontSize: "0.95rem", fontWeight: 500, margin: "0 0 1rem 0", color: "var(--foreground)" }}>
            Upload Document
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
            <label style={{ display: "block" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--muted)", display: "block", marginBottom: 4 }}>Patient</span>
              <select
                value={uploadPatientId}
                onChange={(e) => setUploadPatientId(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  background: "var(--surface-elevated)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius)",
                  color: "var(--foreground)",
                  fontSize: "0.85rem",
                }}
              >
                <option value="">Select patient…</option>
                {patients.map((p) => (
                  <option key={p.id} value={p.id}>{p.full_name}</option>
                ))}
              </select>
            </label>
            <label style={{ display: "block" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--muted)", display: "block", marginBottom: 4 }}>Title</span>
              <input
                type="text"
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                placeholder="Document title"
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  background: "var(--surface-elevated)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius)",
                  color: "var(--foreground)",
                  fontSize: "0.85rem",
                }}
              />
            </label>
          </div>
          <label style={{ display: "block", marginBottom: 12 }}>
            <span style={{ fontSize: "0.75rem", color: "var(--muted)", display: "block", marginBottom: 4 }}>File</span>
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.txt,.md"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
              style={{ fontSize: "0.85rem", color: "var(--foreground)" }}
            />
          </label>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={handleUpload}
              disabled={!uploadFile || !uploadPatientId || uploading}
              style={{
                padding: "0.5rem 1rem",
                background: "var(--brand)",
                color: "#fff",
                border: "none",
                borderRadius: "var(--radius)",
                fontSize: "0.85rem",
                cursor: "pointer",
              }}
            >
              {uploading ? "Uploading…" : "Upload"}
            </button>
            <button
              onClick={() => setShowUpload(false)}
              style={{
                padding: "0.5rem 1rem",
                background: "transparent",
                color: "var(--muted)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius)",
                fontSize: "0.85rem",
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{
          padding: "0.6rem 1rem",
          borderRadius: "var(--radius)",
          background: "rgba(248,113,113,0.1)",
          border: "1px solid rgba(248,113,113,0.2)",
          color: "#f87171",
          fontSize: "0.8rem",
          marginBottom: "1rem",
        }}>
          {error}
        </div>
      )}

      {/* Document list */}
      {loading ? (
        <div style={{ color: "var(--muted)", fontSize: "0.85rem", padding: "2rem 0" }}>Loading documents…</div>
      ) : documents.length === 0 ? (
        <div style={{
          padding: "3rem 2rem",
          textAlign: "center",
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
        }}>
          <div style={{ fontSize: "2rem", marginBottom: "0.75rem" }}>📁</div>
          <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
            No documents found. Upload a document or sync from HMS.
          </div>
        </div>
      ) : (
        <div style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          overflow: "hidden",
        }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                {["Title", "Type", "Status", "Pages", "Created"].map((h) => (
                  <th key={h} style={{
                    padding: "0.65rem 1rem",
                    textAlign: "left",
                    fontWeight: 500,
                    color: "var(--muted)",
                    fontSize: "0.75rem",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr 
                  key={doc.id} 
                  onClick={() => window.location.href = `/documents/${doc.id}`}
                  style={{ 
                    borderBottom: "1px solid var(--border)", 
                    cursor: "pointer" 
                  }}
                  className="hover:bg-white/5"
                >
                  <td style={{ padding: "0.6rem 1rem", color: "var(--foreground)" }}>
                    {doc.title}
                  </td>
                  <td style={{ padding: "0.6rem 1rem", color: "var(--muted)" }}>
                    {doc.document_type.replace("hms_", "").replace(/_/g, " ")}
                  </td>
                  <td style={{ padding: "0.6rem 1rem" }}>
                    <span style={{
                      display: "inline-block",
                      padding: "2px 8px",
                      borderRadius: 12,
                      fontSize: "0.75rem",
                      fontWeight: 500,
                      background: `${statusColor[doc.status] || "var(--muted)"}22`,
                      color: statusColor[doc.status] || "var(--muted)",
                    }}>
                      {doc.status}
                    </span>
                  </td>
                  <td style={{ padding: "0.6rem 1rem", color: "var(--muted)" }}>
                    {doc.page_count ?? "—"}
                  </td>
                  <td style={{ padding: "0.6rem 1rem", color: "var(--muted)" }}>
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
