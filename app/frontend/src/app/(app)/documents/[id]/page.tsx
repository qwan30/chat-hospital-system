"use client";

import { useAuth } from "@/lib/auth-context";
import { getDocument, type DocumentItem } from "@/lib/api-client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

export default function DocumentDetailPage({ params }: { params: { id: string } }) {
  const { apiUrl, token } = useAuth();
  const router = useRouter();

  const [document, setDocument] = useState<DocumentItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!apiUrl || !token) return;

    let cancelled = false;
    void Promise.resolve().then(() => {
      if (cancelled) return;
      setLoading(true);
      getDocument({ apiUrl, token }, params.id)
        .then((doc) => {
          if (cancelled) return;
          setDocument(doc);
          setLoading(false);
        })
        .catch((err: unknown) => {
          if (cancelled) return;
          setError(err instanceof Error ? err.message : "Failed to load document details");
          setLoading(false);
        });
    });
    return () => {
      cancelled = true;
    };
  }, [params.id, apiUrl, token]);

  const statusColor: Record<string, string> = {
    indexed: "#34d399",
    uploaded: "#60a5fa",
    processing: "#fbbf24",
    failed: "#f87171",
  };

  return (
    <div style={{ padding: "1.5rem 2rem", maxWidth: 800 }}>
      <button
        onClick={() => router.back()}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          background: "transparent",
          border: "none",
          color: "var(--muted)",
          cursor: "pointer",
          fontSize: "0.85rem",
          marginBottom: "1.5rem",
        }}
      >
        <ArrowLeft size={16} /> Back to Documents
      </button>

      {loading ? (
        <div style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Loading document details…</div>
      ) : error ? (
        <div style={{
          padding: "0.6rem 1rem",
          borderRadius: "var(--radius)",
          background: "rgba(248,113,113,0.1)",
          border: "1px solid rgba(248,113,113,0.2)",
          color: "#f87171",
          fontSize: "0.8rem",
        }}>
          {error}
        </div>
      ) : document ? (
        <div style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius)",
          padding: "2rem",
        }}>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 600, margin: "0 0 0.5rem 0", color: "var(--foreground)" }}>
            {document.title}
          </h1>
          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "2rem", alignItems: "center" }}>
            <span style={{
              display: "inline-block",
              padding: "2px 8px",
              borderRadius: 12,
              fontSize: "0.75rem",
              fontWeight: 500,
              background: `${statusColor[document.status] || "var(--muted)"}22`,
              color: statusColor[document.status] || "var(--muted)",
            }}>
              {document.status}
            </span>
            <span style={{ color: "var(--muted)", fontSize: "0.8rem" }}>
              {document.document_type.replace("hms_", "").replace(/_/g, " ")}
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
            <div>
              <div style={{ color: "var(--muted)", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.25rem" }}>
                Patient ID
              </div>
              <div style={{ color: "var(--foreground)", fontSize: "0.9rem" }}>
                {document.patient_id}
              </div>
            </div>
            <div>
              <div style={{ color: "var(--muted)", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.25rem" }}>
                Created At
              </div>
              <div style={{ color: "var(--foreground)", fontSize: "0.9rem" }}>
                {new Date(document.created_at).toLocaleString()}
              </div>
            </div>
            <div>
              <div style={{ color: "var(--muted)", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.25rem" }}>
                MIME Type
              </div>
              <div style={{ color: "var(--foreground)", fontSize: "0.9rem" }}>
                {document.mime_type}
              </div>
            </div>
            <div>
              <div style={{ color: "var(--muted)", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.25rem" }}>
                Page Count
              </div>
              <div style={{ color: "var(--foreground)", fontSize: "0.9rem" }}>
                {document.page_count ?? "N/A"}
              </div>
            </div>
          </div>

          {document.ocr_error && (
            <div style={{
              padding: "1rem",
              borderRadius: "var(--radius)",
              background: "rgba(248,113,113,0.1)",
              border: "1px solid rgba(248,113,113,0.2)",
              marginBottom: "1.5rem",
            }}>
              <div style={{ color: "#f87171", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.25rem", fontWeight: 600 }}>
                OCR Error
              </div>
              <div style={{ color: "var(--foreground)", fontSize: "0.85rem" }}>
                {document.ocr_error}
              </div>
            </div>
          )}

          <div>
            <div style={{ color: "var(--muted)", fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>
              Storage URI
            </div>
            <div style={{
              background: "var(--surface-elevated)",
              padding: "0.75rem",
              borderRadius: "var(--radius)",
              border: "1px solid var(--border)",
              color: "var(--foreground)",
              fontSize: "0.8rem",
              wordBreak: "break-all",
              fontFamily: "monospace",
            }}>
              {document.storage_uri}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
