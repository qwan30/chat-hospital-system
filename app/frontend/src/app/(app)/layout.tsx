"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useEffect, useState, useMemo, type ReactNode } from "react";
import { globalSearch, type GlobalSearchResult } from "@/lib/api-client";

interface NavItem {
  label: string;
  href: string;
  icon: string;
  roles?: string[];
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: "🏠" },
  { label: "Patients", href: "/patients", icon: "👥" },
  { label: "Chat", href: "/chat", icon: "💬" },
  { label: "Documents", href: "/documents", icon: "📄" },
  { label: "Metrics", href: "/metrics", icon: "📊", roles: ["admin", "doctor"] },
  { label: "Admin", href: "/admin", icon: "🛡️", roles: ["admin", "security"] },
  { label: "Settings", href: "/admin/settings", icon: "⚙️", roles: ["admin"] },
  { label: "Audit", href: "/admin/audit", icon: "🔒", roles: ["admin", "security"] },
];

export default function AppShellLayout({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading, user, logout, apiUrl, token } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const opts = useMemo(() => ({ apiUrl: apiUrl || "", token: token || "" }), [apiUrl, token]);

  // Command Palette State
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState<GlobalSearchResult | null>(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  // Command Palette key handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setPaletteOpen((prev) => !prev);
      }
      if (e.key === "Escape") {
        setPaletteOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Debounced API call for global search
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (!paletteOpen) {
      setSearchQuery("");
      setResults(null);
      return;
    }
    if (!searchQuery.trim()) {
      setResults(null);
      return;
    }
    const delayDebounceFn = setTimeout(() => {
      setSearching(true);
      globalSearch(opts, searchQuery)
        .then((data) => {
          setResults(data);
          setSearching(false);
        })
        .catch(() => {
          setSearching(false);
        });
    }, 250);
    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery, paletteOpen, opts]);
  /* eslint-enable react-hooks/set-state-in-effect */

  if (isLoading || !isAuthenticated) {
    return (
      <div style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--background)",
        color: "var(--muted)",
      }}>
        Loading…
      </div>
    );
  }

  const visibleNav = NAV_ITEMS.filter((item) => {
    if (!item.roles) return true;
    return user && item.roles.includes(user.role);
  });

  return (
    <div style={{
      display: "flex",
      minHeight: "100vh",
      background: "var(--background)",
    }}>
      {/* Sidebar */}
      <aside style={{
        width: 220,
        background: "var(--surface)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        flexShrink: 0,
      }}>
        {/* Logo */}
        <div style={{
          padding: "1.25rem 1rem",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}>
          <div style={{
            width: 32,
            height: 32,
            background: "var(--brand)",
            borderRadius: 8,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 16,
          }}>
            🏥
          </div>
          <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--foreground)" }}>
            Hospital AI
          </span>
        </div>

        {/* Nav items */}
        <nav style={{ flex: 1, padding: "0.75rem 0.5rem" }}>
          {visibleNav.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "0.55rem 0.75rem",
                  borderRadius: "var(--radius)",
                  fontSize: "0.85rem",
                  fontWeight: active ? 500 : 400,
                  color: active ? "var(--foreground)" : "var(--muted)",
                  background: active ? "var(--surface-elevated)" : "transparent",
                  textDecoration: "none",
                  marginBottom: 2,
                  transition: "background 0.15s",
                }}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Global Search Shortcut Tip */}
        <div style={{
          padding: "0.5rem 1rem",
          fontSize: "0.7rem",
          color: "var(--muted)",
          borderTop: "1px solid var(--border)",
          textAlign: "center"
        }}>
          Press <kbd style={{ background: "var(--surface-elevated)", border: "1px solid var(--border)", borderRadius: 3, padding: "1px 4px", fontFamily: "monospace" }}>Ctrl+K</kbd> to search
        </div>

        {/* User info */}
        <div style={{
          padding: "0.75rem 1rem",
          borderTop: "1px solid var(--border)",
        }}>
          <div style={{ fontSize: "0.8rem", color: "var(--foreground)", fontWeight: 500 }}>
            {user?.full_name || "User"}
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--muted)", marginTop: 2 }}>
            {user?.role || "—"} · {user?.department || "—"}
          </div>
          <button
            id="logout-button"
            onClick={logout}
            style={{
              marginTop: 8,
              padding: "0.35rem 0.6rem",
              fontSize: "0.75rem",
              background: "transparent",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              color: "var(--muted)",
              cursor: "pointer",
              width: "100%",
            }}
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, overflow: "auto" }}>
        {children}
      </main>

      {/* Global Command Palette Overlay */}
      {paletteOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(4px)",
            zIndex: 1000,
            display: "flex",
            justifyContent: "center",
            paddingTop: "10vh",
          }}
          onClick={() => setPaletteOpen(false)}
        >
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              width: 540,
              maxWidth: "90%",
              height: "fit-content",
              padding: "1rem",
              display: "flex",
              flexDirection: "column",
              gap: 12,
              boxShadow: "0 20px 25px -5px rgba(0,0,0,0.5)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                autoFocus
                placeholder="Search patients, files, threads..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  background: "var(--surface-elevated)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius)",
                  padding: "0.6rem 0.75rem",
                  width: "100%",
                  outline: "none",
                  color: "var(--foreground)",
                  fontSize: "0.85rem",
                }}
              />
            </div>

            {/* Results Section */}
            <div style={{ maxHeight: 320, overflowY: "auto", display: "flex", flexDirection: "column", gap: 14 }}>
              {searching ? (
                <div style={{ color: "var(--muted)", fontSize: "0.8rem", textAlign: "center", padding: "1.5rem" }}>
                  Searching codebase index…
                </div>
              ) : results ? (
                <>
                  {/* Patients */}
                  {results.patients && results.patients.length > 0 && (
                    <div>
                      <div style={{ fontSize: "0.7rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
                        Patients ({results.patients.length})
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                        {results.patients.map((p) => (
                          <Link
                            key={p.id}
                            href={`/patients/${p.id}`}
                            onClick={() => setPaletteOpen(false)}
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              padding: "0.5rem 0.75rem",
                              borderRadius: "var(--radius)",
                              background: "rgba(255,255,255,0.02)",
                              fontSize: "0.8rem",
                              textDecoration: "none",
                              color: "white"
                            }}
                            className="hover:bg-white/[0.06]"
                          >
                            <span>{p.full_name}</span>
                            <span style={{ color: "var(--muted)" }}>MRN: {p.mrn}</span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Documents */}
                  {results.documents && results.documents.length > 0 && (
                    <div>
                      <div style={{ fontSize: "0.7rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
                        Documents ({results.documents.length})
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                        {results.documents.map((d) => (
                          <Link
                            key={d.id}
                            href={`/documents`}
                            onClick={() => setPaletteOpen(false)}
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              padding: "0.5rem 0.75rem",
                              borderRadius: "var(--radius)",
                              background: "rgba(255,255,255,0.02)",
                              fontSize: "0.8rem",
                              textDecoration: "none",
                              color: "white"
                            }}
                            className="hover:bg-white/[0.06]"
                          >
                            <span>{d.title}</span>
                            <span style={{ color: "var(--muted)", fontSize: "0.72rem" }}>{d.document_type}</span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Threads */}
                  {results.threads && results.threads.length > 0 && (
                    <div>
                      <div style={{ fontSize: "0.7rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
                        Chat Threads ({results.threads.length})
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                        {results.threads.map((t) => (
                          <Link
                            key={t.id}
                            href={`/chat`}
                            onClick={() => setPaletteOpen(false)}
                            style={{
                              display: "flex",
                              flexDirection: "column",
                              padding: "0.5rem 0.75rem",
                              borderRadius: "var(--radius)",
                              background: "rgba(255,255,255,0.02)",
                              fontSize: "0.8rem",
                              textDecoration: "none",
                              color: "white"
                            }}
                            className="hover:bg-white/[0.06]"
                          >
                            <span>{t.title || "Untitled Chat Session"}</span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}

                  {results.patients.length === 0 && results.documents.length === 0 && results.threads.length === 0 && (
                    <div style={{ color: "var(--muted)", fontSize: "0.8rem", textAlign: "center", padding: "1.5rem" }}>
                      No matching records found in clinical scope.
                    </div>
                  )}
                </>
              ) : searchQuery.trim() ? (
                <div style={{ color: "var(--muted)", fontSize: "0.8rem", textAlign: "center", padding: "1.5rem" }}>
                  Searching codebase index…
                </div>
              ) : (
                <div style={{ color: "var(--muted)", fontSize: "0.8rem", textAlign: "center", padding: "1.5rem" }}>
                  Type keywords to search across patients, documents, or threads.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
