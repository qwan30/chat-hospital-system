"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Topbar } from "@/components/app-shell/Topbar";
import { Sidebar } from "@/components/app-shell/Sidebar";
import { Footer } from "@/components/app-shell/Footer";
import { CommandPalette } from "@/components/app-shell/CommandPalette";
import { SAFETY_FOOTER } from "@/lib/constants";

export default function AppShellLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [paletteOpen, setPaletteOpen] = useState(false);

  useEffect(() => {
    // E2E test bypass: if e2e_auth_token is present, skip redirect (auto-login handles it)
    const isE2E = typeof window !== "undefined" && localStorage.getItem("e2e_auth_token");
    if (!isLoading && !isAuthenticated && !isE2E) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setPaletteOpen((prev) => !prev);
      }
      if (e.key === "Escape") setPaletteOpen(false);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-app text-text-muted">
        Loading...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-app flex">
      <Sidebar />
      <div className="flex-1 flex flex-col" style={{ marginLeft: "244px" }}>
        <Topbar onOpenCommandPalette={() => setPaletteOpen(true)} />
        <main className="flex-1 overflow-auto" style={{ paddingTop: "84px" }}>
          {children}
        </main>
        <Footer />
      </div>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </div>
  );
}
