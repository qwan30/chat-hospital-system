"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const DEV_TOKENS = [
  { label: "Doctor", token: "dev-doctor", role: "doctor" },
  { label: "Records Staff", token: "dev-records", role: "records_staff" },
  { label: "Security", token: "dev-security", role: "security" },
  { label: "Admin", token: "dev-admin", role: "admin" },
];

export default function LoginPage() {
  const { login, apiUrl, setApiUrl, isLoading } = useAuth();
  const router = useRouter();
  const [localApiUrl, setLocalApiUrl] = useState(apiUrl || "http://localhost:8000/api/v1");
  const [token, setToken] = useState("");
  const [error, setError] = useState("");

  async function handleLogin(useToken?: string) {
    setError("");
    const t = useToken || token;
    if (!t.trim()) {
      setError("Please enter a bearer token.");
      return;
    }
    const ok = await login(localApiUrl, t.trim());
    if (ok) {
      router.push("/chat");
    } else {
      setError("Invalid token or API unreachable. Check the API URL and token.");
    }
  }

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "var(--background)",
      padding: "1.5rem",
    }}>
      <div style={{
        width: "100%",
        maxWidth: 440,
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius)",
        padding: "2.5rem 2rem",
      }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{
            width: 48,
            height: 48,
            background: "var(--brand)",
            borderRadius: 12,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: "1rem",
            fontSize: 22,
          }}>
            🏥
          </div>
          <h1 style={{
            fontSize: "1.25rem",
            fontWeight: 600,
            color: "var(--foreground)",
            margin: 0,
          }}>
            Hospital Knowledge Assistant
          </h1>
          <p style={{
            fontSize: "0.85rem",
            color: "var(--muted)",
            marginTop: "0.5rem",
          }}>
            Sign in with your bearer token to continue
          </p>
        </div>

        {/* API URL */}
        <label style={{ display: "block", marginBottom: "1rem" }}>
          <span style={{ fontSize: "0.8rem", color: "var(--muted)", display: "block", marginBottom: 4 }}>
            API Base URL
          </span>
          <input
            id="api-url-input"
            type="url"
            value={localApiUrl}
            onChange={(e) => {
              setLocalApiUrl(e.target.value);
              setApiUrl(e.target.value);
            }}
            style={{
              width: "100%",
              padding: "0.6rem 0.75rem",
              background: "var(--surface-elevated)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              color: "var(--foreground)",
              fontSize: "0.875rem",
            }}
          />
        </label>

        {/* Token */}
        <label style={{ display: "block", marginBottom: "1rem" }}>
          <span style={{ fontSize: "0.8rem", color: "var(--muted)", display: "block", marginBottom: 4 }}>
            Bearer Token
          </span>
          <input
            id="token-input"
            type="text"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="e.g. dev-doctor"
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            style={{
              width: "100%",
              padding: "0.6rem 0.75rem",
              background: "var(--surface-elevated)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              color: "var(--foreground)",
              fontSize: "0.875rem",
            }}
          />
        </label>

        {/* Error */}
        {error && (
          <div style={{
            padding: "0.5rem 0.75rem",
            borderRadius: "var(--radius)",
            background: "rgba(248,113,113,0.12)",
            border: "1px solid rgba(248,113,113,0.25)",
            color: "#f87171",
            fontSize: "0.8rem",
            marginBottom: "1rem",
          }}>
            {error}
          </div>
        )}

        {/* Sign In button */}
        <button
          id="login-button"
          disabled={isLoading}
          onClick={() => handleLogin()}
          style={{
            width: "100%",
            padding: "0.65rem",
            background: "var(--brand)",
            color: "#fff",
            border: "none",
            borderRadius: "var(--radius)",
            fontWeight: 500,
            fontSize: "0.9rem",
            cursor: isLoading ? "wait" : "pointer",
            marginBottom: "1.5rem",
            opacity: isLoading ? 0.7 : 1,
          }}
        >
          {isLoading ? "Signing in…" : "Sign In"}
        </button>

        {/* Dev quick tokens */}
        <div>
          <p style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: "0.5rem" }}>
            Development Quick Access
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {DEV_TOKENS.map((dt) => (
              <button
                key={dt.token}
                id={`dev-token-${dt.role}`}
                onClick={() => handleLogin(dt.token)}
                style={{
                  padding: "0.45rem 0.5rem",
                  background: "var(--surface-elevated)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius)",
                  color: "var(--foreground)",
                  fontSize: "0.8rem",
                  cursor: "pointer",
                  textAlign: "center",
                }}
              >
                {dt.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
