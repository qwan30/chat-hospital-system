"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useEffect, type ReactNode } from "react";

interface NavItem {
  label: string;
  href: string;
  icon: string;
  roles?: string[];
}

const NAV_ITEMS: NavItem[] = [
  { label: "Chat", href: "/chat", icon: "💬" },
  { label: "Documents", href: "/documents", icon: "📄" },
  { label: "Metrics", href: "/metrics", icon: "📊", roles: ["admin", "doctor"] },
  { label: "Admin", href: "/admin", icon: "🛡️", roles: ["admin", "security"] },
  { label: "Settings", href: "/admin/settings", icon: "⚙️", roles: ["admin"] },
  { label: "Audit", href: "/admin/audit", icon: "🔒", roles: ["admin", "security"] },
];

export default function AppShellLayout({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading, user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

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
    </div>
  );
}
