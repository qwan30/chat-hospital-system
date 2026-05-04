"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/lib/auth-context";

interface LLMSettings {
  chat_provider: string;
  chat_model: string;
  openai_chat_model: string;
  openai_base_url: string;
  ollama_base_url: string;
  system_prompt: string;
  streaming_enabled: boolean;
  available_providers: string[];
}

interface EmbeddingSettings {
  embedding_provider: string;
  embedding_model: string;
  embedding_dimensions: number;
  openai_embedding_model: string;
}

interface RAGSettings {
  retrieval_top_k: number;
  evidence_threshold: number;
  chunk_size: number;
  chunk_overlap: number;
}

interface AllSettings {
  llm: LLMSettings;
  embedding: EmbeddingSettings;
  rag: RAGSettings;
}

const sectionStyle: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius)",
  padding: "1.5rem",
  marginBottom: "1.5rem",
};

const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "0.8rem",
  color: "var(--muted)",
  marginBottom: 4,
  fontWeight: 500,
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.5rem 0.75rem",
  fontSize: "0.85rem",
  background: "var(--surface-elevated)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius)",
  color: "var(--foreground)",
  outline: "none",
};

const selectStyle: React.CSSProperties = {
  ...inputStyle,
  appearance: "none" as const,
  cursor: "pointer",
};

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: "1rem",
};

const buttonStyle: React.CSSProperties = {
  padding: "0.6rem 1.5rem",
  fontSize: "0.85rem",
  fontWeight: 600,
  borderRadius: "var(--radius)",
  border: "none",
  cursor: "pointer",
  transition: "all 0.15s ease",
};

export default function AdminSettingsPage() {
  const { token } = useAuth();
  const [settings, setSettings] = useState<AllSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Draft state for editing
  const [draft, setDraft] = useState<Record<string, unknown>>({});

  const fetchSettings = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/settings", {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data: AllSettings = await res.json();
      setSettings(data);
      setDraft({
        chat_provider: data.llm.chat_provider,
        chat_model: data.llm.chat_model,
        openai_chat_model: data.llm.openai_chat_model,
        openai_base_url: data.llm.openai_base_url,
        ollama_base_url: data.llm.ollama_base_url,
        system_prompt: data.llm.system_prompt,
        streaming_enabled: data.llm.streaming_enabled,
        embedding_provider: data.embedding.embedding_provider,
        embedding_model: data.embedding.embedding_model,
        embedding_dimensions: data.embedding.embedding_dimensions,
        openai_embedding_model: data.embedding.openai_embedding_model,
        retrieval_top_k: data.rag.retrieval_top_k,
        evidence_threshold: data.rag.evidence_threshold,
        chunk_size: data.rag.chunk_size,
        chunk_overlap: data.rag.chunk_overlap,
      });
    } catch (err) {
      setMessage({ type: "error", text: `Failed to load settings: ${err}` });
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    let cancelled = false;
    void Promise.resolve().then(() => {
      if (!cancelled) {
        void fetchSettings();
      }
    });
    return () => {
      cancelled = true;
    };
  }, [fetchSettings]);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const res = await fetch("/api/v1/settings", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(draft),
      });
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data: AllSettings = await res.json();
      setSettings(data);
      setMessage({ type: "success", text: "Settings saved successfully." });
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      setMessage({ type: "error", text: `Save failed: ${err}` });
    } finally {
      setSaving(false);
    }
  };

  const updateDraft = (key: string, value: unknown) => {
    setDraft((prev) => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return (
      <div style={{ padding: "2rem", color: "var(--muted)" }}>
        Loading settings…
      </div>
    );
  }

  return (
    <div style={{ padding: "2rem", maxWidth: 900, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--foreground)", margin: 0 }}>
            ⚙️ System Settings
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: 4 }}>
            Configure LLM providers, embedding models, and RAG parameters.
          </p>
        </div>
        <button
          id="save-settings-button"
          onClick={handleSave}
          disabled={saving}
          style={{
            ...buttonStyle,
            background: saving ? "var(--surface-elevated)" : "var(--brand)",
            color: saving ? "var(--muted)" : "#fff",
          }}
        >
          {saving ? "Saving…" : "Save Changes"}
        </button>
      </div>

      {/* Status message */}
      {message && (
        <div
          style={{
            padding: "0.75rem 1rem",
            marginBottom: "1.5rem",
            borderRadius: "var(--radius)",
            fontSize: "0.85rem",
            background: message.type === "success"
              ? "rgba(39, 166, 68, 0.12)"
              : "rgba(239, 68, 68, 0.12)",
            color: message.type === "success" ? "var(--success)" : "#ef4444",
            border: `1px solid ${message.type === "success" ? "rgba(39,166,68,0.3)" : "rgba(239,68,68,0.3)"}`,
          }}
        >
          {message.text}
        </div>
      )}

      {/* LLM Configuration */}
      <section style={sectionStyle}>
        <h2 style={{ fontSize: "1.05rem", fontWeight: 600, color: "var(--foreground)", margin: "0 0 1rem 0" }}>
          🤖 LLM Configuration
        </h2>
        <div style={gridStyle}>
          <div>
            <label htmlFor="chat-provider" style={labelStyle}>Chat Provider</label>
            <select
              id="chat-provider"
              style={selectStyle}
              value={String(draft.chat_provider || "")}
              onChange={(e) => updateDraft("chat_provider", e.target.value)}
            >
              {(settings?.llm.available_providers || []).map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="chat-model" style={labelStyle}>Chat Model</label>
            <input
              id="chat-model"
              style={inputStyle}
              value={String(draft.chat_model || "")}
              onChange={(e) => updateDraft("chat_model", e.target.value)}
              placeholder="e.g. qwen2.5:7b"
            />
          </div>
          <div>
            <label htmlFor="openai-model" style={labelStyle}>OpenAI Model</label>
            <input
              id="openai-model"
              style={inputStyle}
              value={String(draft.openai_chat_model || "")}
              onChange={(e) => updateDraft("openai_chat_model", e.target.value)}
              placeholder="e.g. gpt-4o-mini"
            />
          </div>
          <div>
            <label htmlFor="openai-base-url" style={labelStyle}>OpenAI Base URL</label>
            <input
              id="openai-base-url"
              style={inputStyle}
              value={String(draft.openai_base_url || "")}
              onChange={(e) => updateDraft("openai_base_url", e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="ollama-base-url" style={labelStyle}>Ollama Base URL</label>
            <input
              id="ollama-base-url"
              style={inputStyle}
              value={String(draft.ollama_base_url || "")}
              onChange={(e) => updateDraft("ollama_base_url", e.target.value)}
            />
          </div>
          <div>
            <label style={labelStyle}>
              <input
                id="streaming-toggle"
                type="checkbox"
                checked={Boolean(draft.streaming_enabled)}
                onChange={(e) => updateDraft("streaming_enabled", e.target.checked)}
                style={{ marginRight: 8 }}
              />
              Enable Streaming
            </label>
          </div>
        </div>
        <div style={{ marginTop: "1rem" }}>
          <label htmlFor="system-prompt" style={labelStyle}>System Prompt</label>
          <textarea
            id="system-prompt"
            style={{
              ...inputStyle,
              minHeight: 100,
              resize: "vertical",
              fontFamily: "monospace",
              fontSize: "0.8rem",
            }}
            value={String(draft.system_prompt || "")}
            onChange={(e) => updateDraft("system_prompt", e.target.value)}
          />
        </div>
      </section>

      {/* Embedding Configuration */}
      <section style={sectionStyle}>
        <h2 style={{ fontSize: "1.05rem", fontWeight: 600, color: "var(--foreground)", margin: "0 0 1rem 0" }}>
          📐 Embedding Configuration
        </h2>
        <div style={gridStyle}>
          <div>
            <label htmlFor="embedding-provider" style={labelStyle}>Embedding Provider</label>
            <select
              id="embedding-provider"
              style={selectStyle}
              value={String(draft.embedding_provider || "")}
              onChange={(e) => updateDraft("embedding_provider", e.target.value)}
            >
              <option value="deterministic">Deterministic (Local)</option>
              <option value="ollama">Ollama</option>
              <option value="openai">OpenAI</option>
            </select>
          </div>
          <div>
            <label htmlFor="embedding-model" style={labelStyle}>Embedding Model</label>
            <input
              id="embedding-model"
              style={inputStyle}
              value={String(draft.embedding_model || "")}
              onChange={(e) => updateDraft("embedding_model", e.target.value)}
              placeholder="e.g. bge-m3"
            />
          </div>
          <div>
            <label htmlFor="embedding-dimensions" style={labelStyle}>Dimensions</label>
            <input
              id="embedding-dimensions"
              type="number"
              style={inputStyle}
              value={Number(draft.embedding_dimensions || 1024)}
              onChange={(e) => updateDraft("embedding_dimensions", parseInt(e.target.value, 10))}
              min={64}
              max={4096}
            />
          </div>
          <div>
            <label htmlFor="openai-embedding-model" style={labelStyle}>OpenAI Embedding Model</label>
            <input
              id="openai-embedding-model"
              style={inputStyle}
              value={String(draft.openai_embedding_model || "")}
              onChange={(e) => updateDraft("openai_embedding_model", e.target.value)}
              placeholder="e.g. text-embedding-3-small"
            />
          </div>
        </div>
      </section>

      {/* RAG Parameters */}
      <section style={sectionStyle}>
        <h2 style={{ fontSize: "1.05rem", fontWeight: 600, color: "var(--foreground)", margin: "0 0 1rem 0" }}>
          🔍 RAG Parameters
        </h2>
        <div style={gridStyle}>
          <div>
            <label htmlFor="retrieval-top-k" style={labelStyle}>
              Retrieval Top-K
              <span style={{ fontWeight: 400, color: "var(--muted)", marginLeft: 4 }}>(1–50)</span>
            </label>
            <input
              id="retrieval-top-k"
              type="number"
              style={inputStyle}
              value={Number(draft.retrieval_top_k || 5)}
              onChange={(e) => updateDraft("retrieval_top_k", parseInt(e.target.value, 10))}
              min={1}
              max={50}
            />
          </div>
          <div>
            <label htmlFor="evidence-threshold" style={labelStyle}>
              Evidence Threshold
              <span style={{ fontWeight: 400, color: "var(--muted)", marginLeft: 4 }}>(0.0–1.0)</span>
            </label>
            <input
              id="evidence-threshold"
              type="number"
              step="0.05"
              style={inputStyle}
              value={Number(draft.evidence_threshold ?? 0.2)}
              onChange={(e) => updateDraft("evidence_threshold", parseFloat(e.target.value))}
              min={0}
              max={1}
            />
          </div>
          <div>
            <label htmlFor="chunk-size" style={labelStyle}>
              Chunk Size
              <span style={{ fontWeight: 400, color: "var(--muted)", marginLeft: 4 }}>(64–4096)</span>
            </label>
            <input
              id="chunk-size"
              type="number"
              style={inputStyle}
              value={Number(draft.chunk_size || 512)}
              onChange={(e) => updateDraft("chunk_size", parseInt(e.target.value, 10))}
              min={64}
              max={4096}
            />
          </div>
          <div>
            <label htmlFor="chunk-overlap" style={labelStyle}>
              Chunk Overlap
              <span style={{ fontWeight: 400, color: "var(--muted)", marginLeft: 4 }}>(0–512)</span>
            </label>
            <input
              id="chunk-overlap"
              type="number"
              style={inputStyle}
              value={Number(draft.chunk_overlap || 64)}
              onChange={(e) => updateDraft("chunk_overlap", parseInt(e.target.value, 10))}
              min={0}
              max={512}
            />
          </div>
        </div>
      </section>

      {/* Info bar */}
      <div style={{
        padding: "0.75rem 1rem",
        borderRadius: "var(--radius)",
        background: "rgba(94, 106, 210, 0.08)",
        border: "1px solid rgba(94, 106, 210, 0.2)",
        fontSize: "0.8rem",
        color: "var(--muted)",
        lineHeight: 1.5,
      }}>
        💡 Changes take effect immediately for new chat requests. Active streaming sessions
        will complete with previous settings. Environment variable defaults are restored on
        server restart.
      </div>
    </div>
  );
}
