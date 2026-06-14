"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { AuthMarketingPane } from "@/components/auth/AuthMarketingPane";
import { LoginCard } from "@/components/auth/LoginCard";

export default function LoginPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && isAuthenticated) router.replace("/dashboard");
  }, [authLoading, isAuthenticated, router]);

  if (isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-app">
        <p className="text-text-muted">Redirecting...</p>
      </div>
    );
  }

  return (
    <div className="grid lg:grid-cols-[592px_1fr] min-h-screen bg-bg-app relative">
      {/* Loading overlay — shown during login API call, LoginCard stays mounted beneath */}
      {authLoading && (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-bg-page/70">
          <p className="text-text-muted text-[15px] animate-pulse">Signing in...</p>
        </div>
      )}

      {/* Left Marketing Pane */}
      <div className="hidden lg:block">
        <AuthMarketingPane />
      </div>

      {/* Right Form Pane */}
      <div className="flex flex-col items-center justify-center relative bg-white px-8">
        {/* Environment Pill — top right */}
        <div className="absolute top-8 right-8 z-20 flex items-center gap-1.5 px-3 py-2 rounded-xl bg-success-50 border border-success-100 shadow-sm">
          <span className="w-4 h-4 rounded-sm bg-success-600 flex items-center justify-center text-white text-[10px]">DB</span>
          <span className="text-[12px] text-success-700">Synthetic Data</span>
        </div>

        <div className="w-full max-w-[576px]">
          <LoginCard />
        </div>
      </div>
    </div>
  );
}
